from . import routes_bp
from flask import render_template

@routes_bp.route("/cliente/login")
def cliente_login_view():
    return render_template("cliente/login_cliente.html")

@routes_bp.route("/cliente/perfil")
def cliente_perfil_view():
    return render_template("cliente/perfil.html")

@routes_bp.route("/cliente/menu")
def cliente_menu_view():
    return render_template("cliente/menu.html")