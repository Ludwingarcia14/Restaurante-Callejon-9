from . import routes_bp
from flask import session, render_template
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.cocina.cocinaController import CocinaController

@routes_bp.route("/dashboard/cocina")
@login_required
@rol_required(['3'])
def dashboard_cocina():
    return DashboardController.cocina()

@routes_bp.route("/cocina/pedidos")
@login_required
@rol_required(['3'])
def cocina_pedidos():
    perfil_cocina = session.get("perfil_cocina", {})
    return render_template("cocina/pedidos.html", perfil=perfil_cocina)

@routes_bp.route("/cocina/en-proceso")
@login_required
@rol_required(['3'])
def cocina_en_proceso():
    return render_template("cocina/en_proceso.html")

@routes_bp.route("/cocina/listos")
@login_required
@rol_required(['3'])
def cocina_listos():
    return render_template("cocina/listos.html")

# ── API Cocina ────────────────────────────────────────────
@routes_bp.route("/api/cocina/pedidos/pendientes", methods=["GET"])
@login_required
@rol_required(['1', '3'])
def api_cocina_pedidos_pendientes():
    return CocinaController.obtener_pedidos_pendientes()

@routes_bp.route("/api/cocina/pedidos/en-proceso", methods=["GET"])
@login_required
@rol_required(['1', '3'])
def api_cocina_pedidos_en_proceso():
    return CocinaController.obtener_pedidos_en_proceso()

@routes_bp.route("/api/cocina/pedidos/listos", methods=["GET"])
@login_required
@rol_required(['1', '3'])
def api_cocina_pedidos_listos():
    return CocinaController.obtener_pedidos_listos()

@routes_bp.route("/api/cocina/pedido/iniciar", methods=["POST"])
@login_required
@rol_required(['1', '3'])
def api_cocina_iniciar_preparacion():
    return CocinaController.iniciar_preparacion()

@routes_bp.route("/api/cocina/pedido/listo", methods=["POST"])
@login_required
@rol_required(['1', '3'])
def api_cocina_marcar_listo():
    return CocinaController.marcar_como_listo()

@routes_bp.route("/api/cocina/pedido/entregado", methods=["POST"])
@login_required
@rol_required(['1', '2', '3'])
def api_cocina_marcar_entregado():
    return CocinaController.marcar_como_entregado()

@routes_bp.route("/api/cocina/estadisticas", methods=["GET"])
@login_required
@rol_required(['1', '3'])
def api_cocina_estadisticas():
    return CocinaController.obtener_estadisticas_cocina()
