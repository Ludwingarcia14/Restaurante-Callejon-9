"""
Módulo de Rutas - Sistema de Restaurante Callejón 9
Roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import Blueprint, render_template, session, redirect, url_for
from flask import render_template, session, redirect, url_for, jsonify
from controllers.auth.AuthController import AuthController, login_required, rol_required, permiso_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.admin.BackupController import BackupController
from controllers.inventario.inventarioController import InventarioController
from controllers.dashboard.dashboardApiController import DashboardAPIController
from controllers.comanda.comandaController import ComandaController
from controllers.mesa.mesaController import MesaController
from flask import jsonify, request
from models.mesa_model import Mesa
from models.comanda_model import Comanda
from models.producto_model import Producto
from config.db import db

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
#  API NOTIFICACIONES
# ============================================

# Obtener datos del usuario para Socket.IO
@routes_bp.route('/api/me', methods=['GET'])
@login_required
def api_me():
    """Endpoint para obtener datos del usuario autenticado y token de socket"""
    return NotificacionController.get_datos_socket()

# Obtener todas las notificaciones
@routes_bp.route('/api/notificaciones', methods=['GET'])
@login_required
def api_notificaciones():
    """Obtiene todas las notificaciones del usuario"""
    return NotificacionController.get_notificaciones()

# Obtener solo notificaciones no leídas
@routes_bp.route('/api/notificaciones/no-leidas', methods=['GET'])
@login_required
def api_notificaciones_no_leidas():
    """Obtiene notificaciones no leídas"""
    return NotificacionController.get_notificaciones_no_leidas()

# Contador de notificaciones no leídas
@routes_bp.route('/api/notificaciones/contador', methods=['GET'])
@login_required
def api_notificaciones_contador():
    """Obtiene el número de notificaciones no leídas"""
    return NotificacionController.get_contador()

# Marcar una notificación como leída
@routes_bp.route('/api/notificaciones/<id_notificacion>/leida', methods=['PUT'])
@login_required
def api_notificacion_leida(id_notificacion):
    """Marca una notificación específica como leída"""
    return NotificacionController.marcar_leida(id_notificacion)

# Marcar todas como leídas
@routes_bp.route('/api/notificaciones/marcar-todas-leidas', methods=['POST'])
@login_required
def api_marcar_todas_leidas():
    """Marca todas las notificaciones del usuario como leídas"""
    return NotificacionController.marcar_todas_leidas()

# Eliminar notificación
@routes_bp.route('/api/notificaciones/<id_notificacion>', methods=['DELETE'])
@login_required
def api_eliminar_notificacion(id_notificacion):
    """Elimina una notificación específica"""
    return NotificacionController.eliminar_notificacion(id_notificacion)

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
    return DashboardController.mesero()

@routes_bp.route("/mesero/mesas")
@login_required
@rol_required(['2'])
def mesero_mesas():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))

    stats = {
        "mesas_asignadas": perfil_mesero.get("mesas_asignadas", []),
        "comandas_activas": 0,
        "propinas_dia": perfil_mesero.get("propinas", {}).get("acumulada_dia", 0)
    }

    return render_template(
        "mesero/dashboard.html",
        perfil=perfil_mesero,
        stats=stats
    )

@routes_bp.route("/mesero/comandas")
@login_required
@rol_required(['2'])
def mesero_comandas():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))

    return render_template(
        "mesero/comandas.html",
        perfil=perfil_mesero,
        stats={"mesas_asignadas": perfil_mesero.get("mesas_asignadas", [])}
    )


@routes_bp.route("/mesero/menu")
@login_required
@rol_required(['2'])
def mesero_menu():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))

    return render_template(
        "mesero/mesero_menu.html",
        perfil=perfil_mesero,
        stats={"mesas_asignadas": perfil_mesero.get("mesas_asignadas", [])}
    )


@routes_bp.route("/mesero/propinas")
@login_required
@rol_required(['2'])
def mesero_propinas():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))

    return render_template("mesero/mesero_propinas.html", perfil=perfil_mesero)


@routes_bp.route("/mesero/historial")
@login_required
@rol_required(['2'])
def mesero_historial():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))

    return render_template("mesero/mesero_historial.html", perfil=perfil_mesero)


@routes_bp.route("/mesero/comanda/<cuenta_id>/agregar")
@login_required
@rol_required(['2'])
def vista_agregar_items(cuenta_id):
    return ComandaController.vista_agregar_items(cuenta_id)

# =========================
# API GENERALES
# =========================

@routes_bp.route("/api/menu", methods=["GET"])
@login_required
@rol_required(['1', '2'])
def api_get_menu():
    productos = Producto.obtener_todo()
    return jsonify({"success": True, "menu": productos})


@routes_bp.route("/api/mesero/estadisticas/dia", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_estadisticas_dia():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return jsonify({"success": False, "error": "Sesión inválida"}), 401

    return jsonify({
        "success": True,
        "estadisticas": {
            "venta_dia": float(perfil_mesero.get("rendimiento", {}).get("ventas_promedio_dia", 0)),
            "propinas": float(perfil_mesero.get("propinas", {}).get("acumulada_dia", 0))
        }
    })

# =========================
# API MESAS
# =========================

@routes_bp.route("/api/mesero/mesas/estado", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_mesas_estado():
    return MesaController.estado_mesas_mesero()


@routes_bp.route("/api/mesero/mesa/<numero>", methods=["GET"])
@login_required
def api_mesero_mesa_detalle(numero):
    return MesaController.detalle_mesa(numero)

# =========================
# API COMANDAS
# =========================

@routes_bp.route("/api/mesero/comandas/activas", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_comandas_activas():
    return ComandaController.comandas_activas()

@routes_bp.route("/api/mesero/cuenta/abrir", methods=["POST"])
@login_required
@rol_required(['2'])
def api_abrir_cuenta():
    return ComandaController.abrir_cuenta()

@routes_bp.route("/api/mesero/comanda/<cuenta_id>/items", methods=["POST"])
@login_required
@rol_required(['2'])
def api_guardar_items_comanda(cuenta_id):
    return ComandaController.guardar_items(cuenta_id)
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