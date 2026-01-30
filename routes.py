"""
Módulo de Rutas - Sistema de Restaurante Callejón 9
Roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import Blueprint, render_template, session, redirect, url_for
from controllers.auth.AuthController import AuthController, login_required, rol_required, permiso_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.admin.BackupController import BackupController

routes_bp = Blueprint("routes", __name__)

# ============================================
#  AUTENTICACIÓN
# ============================================

# Ruta raíz - redirige según estado de sesión
@routes_bp.route("/")
def home():
    return DashboardController.index()

# Login y Logout
routes_bp.add_url_rule("/login", view_func=AuthController.login, methods=["GET", "POST"], endpoint="login")
routes_bp.add_url_rule("/logout", view_func=AuthController.logout, endpoint="logout")
routes_bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"], endpoint="verify_2fa")


# ============================================
#  PANEL DE ADMINISTRACIÓN (Rol 1)
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
def admin_empleados_crear():
    return DashboardController.empleados_crear()

# --- Reportes y Analítica ---
@routes_bp.route("/support/reportes")
@login_required
@rol_required(['1'])
def admin_reportes():
    return DashboardController.reportes()


# ============================================
# 🍽️ PANEL DE MESERO (Rol 2)
# ============================================

@routes_bp.route("/dashboard/mesero")
@login_required
@rol_required(['2'])
def dashboard_mesero():
    """Dashboard principal del mesero"""
    return DashboardController.mesero()

@routes_bp.route("/mesero/mesas")
@login_required
@rol_required(['2'])
def mesero_mesas():
    """Vista de mesas asignadas"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
        return redirect(url_for("routes.login"))
    
    perfil_mesero = session.get("perfil_mesero", {})
    stats = {
        "mesas_asignadas": perfil_mesero.get("mesas_asignadas", []),
        "comandas_activas": 0,
        "propinas_dia": perfil_mesero.get("propinas", {}).get("acumulada_dia", 0)
    }
    
    return render_template("mesero/dashboard.html",
                         perfil=perfil_mesero,
                         stats=stats)

@routes_bp.route("/mesero/comandas")
@login_required
@rol_required(['2'])
def mesero_comandas():
    """Vista de comandas activas"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
        return redirect(url_for("routes.login"))
    
    perfil_mesero = session.get("perfil_mesero", {})
    stats = {
        "mesas_asignadas": perfil_mesero.get("mesas_asignadas", []),
    }
    
    return render_template("mesero/comandas.html",
                         perfil=perfil_mesero,
                         stats=stats)

@routes_bp.route("/mesero/menu")
@login_required
@rol_required(['2'])
def mesero_menu():
    """Vista del menú para tomar pedidos"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
        return redirect(url_for("routes.login"))
    
    perfil_mesero = session.get("perfil_mesero", {})
    stats = {
        "mesas_asignadas": perfil_mesero.get("mesas_asignadas", []),
    }
    
    return render_template("mesero/menu.html",
                         perfil=perfil_mesero,
                         stats=stats)

@routes_bp.route("/mesero/propinas")
@login_required
@rol_required(['2'])
def mesero_propinas():
    """Vista de propinas del día"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
        return redirect(url_for("routes.login"))
    
    # Placeholder: implementar lógica de propinas
    return render_template("mesero/dashboard.html")

@routes_bp.route("/mesero/historial")
@login_required
@rol_required(['2'])
def mesero_historial():
    """Vista de historial de comandas"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
        return redirect(url_for("routes.login"))
    
    # Placeholder: implementar lógica de historial
    return render_template("mesero/comandas.html")

# ============================================
# 👨‍🍳 PANEL DE COCINA (Rol 3)
# ============================================

@routes_bp.route("/dashboard/cocina")
@login_required
@rol_required(['3'])
def dashboard_cocina():
    """Dashboard principal de cocina"""
    return DashboardController.cocina()

@routes_bp.route("/cocina/pedidos")
@login_required
@rol_required(['3'])
def cocina_pedidos():
    """Vista de pedidos pendientes"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
        return redirect(url_for("routes.login"))
    
    perfil_cocina = session.get("perfil_cocina", {})
    
    return render_template("cocina/pedidos.html",
                         perfil=perfil_cocina)

@routes_bp.route("/cocina/en-proceso")
@login_required
@rol_required(['3'])
def cocina_en_proceso():
    """Vista de pedidos en preparación"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
        return redirect(url_for("routes.login"))
    
    # Placeholder: implementar vista
    return render_template("cocina/dashboard.html")

@routes_bp.route("/cocina/listos")
@login_required
@rol_required(['3'])
def cocina_listos():
    """Vista de pedidos listos"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
        return redirect(url_for("routes.login"))
    
    # Placeholder: implementar vista
    return render_template("cocina/dashboard.html")

@routes_bp.route("/cocina/inventario")
@login_required
@rol_required(['3'])
def cocina_inventario():
    """Vista de consulta de inventario (solo lectura)"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
        return redirect(url_for("routes.login"))
    
    # Placeholder: implementar vista de inventario
    return render_template("cocina/dashboard.html")


# ============================================
#  UTILIDADES
# ============================================

@routes_bp.route('/toggle/theme')
@login_required
def toggle_theme():
    from controllers.dashboard.dashboard_controller import toggle_theme as toggle_theme_func
    return toggle_theme_func()

# ------------------------------------------------------------
# Módulo de Seguridad y Backup
# Gestión Principal de Respaldos (Listar y Panel)
routes_bp.add_url_rule("/admin/backup", view_func=BackupController.index, endpoint="admin_backup_view")

# Creación de Respaldo (POST)
routes_bp.add_url_rule("/admin/backup/create", view_func=BackupController.create, methods=["POST"], endpoint="admin_backup_create")

# Eliminación de Archivo Físico
routes_bp.add_url_rule("/admin/backup/delete/<filename>", view_func=BackupController.delete_file, endpoint="admin_backup_delete")

# Restauración
# Vista de Restauración (Historial y Carga)
routes_bp.add_url_rule("/admin/restore", view_func=BackupController.restore_view, endpoint="admin_backup_restore_view")
routes_bp.add_url_rule("/admin/backup/restore", view_func=BackupController.restore, methods=["POST"], endpoint="admin_backup_restore")

# Acción de Restaurar (POST - Procesa archivos del servidor y subidos)
routes_bp.add_url_rule("/admin/backup/restore", view_func=BackupController.restore, methods=["POST"], endpoint="admin_backup_restore")