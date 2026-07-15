from . import routes_bp
from flask import session, redirect, url_for
from controllers.auth.AuthController import login_required, rol_required
from controllers.repartidor.repartidor_controller import (
    RepartidorViewController,
    AdminDeliveryViewController,
    DeliveryAPIController,
    RepartidorAPIController,
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
