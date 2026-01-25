"""
Módulo de Rutas - Sistema de Restaurante Callejón 9
Adaptado a la estructura actual con roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import Blueprint
from controllers.auth.AuthController import AuthController, login_required, rol_required, permiso_required
from controllers.dashboard.dashboard_controller import DashboardController

routes_bp = Blueprint("routes", __name__)

# ============================================
# 🔑 AUTENTICACIÓN
# ============================================

routes_bp.add_url_rule("/", view_func=DashboardController.index, endpoint="home")
routes_bp.add_url_rule("/login", view_func=AuthController.login, methods=["GET", "POST"], endpoint="login")
routes_bp.add_url_rule("/logout", view_func=AuthController.logout, endpoint="logout")
routes_bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"], endpoint="verify_2fa")


# ============================================
# 👔 PANEL DE ADMINISTRACIÓN (Rol 1)
# ============================================

# Dashboard Principal
@routes_bp.route("/dashboard/admin")
@login_required
@rol_required(['1'])
def dashboard_admin():
    return DashboardController.admin()


# --- Gestión de Empleados ---
@routes_bp.route("/admin/empleados")
@login_required
@rol_required(['1'])
def admin_empleados_lista():
    return DashboardController.empleados_lista()

@routes_bp.route("/admin/empleados/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1'])
@permiso_required('puede_crear')
def admin_empleados_crear():
    return DashboardController.empleados_crear()


# --- Reportes y Analítica ---
@routes_bp.route("/admin/reportes")
@login_required
@rol_required(['1'])
@permiso_required('puede_ver_reportes')
def admin_reportes():
    return DashboardController.reportes()


# ============================================
# 🍽️ PANEL DE MESERO (Rol 2)
# ============================================

# Dashboard Mesero
@routes_bp.route("/dashboard/mesero")
@login_required
@rol_required(['2'])
def dashboard_mesero():
    return DashboardController.mesero()


# ============================================
# 👨‍🍳 PANEL DE COCINA (Rol 3)
# ============================================

# Dashboard Cocina
@routes_bp.route("/dashboard/cocina")
@login_required
@rol_required(['3'])
def dashboard_cocina():
    return DashboardController.cocina()


# ============================================
# 🛠️ UTILIDADES
# ============================================

@routes_bp.route('/toggle/theme')
@login_required
def toggle_theme():
    return DashboardController.toggle_theme()