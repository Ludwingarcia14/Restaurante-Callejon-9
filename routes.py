"""
Módulo de Rutas - Sistema Restaurante Callejón 9
Roles:
1 = Admin
2 = Mesero
3 = Cocina
4 = Inventario
"""

from flask import Blueprint, render_template, session, redirect, url_for
from controllers.auth.AuthController import AuthController, login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.dashboard.dashboardApiController import DashboardAPIController
from controllers.admin.BackupController import BackupController
from controllers.inventario.inventarioController import InventarioController

routes_bp = Blueprint("routes", __name__)

# =================================================
# AUTH
# =================================================

@routes_bp.route("/")
def home():
    return DashboardController.index()

routes_bp.add_url_rule("/login", view_func=AuthController.login, methods=["GET","POST"])
routes_bp.add_url_rule("/logout", view_func=AuthController.logout)
routes_bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"])

# =================================================
# API DASHBOARD ADMIN
# =================================================

@routes_bp.route("/api/dashboard/admin/stats")
@login_required
@rol_required(['1'])
def api_dashboard_stats():
    return DashboardAPIController.get_stats()


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


@routes_bp.route("/api/dashboard/admin/actividad")
@login_required
@rol_required(['1'])
def api_dashboard_actividad():
    return DashboardAPIController.get_actividad_reciente()

# =================================================
# ADMIN PANEL
# =================================================

@routes_bp.route("/dashboard/admin")
@login_required
@rol_required(['1'])
def dashboard_admin():
    return DashboardController.admin()


@routes_bp.route("/admin/empleados")
@login_required
@rol_required(['1'])
def admin_empleados_lista():
    return DashboardController.empleados_lista()


@routes_bp.route("/admin/empleados/crear", methods=["GET","POST"])
@login_required
@rol_required(['1'])
def admin_empleados_crear():
    return DashboardController.empleados_crear()


@routes_bp.route("/support/reportes")
@login_required
@rol_required(['1'])
def admin_reportes():
    return DashboardController.reportes()

# =================================================
# MESERO
# =================================================

@routes_bp.route("/dashboard/mesero")
@login_required
@rol_required(['2'])
def dashboard_mesero():
    return DashboardController.mesero()

# =================================================
# COCINA
# =================================================

@routes_bp.route("/dashboard/cocina")
@login_required
@rol_required(['3'])
def dashboard_cocina():
    return DashboardController.cocina()

# =================================================
# INVENTARIO
# =================================================

@routes_bp.route("/inventario/dashboard")
@login_required
@rol_required(['1','4'])
def dashboard_inventario():
    return InventarioController.dashboard()


@routes_bp.route("/inventario/insumos")
@login_required
@rol_required(['1','4'])
def inventario_insumos():
    return InventarioController.lista_insumos()


@routes_bp.route("/inventario/insumos/crear", methods=["GET","POST"])
@login_required
@rol_required(['1','4'])
def inventario_crear_insumo():
    return InventarioController.crear_insumo()

# =================================================
# BACKUP ADMIN
# =================================================

@routes_bp.route("/admin/backup")
@login_required
@rol_required(['1'])
def admin_backup_view():
    return BackupController.index()


@routes_bp.route("/admin/backup/create", methods=["POST"])
@login_required
@rol_required(['1'])
def admin_backup_create():
    return BackupController.create()


@routes_bp.route("/admin/backup/delete/<filename>")
@login_required
@rol_required(['1'])
def admin_backup_delete(filename):
    return BackupController.delete_file(filename)


@routes_bp.route("/admin/backup/restore", methods=["GET","POST"])
@login_required
@rol_required(['1'])
def admin_backup_restore():
    return BackupController.restore()

