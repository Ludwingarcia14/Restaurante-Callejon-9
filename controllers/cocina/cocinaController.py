from flask import jsonify, request, session
from services.cocina_service import CocinaService


class CocinaController:

    @staticmethod
    def obtener_pedidos_pendientes():
        try:
            pedidos = CocinaService.get_pedidos_pendientes()
            return jsonify({"success": True, "pedidos": pedidos, "total": len(pedidos)}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_pedidos_movil():
        """Pedidos hechos desde la app/wearable del cliente (no confundir con comandas de mesero)."""
        try:
            pedidos = CocinaService.get_pedidos_movil_pendientes()
            return jsonify({"success": True, "pedidos": pedidos, "total": len(pedidos)}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def actualizar_estado_pedido_movil():
        try:
            data = request.json or {}
            pedido_id = data.get("pedido_id")
            nuevo_estado = data.get("estado")
            if not pedido_id or not nuevo_estado:
                return jsonify({"success": False, "error": "pedido_id y estado son requeridos"}), 400
            ok = CocinaService.actualizar_estado_pedido_movil(pedido_id, nuevo_estado)
            if ok:
                return jsonify({"success": True, "message": f"Pedido actualizado a '{nuevo_estado}'"}), 200
            return jsonify({"success": False, "error": "No se pudo actualizar el pedido"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_pedidos_en_proceso():
        try:
            pedidos = CocinaService.get_pedidos_en_proceso()
            return jsonify({"success": True, "pedidos": pedidos, "total": len(pedidos)}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_pedidos_listos():
        try:
            pedidos = CocinaService.get_pedidos_listos()
            return jsonify({"success": True, "pedidos": pedidos, "total": len(pedidos)}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def iniciar_preparacion():
        try:
            data = request.json or {}
            comanda_id = data.get("comanda_id")
            item_ids = data.get("item_ids", [])
            if not comanda_id or not item_ids:
                return jsonify({"success": False, "error": "Datos incompletos"}), 400
            ok = CocinaService.iniciar_preparacion(comanda_id, item_ids, session.get("usuario_id"))
            if ok:
                return jsonify({"success": True, "message": "Preparación iniciada"}), 200
            return jsonify({"success": False, "error": "No se pudo actualizar"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def marcar_como_listo():
        try:
            data = request.json or {}
            comanda_id = data.get("comanda_id")
            item_ids = data.get("item_ids", [])
            if not comanda_id or not item_ids:
                return jsonify({"success": False, "error": "Datos incompletos"}), 400
            ok = CocinaService.marcar_listo(comanda_id, item_ids)
            if ok:
                return jsonify({"success": True, "message": "Pedido marcado como listo"}), 200
            return jsonify({"success": False, "error": "No se pudo actualizar"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def marcar_como_entregado():
        try:
            data = request.json or {}
            CocinaService.marcar_entregado(data.get("comanda_id"), data.get("item_ids", []))
            return jsonify({"success": True, "message": "Pedido entregado"}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_estadisticas_cocina():
        try:
            return jsonify({"success": True, "estadisticas": CocinaService.get_estadisticas()}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def get_top_platillos():
        try:
            return jsonify({"success": True, "data": CocinaService.get_top_platillos()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def get_kmeans_platillos():
        try:
            resultado = CocinaService.get_kmeans_platillos()
            return jsonify({"success": True, **resultado})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# FUNCIONES AUXILIARES
# ============================================
from datetime import datetime
def _calcular_tiempo_espera(fecha_inicio):
    if not fecha_inicio:
        return 0
    delta = datetime.utcnow() - fecha_inicio
    return int(delta.total_seconds() / 60)


def _emitir_evento_cocina(comanda_id, evento, data):
    try:
        from extensions import socketio
        socketio.emit(
            evento,
            {"comanda_id": comanda_id, "data": data, "timestamp": datetime.utcnow().isoformat()},
            room="cocina",
            namespace="/"
        )
    except Exception as e:
        print(f"Error al emitir evento Socket.IO: {e}")


def _notificar_mesero_pedido_listo(mesero_id, comanda_id, mesa_numero, item_ids):
    try:
        from extensions import socketio
        from controllers.notificaciones.notificacion_controller import NotificacionCommandHandler
        NotificacionCommandHandler.crear_notificacion(
            tipo="PEDIDO_LISTO",
            mensaje=f"Pedido listo en mesa {mesa_numero}",
            id_usuario=str(mesero_id),
            datos_extra={"comanda_id": comanda_id, "mesa_numero": mesa_numero, "item_ids": item_ids}
        )
        socketio.emit(
            "pedido_listo",
            {"comanda_id": comanda_id, "mesa": mesa_numero, "items": item_ids},
            room=f"user_{mesero_id}",
            namespace="/"
        )
    except Exception as e:
        print(f"Error al notificar mesero: {e}")
