"""
Controller de Cocina - Sistema Restaurante Callejón 9
Gestiona pedidos pendientes, en proceso y listos
"""

from flask import jsonify, request, session
from config.db import db
from bson.objectid import ObjectId
from datetime import datetime, timedelta


class CocinaController:
    """
    Controlador para gestión de pedidos en cocina
    """

    @staticmethod
    def obtener_pedidos_pendientes():
        """
        GET /api/cocina/pedidos/pendientes
        Obtiene todos los pedidos pendientes de preparación
        """
        try:
            # Buscar comandas con items enviados a cocina
            cursor = db.comandas.find({
                "$or": [
                    {"estado": "enviada"},  # Recién enviada
                    {"items.estado_cocina": "pendiente"}  # Items pendientes
                ]
            }).sort("fecha_apertura", 1)  # Los más antiguos primero

            pedidos = []
            
            for comanda in cursor:
                # Filtrar solo items pendientes
                items_pendientes = [
                    item for item in comanda.get("items", [])
                    if item.get("estado_cocina", "pendiente") == "pendiente"
                ]
                
                if items_pendientes:
                    pedidos.append({
                        "id": str(comanda["_id"]),
                        "folio": comanda.get("folio"),
                        "mesa": comanda.get("mesa_numero"),
                        "mesero": comanda.get("mesero_nombre", "Mesero"),
                        "items": items_pendientes,
                        "num_items": len(items_pendientes),
                        "fecha_pedido": comanda.get("fecha_apertura"),
                        "tiempo_espera": _calcular_tiempo_espera(comanda.get("fecha_apertura"))
                    })

            return jsonify({
                "success": True,
                "pedidos": pedidos,
                "total": len(pedidos)
            }), 200

        except Exception as e:
            print(f"❌ Error en obtener_pedidos_pendientes: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def obtener_pedidos_en_proceso():
        """
        GET /api/cocina/pedidos/en-proceso
        Obtiene pedidos que están siendo preparados
        """
        try:
            cursor = db.comandas.find({
                "items.estado_cocina": "en_preparacion"
            }).sort("fecha_apertura", 1)

            pedidos = []
            
            for comanda in cursor:
                items_en_proceso = [
                    item for item in comanda.get("items", [])
                    if item.get("estado_cocina") == "en_preparacion"
                ]
                
                if items_en_proceso:
                    pedidos.append({
                        "id": str(comanda["_id"]),
                        "folio": comanda.get("folio"),
                        "mesa": comanda.get("mesa_numero"),
                        "items": items_en_proceso,
                        "fecha_inicio": items_en_proceso[0].get("fecha_inicio_preparacion"),
                        "tiempo_preparacion": _calcular_tiempo_espera(
                            items_en_proceso[0].get("fecha_inicio_preparacion")
                        )
                    })

            return jsonify({
                "success": True,
                "pedidos": pedidos,
                "total": len(pedidos)
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def obtener_pedidos_listos():
        """
        GET /api/cocina/pedidos/listos
        Obtiene pedidos listos para servir
        """
        try:
            cursor = db.comandas.find({
                "items.estado_cocina": "listo"
            }).sort("fecha_apertura", -1)

            pedidos = []
            
            for comanda in cursor:
                items_listos = [
                    item for item in comanda.get("items", [])
                    if item.get("estado_cocina") == "listo"
                ]
                
                if items_listos:
                    pedidos.append({
                        "id": str(comanda["_id"]),
                        "folio": comanda.get("folio"),
                        "mesa": comanda.get("mesa_numero"),
                        "items": items_listos,
                        "fecha_listo": items_listos[0].get("fecha_listo")
                    })

            return jsonify({
                "success": True,
                "pedidos": pedidos,
                "total": len(pedidos)
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def iniciar_preparacion():
        """
        POST /api/cocina/pedido/iniciar
        Marca items como en preparación
        """
        try:
            data = request.json
            comanda_id = data.get("comanda_id")
            item_ids = data.get("item_ids", [])  # IDs de productos a preparar

            if not comanda_id or not item_ids:
                return jsonify({
                    "success": False,
                    "error": "Datos incompletos"
                }), 400

            # Actualizar estado de items específicos
            result = db.comandas.update_one(
                {"_id": ObjectId(comanda_id)},
                {
                    "$set": {
                        "items.$[item].estado_cocina": "en_preparacion",
                        "items.$[item].fecha_inicio_preparacion": datetime.utcnow(),
                        "items.$[item].cocinero_id": ObjectId(session.get("usuario_id"))
                    }
                },
                array_filters=[
                    {"item.producto_id": {"$in": item_ids}}
                ]
            )

            if result.modified_count > 0:
                # Emitir evento Socket.IO
                _emitir_evento_cocina(comanda_id, "preparacion_iniciada", item_ids)
                
                return jsonify({
                    "success": True,
                    "message": "Preparación iniciada"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "No se pudo actualizar"
                }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def marcar_como_listo():
        """
        POST /api/cocina/pedido/listo
        Marca items como listos para servir
        """
        try:
            data = request.json
            comanda_id = data.get("comanda_id")
            item_ids = data.get("item_ids", [])

            if not comanda_id or not item_ids:
                return jsonify({
                    "success": False,
                    "error": "Datos incompletos"
                }), 400

            result = db.comandas.update_one(
                {"_id": ObjectId(comanda_id)},
                {
                    "$set": {
                        "items.$[item].estado_cocina": "listo",
                        "items.$[item].fecha_listo": datetime.utcnow()
                    }
                },
                array_filters=[
                    {"item.producto_id": {"$in": item_ids}}
                ]
            )

            if result.modified_count > 0:
                # Obtener info del mesero para notificar
                comanda = db.comandas.find_one({"_id": ObjectId(comanda_id)})
                mesero_id = str(comanda.get("mesero_id"))
                
                # Emitir notificación al mesero
                _notificar_mesero_pedido_listo(
                    mesero_id, 
                    comanda_id, 
                    comanda.get("mesa_numero"),
                    item_ids
                )
                
                return jsonify({
                    "success": True,
                    "message": "Pedido marcado como listo"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "No se pudo actualizar"
                }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def marcar_como_entregado():
        """
        POST /api/cocina/pedido/entregado
        Marca items como entregados (desde vista de mesero)
        """
        try:
            data = request.json
            comanda_id = data.get("comanda_id")
            item_ids = data.get("item_ids", [])

            result = db.comandas.update_one(
                {"_id": ObjectId(comanda_id)},
                {
                    "$set": {
                        "items.$[item].estado_cocina": "entregado",
                        "items.$[item].fecha_entregado": datetime.utcnow()
                    }
                },
                array_filters=[
                    {"item.producto_id": {"$in": item_ids}}
                ]
            )

            return jsonify({
                "success": True,
                "message": "Pedido entregado"
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def obtener_estadisticas_cocina():
        """
        GET /api/cocina/estadisticas
        Obtiene estadísticas de rendimiento de cocina
        """
        try:
            hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            hoy_fin = hoy_inicio + timedelta(days=1)

            # Contar pedidos procesados hoy
            pipeline = [
                {
                    "$match": {
                        "fecha_apertura": {"$gte": hoy_inicio, "$lt": hoy_fin}
                    }
                },
                {
                    "$unwind": "$items"
                },
                {
                    "$group": {
                        "_id": "$items.estado_cocina",
                        "count": {"$sum": 1}
                    }
                }
            ]

            resultados = list(db.comandas.aggregate(pipeline))
            
            stats = {
                "pendientes": 0,
                "en_preparacion": 0,
                "listos": 0,
                "entregados": 0,
                "total_procesados": 0
            }

            for r in resultados:
                estado = r.get("_id", "pendiente")
                count = r.get("count", 0)
                
                if estado in stats:
                    stats[estado] = count
                stats["total_procesados"] += count

            return jsonify({
                "success": True,
                "estadisticas": stats
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def _calcular_tiempo_espera(fecha_inicio):
    """Calcula tiempo transcurrido en minutos"""
    if not fecha_inicio:
        return 0
    
    delta = datetime.utcnow() - fecha_inicio
    return int(delta.total_seconds() / 60)


def _emitir_evento_cocina(comanda_id, evento, data):
    """Emite eventos Socket.IO a cocina"""
    try:
        from extensions import socketio
        
        socketio.emit(
            evento,
            {
                "comanda_id": comanda_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            },
            room="cocina",
            namespace="/"
        )
    except Exception as e:
        print(f"⚠️ Error al emitir evento Socket.IO: {e}")


def _notificar_mesero_pedido_listo(mesero_id, comanda_id, mesa_numero, item_ids):
    """Notifica al mesero que su pedido está listo"""
    try:
        from extensions import socketio
        from cqrs.commands.handlers.notificacion_handler import NotificacionSistemaHandler
        
        # Crear notificación en BD
        NotificacionSistemaHandler.notificar_pedido_listo(
            mesero_id=mesero_id,
            comanda_id=comanda_id,
            mesa_numero=mesa_numero
        )
        
        # Emitir evento en tiempo real
        socketio.emit(
            "pedido_listo",
            {
                "comanda_id": comanda_id,
                "mesa": mesa_numero,
                "items": item_ids
            },
            room=f"user_{mesero_id}",
            namespace="/"
        )
        
    except Exception as e:
        print(f"⚠️ Error al notificar mesero: {e}")