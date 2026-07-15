from flask import jsonify, render_template, session, redirect, url_for
from services.mesero_diagnostico_service import MeseroDiagnosticoService


class MeseroDiagnosticoController:

    @staticmethod
    def vista():
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
            return redirect(url_for("routes.login"))
        return render_template("mesero/mesero_diagnostico.html", perfil=session.get("perfil_mesero", {}))

    @staticmethod
    def api_diagnostico():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        try:
            resultado = MeseroDiagnosticoService.diagnostico_datos(mesero_id)
            return jsonify({"success": True, **resultado})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
