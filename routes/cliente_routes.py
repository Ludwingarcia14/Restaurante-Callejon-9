from . import routes_bp
from flask import render_template

@routes_bp.route("/cliente/login")
def cliente_login_view():
    return render_template("cliente/login_cliente.html")

@routes_bp.route("/cliente/registro")
def cliente_registro_view():
    return render_template("cliente/registro.html")

@routes_bp.route("/cliente/perfil")
def cliente_perfil_view():
    return render_template("cliente/perfil.html")

@routes_bp.route("/cliente/menu")
def cliente_menu_view():
    return render_template("cliente/menu.html")

@routes_bp.route("/cliente/carrito")
def cliente_carrito_view():
    return render_template("cliente/carrito.html")

@routes_bp.route("/cliente/pedido")
def cliente_pedido_activo_view():
    return render_template("cliente/pedido_activo.html")

@routes_bp.route("/cliente/pedidos")
def cliente_mis_pedidos_view():
    return render_template("cliente/mis_pedidos.html")