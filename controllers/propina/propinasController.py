from flask import jsonify, session, request
from services.propina_service import PropinaService


class PropinasController:

    @staticmethod
    def propinas_hoy():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        try:
            return jsonify({"success": True, **PropinaService.get_hoy(mesero_id)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def propinas_rango():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        try:
            rango = request.args.get("rango", "semana")
            mes = request.args.get("mes")
            return jsonify({"success": True, **PropinaService.get_rango(mesero_id, rango, mes)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
