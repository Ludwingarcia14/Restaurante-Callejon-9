from flask import jsonify, render_template, session, redirect, url_for
from services.mesero_kmeans_service import MeseroKMeansService


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
