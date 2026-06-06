from . import routes_bp
from flask import session, redirect, url_for, request, jsonify
from controllers.auth.AuthController import login_required, rol_required
from controllers.pago.mercadoPagoController import MercadoPagoController

@routes_bp.route("/api/pago/crear/<cuenta_id>", methods=["POST"])
@login_required
@rol_required(['2'])
def crear_pago(cuenta_id):
    from bson import ObjectId
    return MercadoPagoController.crear_preferencia(ObjectId(cuenta_id))

@routes_bp.route("/pago/exitoso")
def pago_exitoso():
    if "usuario_rol" not in session:
        return redirect(url_for("routes.login"))
    return MercadoPagoController.procesar_pago_exitoso()

@routes_bp.route("/pago/fallido")
def pago_fallido():
    if "usuario_rol" not in session:
        return redirect(url_for("routes.login"))
    return MercadoPagoController.procesar_pago_fallido()

@routes_bp.route("/pago/pendiente")
def pago_pendiente():
    if "usuario_rol" not in session:
        return redirect(url_for("routes.login"))
    return MercadoPagoController.procesar_pago_pendiente()

@routes_bp.route("/api/webhook/mercadopago", methods=["POST"])
def webhook_mercadopago():
    return MercadoPagoController.webhook()

@routes_bp.route("/api/pago/verificar", methods=["GET"])
@login_required
@rol_required(['2'])
def verificar_pago():
    cuenta_id = request.args.get("cuenta_id")
    if not cuenta_id:
        return jsonify({"success": False, "error": "Falta cuenta_id"}), 400
    return MercadoPagoController.verificar_pago_mercadopago(cuenta_id)
