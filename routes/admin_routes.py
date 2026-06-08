from . import routes_bp
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.dashboard.dashboardApiController import DashboardAPIController
from controllers.admin.BackupController import BackupController
from controllers.menu.menuController import MenuController
from controllers.analytics.analytics_controller import AnalyticsController

# ── Dashboard Admin ──────────────────────────────────────
@routes_bp.route("/dashboard/admin")
@login_required
@rol_required(['1'])
def dashboard_admin():
    return DashboardController.admin()

# ── Empleados ────────────────────────────────────────────
@routes_bp.route("/admin/empleados")
@login_required
@rol_required(['1'])
def admin_empleados_lista():
    return DashboardController.empleados_lista()

@routes_bp.route("/admin/empleados/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1'])
def admin_empleados_crear():
    return DashboardController.empleados_crear()

@routes_bp.route("/admin/empleados/editar/<empleado_id>", methods=["GET", "POST"])
@login_required
@rol_required(['1'])
def admin_empleados_editar(empleado_id):
    return DashboardController.empleados_editar(empleado_id)

# ── API Empleados ─────────────────────────────────────────
@routes_bp.route('/api/dashboard/admin/stats')
@login_required
@rol_required(['1'])
def api_dashboard_stats():
    return DashboardAPIController.get_stats()

@routes_bp.route("/api/dashboard/admin/actividad")
@login_required
@rol_required(['1'])
def api_dashboard_actividad():
    return DashboardAPIController.get_actividad_reciente()

@routes_bp.route("/api/dashboard/admin/personal")
@login_required
@rol_required(['1'])
def api_dashboard_personal():
    return DashboardAPIController.get_personal_activo()

@routes_bp.route("/api/empleados/todos")
@login_required
@rol_required(['1'])
def api_empleados_todos():
    return DashboardAPIController.get_todos_empleados()

@routes_bp.route("/api/empleados/<empleado_id>/detalle")
@login_required
@rol_required(['1'])
def api_empleado_detalle(empleado_id):
    return DashboardAPIController.get_empleado_detalle(empleado_id)

@routes_bp.route("/api/empleados/<empleado_id>/eliminar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_empleado_eliminar(empleado_id):
    return DashboardAPIController.eliminar_empleado(empleado_id)

@routes_bp.route("/api/empleados/<empleado_id>/actualizar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_empleado_actualizar(empleado_id):
    return DashboardAPIController.actualizar_empleado(empleado_id)

@routes_bp.route("/api/empleados/<empleado_id>/desconectar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_empleado_desconectar(empleado_id):
    return DashboardAPIController.desconectar_usuario(empleado_id)

# ── Menú ──────────────────────────────────────────────────
@routes_bp.route("/admin/menu")
@login_required
@rol_required(['1'])
def admin_menu():
    return MenuController.index()

@routes_bp.route("/admin/menu/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1'])
def admin_menu_crear():
    return MenuController.crear()

@routes_bp.route("/admin/menu/editar/<platillo_id>", methods=["GET", "POST"])
@login_required
@rol_required(['1'])
def admin_menu_editar(platillo_id):
    return MenuController.editar(platillo_id)

@routes_bp.route("/admin/menu/detalle/<platillo_id>")
@login_required
@rol_required(['1'])
def admin_menu_detalle(platillo_id):
    return MenuController.detalle(platillo_id)

@routes_bp.route("/admin/menu/categorias")
@login_required
@rol_required(['1'])
def admin_menu_categorias():
    return MenuController.categorias()

# ── API Menú ──────────────────────────────────────────────
@routes_bp.route("/api/menu/crear", methods=["POST"])
@login_required
@rol_required(['1'])
def api_menu_crear():
    return MenuController.api_crear_platillo()

@routes_bp.route("/api/menu/<platillo_id>/actualizar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_menu_actualizar(platillo_id):
    return MenuController.api_actualizar_platillo(platillo_id)

@routes_bp.route("/api/menu/<platillo_id>/eliminar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_menu_eliminar(platillo_id):
    return MenuController.api_eliminar_platillo(platillo_id)

@routes_bp.route("/api/menu/buscar")
@login_required
@rol_required(['1', '2'])
def api_menu_buscar():
    return MenuController.api_buscar_platillos()

@routes_bp.route("/api/menu/<platillo_id>")
@login_required
@rol_required(['1', '2', '3'])
def api_menu_get_platillo(platillo_id):
    return MenuController.api_get_platillo(platillo_id)

@routes_bp.route("/api/menu")
@login_required
@rol_required(['1', '2', '3'])
def api_menu():
    return MenuController.api_get_menu()

@routes_bp.route("/api/menu/<platillo_id>/toggle", methods=["POST"])
@login_required
@rol_required(['1'])
def api_menu_toggle(platillo_id):
    return MenuController.api_toggle_platillo(platillo_id)

@routes_bp.route("/api/categorias")
@login_required
@rol_required(['1'])
def api_categorias():
    return MenuController.api_get_categorias()

# ── Reportes ──────────────────────────────────────────────
@routes_bp.route("/support/reportes")
@login_required
@rol_required(['1'])
def admin_reportes():
    return DashboardController.reportes()

# ── Analytics ─────────────────────────────────────────────
@routes_bp.route("/admin/analytics")
@login_required
@rol_required(['1'])
def analytics_index():
    return AnalyticsController.index()

@routes_bp.route("/api/analytics/kpis")
@login_required
@rol_required(['1'])
def api_analytics_kpis():
    return AnalyticsController.get_kpis()

@routes_bp.route("/api/analytics/top-platillos")
@login_required
@rol_required(['1'])
def api_analytics_top_platillos():
    return AnalyticsController.get_top_platillos()

@routes_bp.route("/api/analytics/ventas-por-dia")
@login_required
@rol_required(['1'])
def api_analytics_ventas_dia():
    return AnalyticsController.get_ventas_por_dia()

@routes_bp.route("/api/analytics/metodos-pago")
@login_required
@rol_required(['1'])
def api_analytics_metodos_pago():
    return AnalyticsController.get_ventas_por_metodo_pago()

@routes_bp.route("/api/analytics/horas-pico")
@login_required
@rol_required(['1'])
def api_analytics_horas_pico():
    return AnalyticsController.get_horas_pico()

@routes_bp.route("/api/analytics/rendimiento-meseros")
@login_required
@rol_required(['1'])
def api_analytics_meseros():
    return AnalyticsController.get_rendimiento_meseros()

@routes_bp.route("/api/analytics/ventas-por-mesa")
@login_required
@rol_required(['1'])
def api_analytics_ventas_mesa():
    return AnalyticsController.get_ventas_por_mesa()

# ── Analytics avanzado: Pareto, Asociación, Predicción ───
@routes_bp.route("/admin/analytics/pareto")
@login_required
@rol_required(['1'])
def analytics_pareto():
    return AnalyticsController.vista_pareto()

@routes_bp.route("/api/analytics/pareto")
@login_required
@rol_required(['1', '2'])
def api_analytics_pareto():
    return AnalyticsController.get_pareto()

@routes_bp.route("/admin/analytics/asociacion")
@login_required
@rol_required(['1'])
def analytics_asociacion():
    return AnalyticsController.vista_asociacion()

@routes_bp.route("/api/analytics/asociacion")
@login_required
@rol_required(['1', '2'])
def api_analytics_asociacion():
    return AnalyticsController.get_asociacion()

@routes_bp.route("/admin/analytics/prediccion")
@login_required
@rol_required(['1'])
def analytics_prediccion():
    return AnalyticsController.vista_prediccion()

@routes_bp.route("/api/analytics/prediccion")
@login_required
@rol_required(['1', '2'])
def api_analytics_prediccion():
    return AnalyticsController.get_prediccion()

# ── Backup y Seguridad ────────────────────────────────────
@routes_bp.route('/admin/backup', methods=['GET'])
@login_required
@rol_required(['1'])
def admin_backup_view():
    return BackupController.index()

@routes_bp.route('/admin/backup/create', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_create():
    return BackupController.create()

@routes_bp.route('/admin/backup/delete/<filename>', methods=['GET'])
@login_required
@rol_required(['1'])
def admin_backup_delete(filename):
    return BackupController.delete_file(filename)

@routes_bp.route('/admin/backup/delete-with-auth/<filename>', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_delete_with_auth(filename):
    return BackupController.delete_file_with_auth()

@routes_bp.route('/admin/backup/download-with-auth/<filename>', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_download_with_auth(filename):
    return BackupController.download_with_auth()

@routes_bp.route('/admin/backup/restore', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_restore():
    return BackupController.restore()

@routes_bp.route('/admin/backup/configure', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_configure():
    return BackupController.configure_auto_backup()
