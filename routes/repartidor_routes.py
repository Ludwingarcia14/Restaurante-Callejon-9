from . import routes_bp
from flask import session, redirect, url_for
from controllers.auth.AuthController import login_required, rol_required
from controllers.repartidor.repartidor_controller import (
    RepartidorViewController,
    AdminDeliveryViewController,
    DeliveryAPIController,
    RepartidorAPIController,
    SensorViewController,
    SensorAPIController,
    AdminMonitorController,
    TrackingController,
)

# ── Vistas Repartidor (Rol 5) ────────────────────────────────
@routes_bp.route("/repartidor/dashboard")
@login_required
@rol_required(['5'])
def dashboard_repartidor():
    return RepartidorViewController.dashboard()

@routes_bp.route("/repartidor/entregas")
@login_required
@rol_required(['5'])
def repartidor_entregas():
    return RepartidorViewController.mis_entregas()

@routes_bp.route("/repartidor/historial")
@login_required
@rol_required(['5'])
def repartidor_historial():
    return RepartidorViewController.historial()

# ── Vistas Admin (Rol 1) ─────────────────────────────────────
@routes_bp.route("/admin/delivery")
@login_required
@rol_required(['1'])
def admin_delivery_panel():
    return AdminDeliveryViewController.panel()

@routes_bp.route("/admin/repartidores")
@login_required
@rol_required(['1'])
def admin_repartidores():
    return AdminDeliveryViewController.gestion_repartidores()

# ── API Deliveries ────────────────────────────────────────────
@routes_bp.route("/api/delivery/crear", methods=["POST"])
@login_required
@rol_required(['1', '2'])
def api_delivery_crear():
    return DeliveryAPIController.crear()

@routes_bp.route("/api/delivery/<delivery_id>/asignar", methods=["PUT"])
@login_required
@rol_required(['1', '2'])
def api_delivery_asignar(delivery_id):
    return DeliveryAPIController.asignar(delivery_id)

@routes_bp.route("/api/delivery/<delivery_id>/estado", methods=["PUT"])
@login_required
@rol_required(['1', '2', '5'])
def api_delivery_estado(delivery_id):
    return DeliveryAPIController.actualizar_estado(delivery_id)

@routes_bp.route("/api/delivery/pendientes")
@login_required
@rol_required(['1', '2'])
def api_delivery_pendientes():
    return DeliveryAPIController.listar_pendientes()

# ── Nuevo flujo: repartidor acepta pedidos por sí mismo ───────
@routes_bp.route("/api/delivery/disponibles")
@login_required
@rol_required(['5'])
def api_delivery_disponibles():
    return DeliveryAPIController.listar_disponibles_api()

@routes_bp.route("/api/delivery/<delivery_id>/aceptar", methods=["POST"])
@login_required
@rol_required(['5'])
def api_delivery_aceptar(delivery_id):
    return DeliveryAPIController.aceptar(delivery_id)

@routes_bp.route("/api/delivery/mis-entregas")
@login_required
@rol_required(['5'])
def api_mis_entregas():
    return DeliveryAPIController.mis_entregas_api()

@routes_bp.route("/api/delivery/historial")
@login_required
@rol_required(['1', '5'])
def api_delivery_historial():
    return DeliveryAPIController.historial_api()

# ── API Repartidores (CRUD admin) ─────────────────────────────
@routes_bp.route("/api/repartidores")
@login_required
@rol_required(['1', '2'])
def api_repartidores_listar():
    return RepartidorAPIController.listar()

@routes_bp.route("/api/repartidores/crear", methods=["POST"])
@login_required
@rol_required(['1'])
def api_repartidores_crear():
    return RepartidorAPIController.crear()

@routes_bp.route("/api/repartidores/<uid>", methods=["PUT"])
@login_required
@rol_required(['1'])
def api_repartidores_actualizar(uid):
    return RepartidorAPIController.actualizar(uid)

@routes_bp.route("/api/repartidores/<uid>", methods=["DELETE"])
@login_required
@rol_required(['1'])
def api_repartidores_eliminar(uid):
    return RepartidorAPIController.eliminar(uid)

# ── Wearable: Sensor screen (Rol 5) ──────────────────────────
@routes_bp.route("/repartidor/sensores")
@login_required
@rol_required(['5'])
def repartidor_sensores():
    return SensorViewController.mis_sensores()

# ── API Sensores (Rol 5 envía, Rol 1 consulta) ───────────────
@routes_bp.route("/api/sensor/enviar", methods=["POST"])
@login_required
@rol_required(['5'])
def api_sensor_enviar():
    return SensorAPIController.recibir()

@routes_bp.route("/api/sensor/todos")
@login_required
@rol_required(['1'])
def api_sensor_todos():
    return SensorAPIController.api_todos()

# ── Admin: Monitor tiempo real ────────────────────────────────
@routes_bp.route("/admin/monitor")
@login_required
@rol_required(['1'])
def admin_monitor_sensores():
    return AdminMonitorController.monitor()

@routes_bp.route("/admin/eventos")
@login_required
@rol_required(['1'])
def admin_eventos_historial():
    return AdminMonitorController.eventos()

@routes_bp.route("/admin/notificar")
@login_required
@rol_required(['1'])
def admin_notificar_vista():
    return AdminMonitorController.notificar_vista()

@routes_bp.route("/api/admin/notificar", methods=["POST"])
@login_required
@rol_required(['1'])
def api_admin_notificar():
    return AdminMonitorController.notificar_enviar()

# ── Tracking público (sin auth) ───────────────────────────────
@routes_bp.route("/seguimiento/<folio>")
def seguimiento_pedido(folio):
    return TrackingController.seguimiento(folio)
