from flask import render_template, session, redirect, url_for


class MeseroRandomForestController:

    @staticmethod
    def vista():
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
            return redirect(url_for("routes.login"))
        return render_template("mesero/mesero_arbol.html", perfil=session.get("perfil_mesero", {}))
