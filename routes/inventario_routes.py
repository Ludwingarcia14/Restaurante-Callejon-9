from flask import render_template, redirect, url_for
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.inventario.inventarioController import InventarioController
from models.inventario_model import Insumo


def register_inventario_routes(bp):

    @bp.route("/cocina/inventario")
    @login_required
    @rol_required(['1', '3', '4'])
    def cocina_inventario():
        return redirect(url_for('routes.dashboard_inventario'))

    @bp.route("/cocina/graficas-inventario")
    @login_required
    @rol_required(['3'])
    def cocina_graficas_inventario():
        return InventarioController.graficas_cocina()

    @bp.route("/inventario/insumos")
    def inventario_insumos():
        insumos = Insumo.obtener_todos()
        return render_template("inventario/insumos.html", insumos=insumos)

    @bp.route("/inventario/dashboard")
    @login_required
    @rol_required(['1', '3', '4'])
    def dashboard_inventario():
        return DashboardController.inventario()

    @bp.route("/inventario/insumos/crear", methods=["GET", "POST"])
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_crear_insumo():
        return InventarioController.crear_insumo()

    @bp.route("/inventario/movimientos/entrada", methods=["GET", "POST"])
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_registrar_entrada():
        return InventarioController.registrar_entrada()

    @bp.route("/inventario/movimientos/salida", methods=["GET", "POST"])
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_registrar_salida():
        return InventarioController.registrar_salida()

    @bp.route("/inventario/movimientos/merma", methods=["GET", "POST"])
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_registrar_merma():
        return InventarioController.registrar_merma()

    @bp.route("/inventario/movimientos/historial")
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_historial():
        return InventarioController.historial_movimientos()

    @bp.route("/inventario/alertas")
    @login_required
    @rol_required(['1', '4'])
    def inventario_alertas():
        return InventarioController.alertas_stock()

    @bp.route("/api/inventario/alertas/resolver", methods=["POST"])
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_resolver_alerta():
        return InventarioController.resolver_alerta()

    @bp.route("/inventario/proveedores")
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_proveedores():
        return InventarioController.lista_proveedores()

    @bp.route("/inventario/proveedores/crear", methods=["GET", "POST"])
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_crear_proveedor():
        return InventarioController.crear_proveedor()

    @bp.route("/inventario/reportes")
    @login_required
    @rol_required(['1', '4', '3'])
    def inventario_reportes():
        return InventarioController.reportes()
