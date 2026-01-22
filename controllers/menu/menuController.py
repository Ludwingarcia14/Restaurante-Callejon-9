"""
Controlador de Menú
"""
from flask import render_template, session, redirect, url_for

class MenuController:
    @staticmethod
    def index():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        return render_template("admin/menu/lista.html")
