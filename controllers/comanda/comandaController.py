from flask import jsonify, request, session, render_template
from models.comanda_model import Comanda
from config.db import db
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime, time, timedelta

class ComandaController:

    @staticmethod
    def comandas_activas():
        mesero_id = session.get("usuario_id")

        if not mesero_id:
            return jsonify({"success": True, "comandas": [], "total": 0})

        mesero_oid = ObjectId(mesero_id)

        # 🔥 EXCLUIR TANTO "pagada" COMO "cerrada"
        cursor = db.comandas.find({
            "estado": {"$nin": ["pagada", "cerrada"]},  # 🔥 Cambiado de $ne a $nin
            "mesero_id": mesero_oid
        }).sort("fecha_apertura", -1)

        comandas = []

        for c in cursor:
            c["id"] = str(c["_id"])
            c["_id"] = str(c["_id"])
            c["mesero_id"] = str(c["mesero_id"])

            for item in c.get("items", []):
                if "id" in item:
                    item["id"] = str(item["id"])

            c["total"] = float(c.get("total", 0))
            comandas.append(c)

        return jsonify({
            "success": True,
            "comandas": comandas,
            "total": len(comandas)
        })


    @staticmethod
    def abrir_cuenta():
        data = request.json
        numero_mesa = data.get("numero_mesa")
        num_comensales = data.get("num_comensales")
        mesero_id = session.get("usuario_id")
        mesero_nombre = session.get("usuario_nombre", "Mesero")

        if not mesero_id:
            return jsonify({
                "success": False,
                "error": "Sesión no válida"
            }), 401

        if not numero_mesa or not num_comensales:
            return jsonify({
                "success": False,
                "error": "Datos incompletos"
            }), 400

        cuenta_id = Comanda.crear_comanda(
            numero_mesa,
            num_comensales,
            mesero_id,
            mesero_nombre
        )

        db.mesas.update_one(
            {"numero": int(numero_mesa)},
            {"$set": {
                "estado": "ocupada",
                "cuenta_activa_id": ObjectId(cuenta_id),
                "comensales": int(num_comensales)
            }}
        )

        return jsonify({
            "success": True,
            "cuenta_id": cuenta_id,
            "message": "Cuenta abierta correctamente"
        })

    @staticmethod
    def guardar_items(cuenta_id):
        """
        VERSIÓN MEJORADA: Ahora envía notificación a cocina cuando se agregan items
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
        
        items_nuevos = data.get("items", [])
        if not items_nuevos:
            return jsonify({"success": False, "error": "Pedido vacío"}), 400

        try:
            # 1. Obtener la comanda actual
            comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
            
            if not comanda:
                return jsonify({"success": False, "error": "Comanda no encontrada"}), 404
            
            # 2. Obtener items existentes
            items_existentes = comanda.get("items", [])
            items_para_cocina = []  # Items nuevos que se enviarán a cocina
            
            # 3. FUSIONAR items: si el producto ya existe, SUMAR cantidad; si no, agregarlo
            for item_nuevo in items_nuevos:
                producto_id = item_nuevo.get('id')
                encontrado = False
                
                # Buscar si el producto ya existe en la comanda
                for item_existente in items_existentes:
                    # Comparar por ID (puede estar como 'id' o 'producto_id')
                    item_id = item_existente.get('producto_id') or item_existente.get('id')
                    
                    if str(item_id) == str(producto_id):
                        # SUMAR la cantidad al item existente
                        item_existente['cantidad'] += item_nuevo['cantidad']
                        encontrado = True
                        
                        # 🔔 Marcar como pendiente de nuevo para cocina
                        item_existente['estado_cocina'] = 'pendiente'
                        items_para_cocina.append(producto_id)
                        break
                
                if not encontrado:
                    # Agregar como nuevo item con estado inicial de cocina
                    nuevo_item = {
                        'producto_id': producto_id,
                        'id': producto_id,  # Por compatibilidad
                        'nombre': item_nuevo['nombre'],
                        'precio': item_nuevo['precio'],
                        'cantidad': item_nuevo['cantidad'],
                        'estado_cocina': 'pendiente',  # 🔥 ESTADO INICIAL
                        'fecha_pedido': datetime.utcnow()
                    }
                    items_existentes.append(nuevo_item)
                    items_para_cocina.append(producto_id)
            
            # 4. Recalcular el total
            total = sum(
                float(item.get('precio', 0)) * int(item.get('cantidad', 0)) 
                for item in items_existentes
            )
            
            # 5. Actualizar la comanda en la base de datos
            db.comandas.update_one(
                {"_id": ObjectId(cuenta_id)},
                {"$set": {
                    "items": items_existentes,
                    "total": total,
                    "estado": "enviada",  # Cambiar estado a enviada
                    "fecha_actualizacion": datetime.utcnow()
                }}
            )
            
            # 🔔 6. NOTIFICAR A COCINA (Socket.IO)
            if items_para_cocina:
                _notificar_cocina_nuevo_pedido(
                    comanda_id=cuenta_id,
                    mesa_numero=comanda.get("mesa_numero"),
                    items=items_nuevos,
                    mesero_nombre=comanda.get("mesero_nombre", "Mesero")
                )
            
            return jsonify({
                "success": True,
                "message": "✅ Pedido enviado a cocina",
                "total": total,
                "items_count": len(items_existentes),
                "items_nuevos": len(items_para_cocina)
            }), 200
            
        except Exception as e:
            print(f"Error en guardar_items: {e}")
            return jsonify({
                "success": False, 
                "error": f"Error al guardar items: {str(e)}"
            }), 500

    @staticmethod
    def vista_agregar_items(cuenta_id):
        perfil_mesero = session.get("perfil_mesero")
        return render_template(
            "mesero/mesero_menu.html",
            perfil=perfil_mesero,
            cuenta_id=cuenta_id
        )

    @staticmethod
    def cerrar_cuenta(cuenta_id):
        """
        🔥 CIERRE DE CUENTA PARA EFECTIVO Y TRANSFERENCIA
        (Mercado Pago se maneja por separado en MercadoPagoController)
        """
        data = request.json or {}

        metodo_pago = data.get("metodo_pago", "efectivo")
        tipo_propina = data.get("tipo_propina", "sin")
        custom_porcentaje = data.get("custom_porcentaje")

        try:
            comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
            if not comanda:
                return jsonify({"success": False, "error": "Comanda no encontrada"}), 404

            # Verificar que no esté ya cerrada
            if comanda.get("estado") in ["cerrada", "pagada"]:
                return jsonify({
                    "success": False,
                    "error": "Esta cuenta ya fue cerrada"
                }), 400

            total = float(comanda.get("total", 0))

            # ==========================
            # 🧮 CALCULAR PROPINA
            # ==========================
            porcentaje = 0

            if tipo_propina == "custom":
                porcentaje = float(custom_porcentaje or 0)
            elif tipo_propina.isdigit():
                porcentaje = float(tipo_propina)

            propina = round(total * (porcentaje / 100), 2)
            total_final = round(total + propina, 2)

            # 🔥 USAR HORA LOCAL (NO UTC)
            fecha_actual = datetime.now()
            
            print(f"\n{'='*60}")
            print(f"💵 CERRANDO CUENTA - {metodo_pago.upper()}")
            print(f"{'='*60}")
            print(f"Cuenta ID: {cuenta_id}")
            print(f"Total: ${total_final:.2f}")
            print(f"Propina: ${propina:.2f}")
            print(f"Fecha cierre: {fecha_actual}")
            print(f"{'='*60}\n")

            # ==========================
            # 💾 GUARDAR COMANDA
            # ==========================
            db.comandas.update_one(
                {"_id": ObjectId(cuenta_id)},
                {
                    "$set": {
                        "estado": "pagada",
                        "metodo_pago": metodo_pago,
                        "propina": propina,
                        "porcentaje_propina": porcentaje,
                        "total_final": total_final,
                        "fecha_cierre": fecha_actual
                    }
                }
            )

            # ==========================
            # 🪑 LIBERAR MESA
            # ==========================
            mesa_numero = comanda.get("mesa_numero")
            db.mesas.update_one(
                {"numero": mesa_numero},
                {
                    "$set": {
                        "estado": "disponible",
                        "cuenta_activa_id": None,
                        "num_comensales": 0,
                        "ultima_actualizacion": fecha_actual
                    }
                }
            )

            # ==========================
            # 💰 REGISTRAR PROPINA
            # ==========================
            if propina > 0 and comanda.get("mesero_id"):
                db.propinas.insert_one({
                    "mesero_id": comanda.get("mesero_id"),
                    "comanda_id": ObjectId(cuenta_id),
                    "mesa_numero": mesa_numero,
                    "monto": propina,
                    "porcentaje": porcentaje,
                    "fecha": fecha_actual,
                    "metodo_pago": metodo_pago
                })

            return jsonify({
                "success": True,
                "total": total,
                "propina": propina,
                "porcentaje_propina": porcentaje,
                "total_final": total_final,
                "message": "Cuenta cerrada correctamente"
            })

        except InvalidId:
            return jsonify({"success": False, "error": "ID de cuenta inválido"}), 400
        except Exception as e:
            print(f"❌ Error al cerrar cuenta: {e}")
            return jsonify({
                "success": False,
                "error": f"Error al cerrar cuenta: {str(e)}"
            }), 500

    @staticmethod
    def verificar_estado_pago(cuenta_id):
        """
        🔥 ENDPOINT PARA VERIFICAR SI UN PAGO FUE PROCESADO
        Se usa para polling desde el frontend
        """
        try:
            cuenta_oid = ObjectId(cuenta_id)
        except:
            return jsonify({
                "success": False,
                "error": "ID inválido"
            }), 400
        
        comanda = db.comandas.find_one({"_id": cuenta_oid})
        
        if not comanda:
            return jsonify({
                "success": False,
                "error": "Comanda no encontrada"
            }), 404
        
        # Si está cerrada, el pago fue aprobado
        if comanda.get("estado") in ["cerrada", "pagada"]:
            return jsonify({
                "success": True,
                "status": "approved",
                "total": float(comanda.get("total_final", comanda.get("total", 0))),
                "propina": float(comanda.get("propina", 0)),
                "metodo_pago": comanda.get("metodo_pago", "efectivo")
            })
        
        # Si no está cerrada, sigue pendiente
        return jsonify({
            "success": True,
            "status": "pending"
        })
        
    @staticmethod
    def comandas_cerradas():
        mesero_id = session.get("usuario_id")

        if not mesero_id:
            return jsonify({"success": True, "comandas": []})

        try:
            mesero_oid = ObjectId(mesero_id)
        except Exception:
            return jsonify({"success": True, "comandas": []})

        # 🔥 Buscar tanto "pagada" como "cerrada"
        cursor = db.comandas.find({
            "estado": {"$in": ["pagada", "cerrada"]},
            "mesero_id": mesero_oid
        }).sort("fecha_cierre", -1)

        comandas = []
        for c in cursor:
            comandas.append({
                "id": str(c["_id"]),
                "folio": c.get("folio"),
                "mesa": c.get("mesa_numero"),
                "total": float(c.get("total", 0)),
                "propina": float(c.get("propina", 0)),
                "total_final": float(c.get("total_final", c.get("total", 0))),
                "metodo_pago": c.get("metodo_pago"),
                "fecha": c.get("fecha_cierre")
            })

        return jsonify({
            "success": True,
            "comandas": comandas
        })
        
    @staticmethod
    def estadisticas_dia_mesero():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False}), 401

        mesero_oid = ObjectId(mesero_id)

        # 🔥 USAR HORA LOCAL (NO UTC)
        inicio_dia = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        fin_dia = inicio_dia + timedelta(days=1)

        print(f"\n{'='*60}")
        print(f"📊 ESTADÍSTICAS DEL DÍA - DEBUG")
        print(f"{'='*60}")
        print(f"Mesero ID: {mesero_id}")
        print(f"Inicio día: {inicio_dia}")
        print(f"Fin día: {fin_dia}")

        # 🔥 BUSCAR COMANDAS CON ESTADO "pagada" O "cerrada"
        cursor = db.comandas.find({
            "estado": {"$in": ["pagada", "cerrada"]},
            "mesero_id": mesero_oid,
            "fecha_cierre": {
                "$gte": inicio_dia,
                "$lt": fin_dia
            }
        })

        venta = 0
        propinas = 0
        ordenes = 0

        comandas_del_dia = list(cursor)
        print(f"\n📅 Comandas del día encontradas: {len(comandas_del_dia)}")

        for c in comandas_del_dia:
            venta += float(c.get("total_final", 0))
            propinas += float(c.get("propina", 0))
            ordenes += 1
            print(f"   ✅ Folio: {c.get('folio')}, Total: ${c.get('total_final', 0):.2f}, Fecha: {c.get('fecha_cierre')}")

        print(f"\n💰 RESULTADOS:")
        print(f"   Venta total: ${venta:.2f}")
        print(f"   Propinas: ${propinas:.2f}")
        print(f"   Órdenes: {ordenes}")
        print(f"{'='*60}\n")

        return jsonify({
            "success": True,
            "estadisticas": {
                "venta_dia": venta,
                "propinas_dia": propinas,
                "num_ordenes": ordenes
            }
        })

# ============================================
# 🔔 FUNCIONES AUXILIARES - NOTIFICACIONES
# ============================================

def _notificar_cocina_nuevo_pedido(comanda_id, mesa_numero, items, mesero_nombre):
    """
    Notifica a cocina mediante Socket.IO cuando hay un nuevo pedido
    """
    try:
        from extensions import socketio
        
        # Emitir evento a la sala de cocina
        socketio.emit(
            'nuevo_pedido',
            {
                'comanda_id': comanda_id,
                'mesa': mesa_numero,
                'items': items,
                'mesero': mesero_nombre,
                'timestamp': datetime.utcnow().isoformat(),
                'num_items': len(items)
            },
            room='cocina',
            namespace='/'
        )
        
        print(f"✅ Notificación enviada a cocina - Mesa {mesa_numero}")
        
        # También crear notificación en BD para todos los usuarios de cocina
        _crear_notificacion_bd_cocina(comanda_id, mesa_numero, items)
        
    except Exception as e:
        print(f"⚠️ Error al notificar a cocina: {e}")


def _crear_notificacion_bd_cocina(comanda_id, mesa_numero, items):
    """
    Crea notificación en base de datos para usuarios de cocina
    """
    try:
        # Buscar todos los usuarios con rol de cocina (rol 3)
        usuarios_cocina = db.usuarios.find({"rol": 3})
        
        for usuario in usuarios_cocina:
            db.notificaciones.insert_one({
                "id_usuario": usuario["_id"],
                "tipo": "nuevo_pedido",
                "titulo": f"🍽️ Nuevo Pedido - Mesa {mesa_numero}",
                "mensaje": f"{len(items)} platillo(s) para preparar",
                "leida": False,
                "fecha": datetime.utcnow(),
                "datos": {
                    "comanda_id": comanda_id,
                    "mesa": mesa_numero,
                    "items": items
                }
            })
            
    except Exception as e:
        print(f"⚠️ Error al crear notificación en BD: {e}")