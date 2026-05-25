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
