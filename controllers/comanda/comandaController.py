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

        cursor = db.comandas.find({
            "estado": {"$ne": "pagada"},
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
        data = request.json or {}

        metodo_pago = data.get("metodo_pago", "efectivo")
        tipo_propina = data.get("tipo_propina", "sin")
        custom_porcentaje = data.get("custom_porcentaje")

        comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
        if not comanda:
            return jsonify({"success": False, "error": "Comanda no encontrada"}), 404

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

        # ==========================
        # 💾 GUARDAR COMANDA
        # ==========================
        db.comandas.update_one(
            {"_id": ObjectId(cuenta_id)},
            {"$set": {
                "estado": "pagada",
                "metodo_pago": metodo_pago,
                "propina": propina,
                "porcentaje_propina": porcentaje,
                "total_final": total_final,
                "fecha_cierre": datetime.utcnow()
            }}
        )

        # ==========================
        # 🪑 LIBERAR MESA
        # ==========================
        db.mesas.update_one(
            {"cuenta_activa_id": ObjectId(cuenta_id)},
            {"$set": {
                "estado": "libre",
                "cuenta_activa_id": None,
                "comensales": 0
            }}
        )

        return jsonify({
            "success": True,
            "total": total,
            "propina": propina,
            "porcentaje": porcentaje,
            "total_final": total_final
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

        cursor = db.comandas.find({
            "estado": "pagada",
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

        inicio_dia = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        fin_dia = inicio_dia + timedelta(days=1)

        cursor = db.comandas.find({
            "estado": "pagada",
            "mesero_id": mesero_oid,
            "fecha_cierre": {
                "$gte": inicio_dia,
                "$lt": fin_dia
            }
        })

        venta = 0
        propinas = 0
        ordenes = 0

        for c in cursor:
            venta += float(c.get("total_final", 0))
            propinas += float(c.get("propina", 0))
            ordenes += 1

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