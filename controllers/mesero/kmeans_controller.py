from flask import jsonify, render_template, request, session, redirect, url_for
from services.mesero_kmeans_service import MeseroKMeansService
from services.ia_recomendacion_service import IARecomendacionService


class MeseroKMeansController:

    @staticmethod
    def vista():
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
            return redirect(url_for("routes.login"))
        return render_template("mesero/mesero_kmeans.html", perfil=session.get("perfil_mesero", {}))

    @staticmethod
    def api_kmeans():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        try:
            resultado = MeseroKMeansService.segmentar_mesas(mesero_id)
            return jsonify({"success": True, **resultado})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def api_recomendaciones():
        data = request.get_json(silent=True) or {}
        resumen    = data.get("resumen", [])
        evaluacion = data.get("evaluacion", {})
        if not resumen:
            return jsonify({"success": False, "error": "Sin datos de clusters"}), 400
        try:
            import os
            via_claude = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
            recs = IARecomendacionService.generar_recomendaciones_kmeans(resumen, evaluacion)
            return jsonify({"success": True, "recomendaciones": recs, "via_claude": via_claude})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
