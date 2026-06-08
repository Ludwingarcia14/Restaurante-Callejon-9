"""
API v1 — Blueprint para la app móvil.
Prefijo: /api/v1
Todos los endpoints usan JWT (Bearer token), no sesiones de Flask.
"""
from flask import Blueprint, jsonify
from extensions import limiter
from utils.jwt_utils import jwt_required, jwt_rol_required

# Controllers — Auth empleados (Fase 1)
from controllers.api.v1.auth_mobile_controller import AuthMobileController

# Controllers — Clientes (Fase 2)
from controllers.api.v1.cliente_auth_controller import ClienteAuthController
from controllers.api.v1.cliente_perfil_controller import ClientePerfilController

# Controllers — QR, Menú, Pedidos (Fase 3)
from controllers.api.v1.mesa_movil_controller import MesaMovilController
from controllers.api.v1.menu_movil_controller import MenuMovilController
from controllers.api.v1.pedido_movil_controller import PedidoMovilController

# Controllers — Cuenta y Pagos (Fase 4)
from controllers.api.v1.cuenta_movil_controller import CuentaMovilController
from controllers.api.v1.pago_movil_controller import PagoMovilController

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


# ============================================================
# HEALTH CHECK
# ============================================================
@api_v1_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0"}), 200


# ============================================================
# AUTH — EMPLEADOS  (Fase 1)
# ============================================================
_empleado_login = limiter.limit("10 per minute")(AuthMobileController.login)

@api_v1_bp.route("/auth/empleados/login", methods=["POST"])
def empleado_login():
    return _empleado_login()

@api_v1_bp.route("/auth/empleados/refresh", methods=["POST"])
def empleado_refresh():
    return AuthMobileController.refresh()


# ============================================================
# AUTH — CLIENTES  (Fase 2)
# ============================================================
_cliente_login    = limiter.limit("10 per minute")(ClienteAuthController.login)
_cliente_registro = limiter.limit("5 per minute")(ClienteAuthController.registro)

@api_v1_bp.route("/clientes/registro", methods=["POST"])
def cliente_registro():
    return _cliente_registro()

@api_v1_bp.route("/clientes/login", methods=["POST"])
def cliente_login():
    return _cliente_login()

@api_v1_bp.route("/clientes/refresh", methods=["POST"])
def cliente_refresh():
    return ClienteAuthController.refresh()

@api_v1_bp.route("/clientes/logout", methods=["POST"])
@jwt_required
def cliente_logout():
    return ClienteAuthController.logout()


# ============================================================
# PERFIL — CLIENTES  (Fase 2)
# ============================================================
@api_v1_bp.route("/clientes/perfil", methods=["GET"])
@jwt_required
def cliente_get_perfil():
    return ClientePerfilController.get_perfil()

@api_v1_bp.route("/clientes/perfil", methods=["PATCH"])
@jwt_required
def cliente_actualizar_perfil():
    return ClientePerfilController.actualizar_perfil()

@api_v1_bp.route("/clientes/perfil/foto", methods=["PATCH"])
@jwt_required
def cliente_actualizar_foto():
    return ClientePerfilController.actualizar_foto()

@api_v1_bp.route("/clientes/perfil/password", methods=["PATCH"])
@jwt_required
def cliente_cambiar_password():
    return ClientePerfilController.cambiar_password()


# ============================================================
# MESAS — QR  (Fase 3)
# ============================================================
@api_v1_bp.route("/mesas/escanear/<string:codigo_qr>", methods=["GET"])
def mesa_escanear_qr(codigo_qr):
    """Escanea el QR de una mesa. Sin auth requerida."""
    return MesaMovilController.escanear_qr(codigo_qr)


# ============================================================
# MENÚ  (Fase 3)
# ============================================================
@api_v1_bp.route("/menu", methods=["GET"])
def menu_listar():
    """Lista el menú disponible. Sin auth requerida."""
    return MenuMovilController.get_menu()

@api_v1_bp.route("/menu/categorias", methods=["GET"])
def menu_categorias():
    """Lista las categorías activas del menú."""
    return MenuMovilController.get_categorias()

@api_v1_bp.route("/menu/<string:platillo_id>", methods=["GET"])
def menu_detalle(platillo_id):
    """Detalle de un platillo."""
    return MenuMovilController.get_platillo(platillo_id)


# ============================================================
# PEDIDOS — CLIENTES  (Fase 3)
# ============================================================
@api_v1_bp.route("/pedidos", methods=["POST"])
@jwt_required
def pedido_crear():
    """Realiza un pedido desde la mesa."""
    return PedidoMovilController.crear_pedido()

@api_v1_bp.route("/pedidos/activo", methods=["GET"])
@jwt_required
def pedido_activo():
    """Pedido activo del cliente (el más reciente no finalizado)."""
    return PedidoMovilController.get_pedido_activo()

@api_v1_bp.route("/pedidos/<string:pedido_id>", methods=["GET"])
@jwt_required
def pedido_detalle(pedido_id):
    """Detalle y estado de un pedido específico."""
    return PedidoMovilController.get_pedido(pedido_id)


# ============================================================
# ADMIN / COCINA — PEDIDOS MÓVILES  (Fase 3)
# Solo roles 1=Admin y 3=Cocina
# ============================================================
@api_v1_bp.route("/admin/pedidos-movil", methods=["GET"])
@jwt_rol_required(["1", "3"])
def admin_pedidos_movil_listar():
    """Lista pedidos móviles activos para la vista de cocina."""
    return PedidoMovilController.listar_para_cocina()

@api_v1_bp.route("/admin/pedidos-movil/<string:pedido_id>/estado", methods=["PATCH"])
@jwt_rol_required(["1", "3"])
def admin_pedido_actualizar_estado(pedido_id):
    """Actualiza el estado de un pedido móvil (cocina/admin)."""
    return PedidoMovilController.actualizar_estado(pedido_id)

@api_v1_bp.route("/admin/mesas/qr-tokens", methods=["GET"])
@jwt_rol_required(["1"])
def admin_mesas_qr_tokens():
    """Lista los tokens QR de todas las mesas."""
    return MesaMovilController.listar_qr_mesas()

@api_v1_bp.route("/admin/mesas/<string:numero>/qr", methods=["GET"])
@jwt_rol_required(["1"])
def admin_mesa_qr_imagen(numero):
    """Descarga la imagen PNG del QR de una mesa."""
    return MesaMovilController.generar_imagen_qr(numero)


# ============================================================
# CUENTA  (Fase 4)
# ============================================================
@api_v1_bp.route("/cuenta/<string:pedido_id>", methods=["GET"])
@jwt_required
def cuenta_ver(pedido_id):
    """Desglose de la cuenta con propina y estado de pago."""
    return CuentaMovilController.get_cuenta(pedido_id)

@api_v1_bp.route("/cuenta/<string:pedido_id>/solicitar", methods=["POST"])
@jwt_required
def cuenta_solicitar(pedido_id):
    """Notifica al mesero que el cliente quiere pagar."""
    return CuentaMovilController.solicitar_cuenta(pedido_id)

@api_v1_bp.route("/cuenta/<string:pedido_id>/dividir", methods=["POST"])
@jwt_required
def cuenta_dividir(pedido_id):
    """Calcula la división de la cuenta entre comensales."""
    return CuentaMovilController.dividir_cuenta(pedido_id)


# ============================================================
# PAGOS  (Fase 4)
# ============================================================
@api_v1_bp.route("/pagos", methods=["POST"])
@jwt_required
def pago_crear():
    """Crea preferencia de MercadoPago para el pedido o una parte de él."""
    return PagoMovilController.crear_preferencia()

@api_v1_bp.route("/pagos/<string:pago_id>/estado", methods=["GET"])
@jwt_required
def pago_estado(pago_id):
    """Verifica el estado del pago en MercadoPago (polling)."""
    return PagoMovilController.verificar_estado(pago_id)

@api_v1_bp.route("/pagos/resultado", methods=["GET"])
def pago_resultado():
    """Back URL de MercadoPago tras el checkout (sin auth)."""
    return PagoMovilController.resultado_redireccion()


# ============================================================
# FUTURAS RUTAS
# ============================================================
# Fase 5: GET  /clientes/historial
#         GET  /clientes/puntos
#         GET  /promociones
