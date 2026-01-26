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

# Ruta raíz - redirige según estado de sesión
@routes_bp.route("/")
def home():
    return DashboardController.index()

# Login
routes_bp.add_url_rule("/login", view_func=AuthController.login, methods=["GET", "POST"], endpoint="login")
routes_bp.add_url_rule("/logout", view_func=AuthController.logout, endpoint="logout")
routes_bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"], endpoint="verify_2fa")


# ============================================
# 👔 PANEL DE ADMINISTRACIÓN (Rol 1)
# ============================================

# Dashboard Principal
routes_bp.add_url_rule("/dashboard/admin", view_func=DashboardController.admin, endpoint="dashboard_admin")

# --- Gestión de Empleados ---
routes_bp.add_url_rule("/admin/empleados", view_func=DashboardController.empleados_lista, endpoint="admin_empleados_lista")
routes_bp.add_url_rule("/admin/empleados/crear", view_func=DashboardController.empleados_crear, methods=["GET", "POST"], endpoint="admin_empleados_crear")

# --- Reportes y Analítica ---
routes_bp.add_url_rule("/admin/reportes", view_func=DashboardController.reportes, endpoint="admin_reportes")


# ============================================
# 🍽️ PANEL DE MESERO (Rol 2)
# ============================================

# Dashboard Mesero
routes_bp.add_url_rule("/dashboard/mesero", view_func=DashboardController.mesero, endpoint="dashboard_mesero")


# ============================================
# 👨‍🍳 PANEL DE COCINA (Rol 3)
# ============================================

# Dashboard Cocina
routes_bp.add_url_rule("/dashboard/cocina", view_func=DashboardController.cocina, endpoint="dashboard_cocina")


# ============================================
# 🛠️ UTILIDADES
# ============================================

routes_bp.add_url_rule('/toggle/theme', view_func=DashboardController.toggle_theme, endpoint='toggle_theme')