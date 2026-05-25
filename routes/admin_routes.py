from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.dashboard.dashboardApiController import DashboardAPIController
from controllers.menu.menuController import MenuController


def register_admin_routes(bp):

    # --- Dashboard ---
    @bp.route("/dashboard/admin")
    @login_required
    @rol_required(['1'])
    def dashboard_admin():
        return DashboardController.admin()

    @bp.route("/support/reportes")
    @login_required
    @rol_required(['1'])
    def admin_reportes():
        return DashboardController.reportes()

    # --- Empleados (vistas) ---
    @bp.route("/admin/empleados")
    @login_required
    @rol_required(['1'])
    def admin_empleados_lista():
        return DashboardController.empleados_lista()

    @bp.route("/admin/empleados/crear", methods=["GET", "POST"])
    @login_required
    @rol_required(['1'])
    def admin_empleados_crear():
        return DashboardController.empleados_crear()

    @bp.route("/admin/empleados/editar/<empleado_id>", methods=["GET", "POST"])
    @login_required
    @rol_required(['1'])
    def admin_empleados_editar(empleado_id):
        return DashboardController.empleados_editar(empleado_id)

    # --- Empleados (API) ---
    @bp.route('/api/dashboard/admin/stats')
    @login_required
    @rol_required(['1'])
    def api_dashboard_stats():
        return DashboardAPIController.get_stats()

    @bp.route("/api/dashboard/admin/actividad")
    @login_required
    @rol_required(['1'])
    def api_dashboard_actividad():
        return DashboardAPIController.get_actividad_reciente()

    @bp.route("/api/dashboard/admin/personal")
    @login_required
    @rol_required(['1'])
    def api_dashboard_personal():
        return DashboardAPIController.get_personal_activo()

    @bp.route("/api/empleados/todos")
    @login_required
    @rol_required(['1'])
    def api_empleados_todos():
        return DashboardAPIController.get_todos_empleados()

    @bp.route("/api/empleados/<empleado_id>/detalle")
    @login_required
    @rol_required(['1'])
    def api_empleado_detalle(empleado_id):
        return DashboardAPIController.get_empleado_detalle(empleado_id)

    @bp.route("/api/empleados/<empleado_id>/eliminar", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_empleado_eliminar(empleado_id):
        return DashboardAPIController.eliminar_empleado(empleado_id)

    @bp.route("/api/empleados/<empleado_id>/actualizar", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_empleado_actualizar(empleado_id):
        return DashboardAPIController.actualizar_empleado(empleado_id)

    @bp.route("/api/empleados/<empleado_id>/desconectar", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_empleado_desconectar(empleado_id):
        return DashboardAPIController.desconectar_usuario(empleado_id)

    # --- Menú (vistas) ---
    @bp.route("/admin/menu")
    @login_required
    @rol_required(['1'])
    def admin_menu():
        return MenuController.index()

    @bp.route("/admin/menu/crear", methods=["GET", "POST"])
    @login_required
    @rol_required(['1'])
    def admin_menu_crear():
        return MenuController.crear()

    @bp.route("/admin/menu/editar/<platillo_id>", methods=["GET", "POST"])
    @login_required
    @rol_required(['1'])
    def admin_menu_editar(platillo_id):
        return MenuController.editar(platillo_id)

    @bp.route("/admin/menu/detalle/<platillo_id>")
    @login_required
    @rol_required(['1'])
    def admin_menu_detalle(platillo_id):
        return MenuController.detalle(platillo_id)

    @bp.route("/admin/menu/categorias")
    @login_required
    @rol_required(['1'])
    def admin_menu_categorias():
        return MenuController.categorias()

    # --- Menú (API) ---
    @bp.route("/api/menu/crear", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_menu_crear():
        return MenuController.api_crear_platillo()

    @bp.route("/api/menu/<platillo_id>/actualizar", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_menu_actualizar(platillo_id):
        return MenuController.api_actualizar_platillo(platillo_id)

    @bp.route("/api/menu/<platillo_id>/eliminar", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_menu_eliminar(platillo_id):
        return MenuController.api_eliminar_platillo(platillo_id)

    @bp.route("/api/menu/buscar")
    @login_required
    @rol_required(['1', '2'])
    def api_menu_buscar():
        return MenuController.api_buscar_platillos()

    @bp.route("/api/menu/<platillo_id>")
    @login_required
    @rol_required(['1', '2', '3'])
    def api_menu_get_platillo(platillo_id):
        return MenuController.api_get_platillo(platillo_id)

    @bp.route("/api/menu", methods=["GET"])
    @login_required
    @rol_required(['1', '2', '3'])
    def api_menu():
        return MenuController.api_get_menu()

    @bp.route("/api/menu/<platillo_id>/toggle", methods=["POST"])
    @login_required
    @rol_required(['1'])
    def api_menu_toggle(platillo_id):
        return MenuController.api_toggle_platillo(platillo_id)

    @bp.route("/api/categorias")
    @login_required
    @rol_required(['1'])
    def api_categorias():
        return MenuController.api_get_categorias()
