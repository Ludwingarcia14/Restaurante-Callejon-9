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
from flask import jsonify, request
from models.mesa_model import Mesa
from models.comanda_model import Comanda
from models.producto_model import Producto
from config.db import db
routes_bp = Blueprint("routes", __name__)
def api_auth_error(message="No autorizado", code=401):
    return jsonify({
        "success": False,
        "error": message
    }), code

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

@routes_bp.route("/api/menu", methods=["GET"])
@login_required
@rol_required(['1', '2']) # Agregamos '1' para que tú como admin puedas probarlo
def api_get_menu():
    try:
        # Llamamos al modelo que consulta MongoDB
        productos = Producto.obtener_todo() 
        
        # LOG DE DEPURACIÓN: Esto saldrá en tu terminal de Python
        print(f"DEBUG: Enviando {len(productos)} productos al modal.")
        
        return jsonify({
            "success": True, 
            "menu": productos
        })
    except Exception as e:
        print(f"❌ Error en api_get_menu: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    
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

    return render_template(
        "mesero/mesero_propinas.html",
        perfil=perfil_mesero
    )


@routes_bp.route("/mesero/historial")
@login_required
@rol_required(['2'])
def mesero_historial():
    perfil_mesero = session.get("perfil_mesero")

    if not perfil_mesero:
        return redirect(url_for("routes.login"))

    return render_template(
        "mesero/mesero_historial.html",
        perfil=perfil_mesero
    )

@routes_bp.route("/api/mesero/mesas/estado", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_mesas_estado():
    try:
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return jsonify({"success": False, "error": "Sesión inválida"}), 401

        # Obtener los números de mesa asignados al mesero desde su sesión
        mesas_asignadas = perfil_mesero.get("mesas_asignadas", [])

        # Pasar la lista al modelo para que devuelva información real
        estado_mesas = Mesa.get_estado_mesas_mesero(lista_numeros=mesas_asignadas)
        
        # Opcional: Asegurar que el estado sea minúscula para el JS
        for numero in estado_mesas:
            estado_mesas[numero]["estado"] = str(estado_mesas[numero].get("estado", "")).lower().strip()

        return jsonify({
            "success": True,
            "mesas": estado_mesas # Ahora esto contiene datos reales
        })

    except Exception as e:
        print("❌ api_mesero_mesas_estado:", e)
        return jsonify({"success": False, "error": str(e)}), 500
    
@routes_bp.route("/api/mesero/mesa/<numero>", methods=["GET"])
@login_required
def api_mesero_mesa_detalle(numero):
    try:
        from bson.objectid import ObjectId
        # 1. Buscar la mesa
        mesa_doc = db.mesas.find_one({"numero": int(numero)})
        if not mesa_doc:
            return jsonify({"success": False, "error": "Mesa no encontrada"}), 404
        
        raw_id = mesa_doc.get("cuenta_activa_id")
        print(f"DEBUG: Mesa {numero} tiene cuenta_activa_id: {raw_id} (Tipo: {type(raw_id)})")

        mesa_data = {
            "numero": mesa_doc["numero"],
            "estado": mesa_doc.get("estado", "libre"),
            "comensales": mesa_doc.get("comensales", 0),
            "cuenta_activa_id": str(raw_id) if raw_id else None
        }

        comanda_data = None
        # 2. Intentar buscar la comanda con diferentes métodos de ID
        if mesa_data["estado"] == "ocupada" and raw_id:
            # Intentamos buscarlo tal cual viene (sea ObjectId o String)
            comanda = db.comandas.find_one({"_id": raw_id})
            
            # Si no lo encuentra, intentamos forzar la conversión a ObjectId
            if not comanda and isinstance(raw_id, str):
                try:
                    comanda = db.comandas.find_one({"_id": ObjectId(raw_id)})
                except:
                    pass

            if comanda:
                print(f"DEBUG: ¡Comanda encontrada! Folio: {comanda.get('folio')}")
                comanda_data = {
                    "folio": comanda.get("folio", "N/A"),
                    "total": float(comanda.get("total", 0)),
                    "items": comanda.get("items", []),
                    "num_comensales": comanda.get("num_comensales", mesa_data["comensales"])
                }
            else:
                print(f"❌ DEBUG: No se encontró la comanda en la colección 'comandas' para el ID {raw_id}")

        return jsonify({
            "success": True, 
            "mesa": mesa_data,
            "comanda": comanda_data
        })
    except Exception as e:
        print(f"❌ Error detalle mesa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@routes_bp.route("/api/mesero/estadisticas/dia", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_estadisticas_dia():
    try:
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return jsonify({"success": False, "error": "Sesión inválida"}), 401

        propinas = perfil_mesero.get("propinas", {})
        rendimiento = perfil_mesero.get("rendimiento", {})

        return jsonify({
            "success": True,
            "estadisticas": {
                "venta_dia": float(rendimiento.get("ventas_promedio_dia", 0)),
                "propinas": float(propinas.get("acumulada_dia", 0))
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@routes_bp.route("/api/mesero/comandas/activas", methods=["GET"]) # Agregamos /activas
@login_required
@rol_required(['2'])
def api_mesero_comandas_activas(): # Cambiamos nombre para claridad
    return jsonify({
        "success": True,
        "comandas": [],
        "total": 0
    })
@routes_bp.route("/api/mesero/cuenta/abrir", methods=["POST"])
@login_required
@rol_required(['2'])
def api_abrir_cuenta():
    try:
        data = request.json
        numero_mesa = data.get('numero_mesa')
        num_comensales = data.get('num_comensales')
        mesero_id = session.get("user_id")

        if not numero_mesa or not num_comensales:
            return jsonify({"success": False, "error": "Datos incompletos"}), 400

        # 1. Crear la comanda y obtener el ID (ya viene como string desde el modelo)
        from models.comanda_model import Comanda
        cuenta_id_str = Comanda.crear_comanda(numero_mesa, num_comensales, mesero_id)
        
        # 2. Convertir a ObjectId solo para la operación de guardado en la DB
        from bson.objectid import ObjectId
        from config.db import db

        db.mesas.update_one(
            {"numero": int(numero_mesa)},
            {"$set": {
                "estado": "ocupada",
                "cuenta_activa_id": ObjectId(cuenta_id_str), # Se guarda como objeto en Mongo
                "comensales": int(num_comensales)
            }}
        )

        # 3. Devolver el ID como STRING para que JSON no explote
        return jsonify({
            "success": True, 
            "cuenta_id": str(cuenta_id_str), # <--- Forzamos string aquí
            "message": "Cuenta abierta correctamente"
        })
    except Exception as e:
        print(f"❌ Error api_abrir_cuenta: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    
@routes_bp.route("/api/mesero/comanda/<cuenta_id>/items", methods=["POST"])
@login_required
@rol_required(['2'])
def api_guardar_items_comanda(cuenta_id):
    try:
        items = request.json.get('items', [])
        if not items:
            return jsonify({"success": False, "error": "Pedido vacío"}), 400

        Comanda.agregar_items(cuenta_id, items)
        return jsonify({"success": True, "message": "Pedido enviado a cocina"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@routes_bp.route("/mesero/comanda/<cuenta_id>/agregar")
@login_required
@rol_required(['2'])
def vista_agregar_items(cuenta_id):
    perfil_mesero = session.get("perfil_mesero")
    return render_template(
        "mesero/mesero_menu.html", # Reutilizas tu plantilla de menú
        perfil=perfil_mesero,
        cuenta_id=cuenta_id # Pasas el ID para que el JS sepa a dónde guardar
    )
    from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Comanda:
    @staticmethod
    def _collection():
        return db["comandas"]

    @classmethod
    def crear_comanda(cls, numero_mesa, num_comensales, mesero_id):
        nueva_comanda = {
            "mesa_numero": int(numero_mesa),
            "num_comensales": int(num_comensales),
            "mesero_id": str(mesero_id),
            "estado": "nueva", # nueva, enviada, lista, pagada
            "items": [],
            "total": 0.0,
            "fecha_apertura": datetime.utcnow(),
            "folio": f"COM-{datetime.now().strftime('%y%m%d%H%M%S')}"
        }
        res = cls._collection().insert_one(nueva_comanda)
        return str(res.inserted_id)

    @classmethod
    def agregar_items(cls, cuenta_id, lista_items):
        total = sum(item['precio'] * item['cantidad'] for item in lista_items)
        cls._collection().update_one(
            {"_id": ObjectId(cuenta_id)},
            {
                "$set": {
                    "items": lista_items,
                    "total": total,
                    "estado": "enviada"
                }
            }
        )
        return True
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

"""
Rutas del Módulo de Inventario
Agregar estas rutas al archivo routes.py principal
"""

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