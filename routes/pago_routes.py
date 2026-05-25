from flask import request, jsonify
from controllers.auth.AuthController import login_required, rol_required
from controllers.pago.mercadoPagoController import MercadoPagoController


def register_pago_routes(bp):

    @bp.route("/api/pago/crear/<cuenta_id>", methods=["POST"])
    @login_required
    @rol_required(['2'])
    def crear_pago(cuenta_id):
        from bson import ObjectId
        return MercadoPagoController.crear_preferencia(ObjectId(cuenta_id))

    @bp.route("/pago/exitoso")
    def pago_exitoso():
        return MercadoPagoController.procesar_pago_exitoso()

    @bp.route("/pago/fallido")
    def pago_fallido():
        return MercadoPagoController.procesar_pago_fallido()

    @bp.route("/pago/pendiente")
    def pago_pendiente():
        return MercadoPagoController.procesar_pago_pendiente()

    @bp.route("/api/webhook/mercadopago", methods=["POST"])
    def webhook_mercadopago():
        return MercadoPagoController.webhook()

    @bp.route("/api/pago/verificar", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def verificar_pago():
        cuenta_id = request.args.get("cuenta_id")
        if not cuenta_id:
            return jsonify({"success": False, "error": "Falta cuenta_id"}), 400
        return MercadoPagoController.verificar_pago_mercadopago(cuenta_id)
