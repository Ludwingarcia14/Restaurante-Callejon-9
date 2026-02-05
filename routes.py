"""
Módulo de Rutas - Sistema de Restaurante Callejón 9
Roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from controllers.auth.AuthController import AuthController, login_required, rol_required, permiso_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.admin.BackupController import BackupController
from controllers.inventario.inventarioController import InventarioController
from controllers.dashboard.dashboardApiController import DashboardAPIController
from controllers.cocina.pedidos_controller import PedidosController
from controllers.cocina.platillos_no_disponibles_controller import PlatillosNoDisponiblesController

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

@routes_bp.route("/api/dashboard/admin/stats")
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
    return render_template("cocina/en_proceso.html")

@routes_bp.route("/cocina/listos")
@login_required
@rol_required(['3'])
def cocina_listos():
    """Vista de pedidos listos"""
    if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
        return redirect(url_for("routes.login"))
    
    # Placeholder: implementar vista
    return render_template("cocina/listos.html")

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
# 📦 PANEL DE INVENTARIO (Rol 4)
# ============================================

# Dashboard
@routes_bp.route("/inventario/dashboard")
@login_required
@rol_required(['1', '4'])  # Admin e Inventario
def dashboard_inventario():
    return InventarioController.dashboard()

# --- Gestión de Insumos ---
@routes_bp.route("/inventario/insumos")
@login_required
@rol_required(['1', '4'])
def inventario_insumos():
    return InventarioController.lista_insumos()

@routes_bp.route("/inventario/insumos/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_crear_insumo():
    return InventarioController.crear_insumo()

# --- Movimientos ---
@routes_bp.route("/inventario/movimientos/entrada", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_registrar_entrada():
    return InventarioController.registrar_entrada()

@routes_bp.route("/inventario/movimientos/salida", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_registrar_salida():
    return InventarioController.registrar_salida()

@routes_bp.route("/inventario/movimientos/merma", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_registrar_merma():
    return InventarioController.registrar_merma()

@routes_bp.route("/inventario/movimientos/historial")
@login_required
@rol_required(['1', '4'])
def inventario_historial():
    return InventarioController.historial_movimientos()

# --- Alertas ---
@routes_bp.route("/inventario/alertas")
@login_required
@rol_required(['1', '4'])
def inventario_alertas():
    return InventarioController.alertas_stock()

@routes_bp.route("/api/inventario/alertas/resolver", methods=["POST"])
@login_required
@rol_required(['1', '4'])
def inventario_resolver_alerta():
    return InventarioController.resolver_alerta()

# --- Proveedores ---
@routes_bp.route("/inventario/proveedores")
@login_required
@rol_required(['1', '4'])
def inventario_proveedores():
    return InventarioController.lista_proveedores()

@routes_bp.route("/inventario/proveedores/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_crear_proveedor():
    return InventarioController.crear_proveedor()

# --- Reportes ---
@routes_bp.route("/inventario/reportes")
@login_required
@rol_required(['1', '4'])
def inventario_reportes():
    return InventarioController.reportes()

# ============================================
# 👨‍🍳 API DE COCINA (Endpoints JSON)
# ============================================

# --- Pedidos API ---
@routes_bp.route("/api/cocina/pedidos", methods=['GET'])
@login_required
@rol_required(['3'])
def api_obtener_pedidos():
    """Obtiene todos los pedidos pendientes"""
    pedidos = PedidosController.obtener_todos_pedidos()
    return jsonify({'success': True, 'pedidos': pedidos})

@routes_bp.route("/api/cocina/pedidos/preparacion", methods=['GET'])
@login_required
@rol_required(['3'])
def api_obtener_pedidos_preparacion():
    """Obtiene todos los pedidos en preparación"""
    pedidos = PedidosController.obtener_pedidos_preparacion()
    return jsonify({'success': True, 'pedidos': pedidos})

@routes_bp.route("/api/cocina/pedidos/listos", methods=['GET'])
@login_required
@rol_required(['3'])
def api_obtener_pedidos_listos():
    """Obtiene todos los pedidos listos"""
    pedidos = PedidosController.obtener_pedidos_listos()
    return jsonify({'success': True, 'pedidos': pedidos})

@routes_bp.route("/api/cocina/pedidos/<int:pedido_id>", methods=['GET'])
@login_required
@rol_required(['3'])
def api_obtener_detalle_pedido(pedido_id):
    """Obtiene los detalles de un pedido específico"""
    detalle = PedidosController.obtener_detalle_pedido(pedido_id)
    if not detalle:
        return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
    return jsonify({'success': True, 'pedido': detalle})

@routes_bp.route("/api/cocina/pedidos", methods=['POST'])
@login_required
@rol_required(['3'])
def api_crear_pedido():
    """Crea un nuevo pedido"""
    data = request.get_json()
    resultado = PedidosController.crear_pedido(data)
    status_code = 201 if resultado['success'] else 400
    return jsonify(resultado), status_code

@routes_bp.route("/api/cocina/pedidos/<int:pedido_id>/iniciar-preparacion", methods=['PUT'])
@login_required
@rol_required(['3'])
def api_iniciar_preparacion(pedido_id):
    """Inicia la preparación de un pedido"""
    resultado = PedidosController.iniciar_preparacion(pedido_id)
    status_code = 200 if resultado['success'] else 400
    return jsonify(resultado), status_code

@routes_bp.route("/api/cocina/pedidos/<int:pedido_id>/marcar-listo", methods=['PUT'])
@login_required
@rol_required(['3'])
def api_marcar_pedido_listo(pedido_id):
    """Marca un pedido como listo para entregar"""
    resultado = PedidosController.marcar_pedido_listo(pedido_id)
    status_code = 200 if resultado['success'] else 400
    return jsonify(resultado), status_code

@routes_bp.route("/api/cocina/detalles/<int:detalle_id>/estado", methods=['PUT'])
@login_required
@rol_required(['3'])
def api_actualizar_estado_platillo(detalle_id):
    """Actualiza el estado de un platillo"""
    data = request.get_json()
    nuevo_estado = data.get('estado')  # no_iniciado, preparando, listo
    resultado = PedidosController.actualizar_estado_platillo(detalle_id, nuevo_estado)
    status_code = 200 if resultado['success'] else 400
    return jsonify(resultado), status_code

# --- Platillos No Disponibles API ---
@routes_bp.route("/api/cocina/platillos-no-disponibles", methods=['GET'])
@login_required
@rol_required(['3'])
def api_obtener_platillos_no_disponibles():
    """Obtiene lista de platillos no disponibles"""
    no_disponibles = PlatillosNoDisponiblesController.obtener_no_disponibles()
    return jsonify({'success': True, 'platillos': no_disponibles})

@routes_bp.route("/api/cocina/platillos-no-disponibles", methods=['POST'])
@login_required
@rol_required(['3'])
def api_marcar_platillo_no_disponible():
    """Marca un platillo como no disponible"""
    data = request.get_json()
    resultado = PlatillosNoDisponiblesController.marcar_no_disponible(data)
    status_code = 201 if resultado['success'] else 400
    return jsonify(resultado), status_code

@routes_bp.route("/api/cocina/platillos/<int:platillo_id>/reactivar", methods=['PUT'])
@login_required
@rol_required(['3'])
def api_reactivar_platillo(platillo_id):
    """Reactiva un platillo no disponible"""
    resultado = PlatillosNoDisponiblesController.reactivar_platillo(platillo_id)
    status_code = 200 if resultado['success'] else 400
    return jsonify(resultado), status_code

# ============================================
#  UTILIDADES
# ============================================

@routes_bp.route('/toggle/theme')
@login_required
def toggle_theme():
    from controllers.dashboard.dashboard_controller import toggle_theme as toggle_theme_func
    return toggle_theme_func()

# ============================================
#  SEGURIDAD Y BACKUP
# ============================================

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
=======
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

>>>>>>> 067b58c (modals con informacion de base de datos, usuarios conectados en tiempo real)
=======
"""
Módulo de Rutas - Sistema de Restaurante Callejón 9
Roles: 1=Admin, 2=Mesero, 3=Cocina, 4=Inventario
"""
from flask import Blueprint, render_template, session, redirect, url_for
from controllers.auth.AuthController import AuthController, login_required, rol_required, permiso_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.admin.BackupController import BackupController
from controllers.inventario.inventarioController import InventarioController
from controllers.dashboard.dashboardApiController import DashboardAPIController

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
#  API ENDPOINTS
# ============================================

# API de estadísticas del dashboard
@routes_bp.route('/api/dashboard/admin/stats')
@login_required
@rol_required(['1'])
def api_dashboard_stats():
    """API endpoint para obtener estadísticas reales del dashboard"""
    return DashboardAPIController.get_stats()

@routes_bp.route("/api/dashboard/admin/actividad")
@login_required
@rol_required(['1'])
def api_dashboard_actividad():
    """API endpoint para obtener actividad reciente"""
    return DashboardAPIController.get_actividad_reciente()

@routes_bp.route("/api/dashboard/admin/personal")
@login_required
@rol_required(['1'])
def api_dashboard_personal():
    """API endpoint para obtener personal activo"""
    return DashboardAPIController.get_personal_activo()

@routes_bp.route("/api/empleados/todos")
@login_required
@rol_required(['1'])
def api_empleados_todos():
    """API endpoint para obtener todos los empleados"""
    return DashboardAPIController.get_todos_empleados()

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
# 📦 PANEL DE INVENTARIO (Rol 4)
# ============================================

# Dashboard
@routes_bp.route("/inventario/dashboard")
@login_required
@rol_required(['1', '4'])  # Admin e Inventario
def dashboard_inventario():
    return InventarioController.dashboard()

# --- Gestión de Insumos ---
@routes_bp.route("/inventario/insumos")
@login_required
@rol_required(['1', '4'])
def inventario_insumos():
    return InventarioController.lista_insumos()

@routes_bp.route("/inventario/insumos/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_crear_insumo():
    return InventarioController.crear_insumo()

# --- Movimientos ---
@routes_bp.route("/inventario/movimientos/entrada", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_registrar_entrada():
    return InventarioController.registrar_entrada()

@routes_bp.route("/inventario/movimientos/salida", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_registrar_salida():
    return InventarioController.registrar_salida()

@routes_bp.route("/inventario/movimientos/merma", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_registrar_merma():
    return InventarioController.registrar_merma()

@routes_bp.route("/inventario/movimientos/historial")
@login_required
@rol_required(['1', '4'])
def inventario_historial():
    return InventarioController.historial_movimientos()

# --- Alertas ---
@routes_bp.route("/inventario/alertas")
@login_required
@rol_required(['1', '4'])
def inventario_alertas():
    return InventarioController.alertas_stock()

@routes_bp.route("/api/inventario/alertas/resolver", methods=["POST"])
@login_required
@rol_required(['1', '4'])
def inventario_resolver_alerta():
    return InventarioController.resolver_alerta()

# --- Proveedores ---
@routes_bp.route("/inventario/proveedores")
@login_required
@rol_required(['1', '4'])
def inventario_proveedores():
    return InventarioController.lista_proveedores()

@routes_bp.route("/inventario/proveedores/crear", methods=["GET", "POST"])
@login_required
@rol_required(['1', '4'])
def inventario_crear_proveedor():
    return InventarioController.crear_proveedor()

# --- Reportes ---
@routes_bp.route("/inventario/reportes")
@login_required
@rol_required(['1', '4'])
def inventario_reportes():
    return InventarioController.reportes()

# ============================================
# 🔒 MÓDULO DE SEGURIDAD Y BACKUP
# ============================================

# Gestión Principal de Respaldos
@routes_bp.route('/admin/backup', methods=['GET'])
@login_required
@rol_required(['1'])
def admin_backup_view():
    return BackupController.index()

# Creación de Respaldo
@routes_bp.route('/admin/backup/create', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_create():
    return BackupController.create()

# Eliminación de Archivo Físico
@routes_bp.route('/admin/backup/delete/<filename>', methods=['GET'])
@login_required
@rol_required(['1'])
def admin_backup_delete(filename):
    return BackupController.delete_file(filename)

# Restauración
@routes_bp.route('/admin/backup/restore', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_restore():
    return BackupController.restore()

# Configuración de Backup Automático
@routes_bp.route('/admin/backup/configure', methods=['POST'])
@login_required
@rol_required(['1'])
def admin_backup_configure():
    return BackupController.configure_auto_backup()