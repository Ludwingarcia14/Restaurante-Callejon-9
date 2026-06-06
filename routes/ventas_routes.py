from . import routes_bp
from controllers.auth.AuthController import login_required, rol_required
from controllers.venta.ventasController import VentasController

@routes_bp.route("/ventas")
@login_required
@rol_required(['1', '2'])
def ventas_dashboard():
    return VentasController.dashboard()

@routes_bp.route("/ventas/nueva", methods=["GET", "POST"])
@login_required
@rol_required(['1', '2'])
def ventas_nueva():
    return VentasController.nueva_venta()

@routes_bp.route("/ventas/cuentas")
@login_required
@rol_required(['1', '2'])
def ventas_cuentas():
    return VentasController.cuentas()

@routes_bp.route("/ventas/cerrar/<cuenta_id>", methods=["GET", "POST"])
@login_required
@rol_required(['1', '2'])
def ventas_cerrar_cuenta(cuenta_id):
    return VentasController.cerrar_cuenta(cuenta_id)

@routes_bp.route("/ventas/corte")
@login_required
@rol_required(['1'])
def ventas_corte():
    return VentasController.corte_caja()

# ── API Ventas ────────────────────────────────────────────
@routes_bp.route("/api/ventas", methods=["GET"])
@login_required
@rol_required(['1', '2'])
def api_ventas():
    return VentasController.api_get_ventas()

@routes_bp.route("/api/ventas/crear", methods=["POST"])
@login_required
@rol_required(['1', '2'])
def api_ventas_crear():
    return VentasController.api_crear_venta()

@routes_bp.route("/api/ventas/<venta_id>", methods=["GET"])
@login_required
@rol_required(['1', '2'])
def api_venta_detalle(venta_id):
    return VentasController.api_get_venta(venta_id)

@routes_bp.route("/api/ventas/<venta_id>/actualizar", methods=["POST"])
@login_required
@rol_required(['1', '2'])
def api_venta_actualizar(venta_id):
    return VentasController.api_actualizar_venta(venta_id)

@routes_bp.route("/api/ventas/<venta_id>/completar", methods=["POST"])
@login_required
@rol_required(['1', '2'])
def api_venta_completar(venta_id):
    return VentasController.api_completar_venta(venta_id)

@routes_bp.route("/api/ventas/<venta_id>/cancelar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_venta_cancelar(venta_id):
    return VentasController.api_cancelar_venta(venta_id)

@routes_bp.route("/api/ventas/<venta_id>/eliminar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_venta_eliminar(venta_id):
    return VentasController.api_eliminar_venta(venta_id)

@routes_bp.route("/api/ventas/estadisticas", methods=["GET"])
@login_required
@rol_required(['1', '2'])
def api_ventas_estadisticas():
    return VentasController.api_get_estadisticas()

@routes_bp.route("/api/cuentas", methods=["GET"])
@login_required
@rol_required(['1', '2'])
def api_cuentas():
    return VentasController.api_get_cuentas()

@routes_bp.route("/api/cuentas/<cuenta_id>/cerrar", methods=["POST"])
@login_required
@rol_required(['1', '2'])
def api_cuenta_cerrar(cuenta_id):
    return VentasController.api_cerrar_cuenta(cuenta_id)

@routes_bp.route("/api/corte/generar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_corte_generar():
    return VentasController.api_generar_corte()

@routes_bp.route("/api/cortes", methods=["GET"])
@login_required
@rol_required(['1'])
def api_cortes():
    return VentasController.api_get_cortes()
