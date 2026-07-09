from . import routes_bp
from flask import redirect, url_for, render_template, request
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.inventario.inventarioController import InventarioController
from models.inventario_model import Insumo

@routes_bp.route("/cocina/inventario")
@login_required
@rol_required(['1', '3', '4'])
def cocina_inventario():
    return redirect(url_for('routes.dashboard_inventario'))

@routes_bp.route("/inventario/dashboard")
@login_required
@rol_required(['1', '3', '4'])
def dashboard_inventario():
    return DashboardController.inventario()

@routes_bp.route("/inventario/insumos")
@login_required
@rol_required(['1', '3', '4'])
def inventario_insumos():
    categoria = request.args.get("categoria")
    filtros = {"categoria": categoria} if categoria else None
    insumos = Insumo.obtener_todos(filtros)
    return render_template(
        "inventario/insumos.html",
        insumos=insumos,
        categoria_seleccionada=categoria
    )

@routes_bp.route("/inventario/insumos/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4', '3'])
def inventario_crear_insumo():
    return InventarioController.crear_insumo()

@routes_bp.route("/inventario/movimientos/entrada", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4', '3'])
def inventario_registrar_entrada():
    return InventarioController.registrar_entrada()

@routes_bp.route("/inventario/movimientos/salida", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4', '3'])
def inventario_registrar_salida():
    return InventarioController.registrar_salida()

@routes_bp.route("/inventario/movimientos/merma", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4', '3'])
def inventario_registrar_merma():
    return InventarioController.registrar_merma()

@routes_bp.route("/inventario/movimientos/historial")
@login_required
@rol_required(['1', '4', '3'])
def inventario_historial():
    return InventarioController.historial_movimientos()

@routes_bp.route("/inventario/alertas")
@login_required
@rol_required(['1', '4'])
def inventario_alertas():
    return InventarioController.alertas_stock()

@routes_bp.route("/api/inventario/alertas/resolver", methods=["POST"])
@login_required
@rol_required(['1', '4', '3'])
def inventario_resolver_alerta():
    return InventarioController.resolver_alerta()

@routes_bp.route("/inventario/proveedores")
@login_required
@rol_required(['1', '4', '3'])
def inventario_proveedores():
    return InventarioController.lista_proveedores()

@routes_bp.route("/inventario/proveedores/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4', '3'])
def inventario_crear_proveedor():
    return InventarioController.crear_proveedor()

@routes_bp.route("/inventario/reportes")
@login_required
@rol_required(['1', '4', '3'])
def inventario_reportes():
    return InventarioController.reportes()

@routes_bp.route("/inventario/prediccion")
@login_required
@rol_required(['1', '4', '3'])
def inventario_prediccion():
    return InventarioController.prediccion()
