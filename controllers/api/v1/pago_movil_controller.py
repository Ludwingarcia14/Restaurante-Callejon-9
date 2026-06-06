"""
Pagos desde la app móvil via MercadoPago.
Soporta pago completo o pago de una parte (división de cuenta).
"""
import os
import logging
import mercadopago

from flask import request, jsonify
from models.pedido_movil_model import PedidoMovil
from models.pago_movil_model import PagoMovil

logger = logging.getLogger(__name__)

_PROPINA_PERMITIDAS = {0, 10, 15, 20}
_NGROK_URL = os.getenv("NGROK_URL", "http://localhost:5000")


def _get_sdk():
    token = os.getenv("MP_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("MP_ACCESS_TOKEN no configurado")
    return mercadopago.SDK(token)


class PagoMovilController:

    # ----------------------------------------------------------
    # CREAR PREFERENCIA DE MERCADOPAGO
    # ----------------------------------------------------------
    @staticmethod
    def crear_preferencia():
        """
        POST /api/v1/pagos
        Body: {
            pedido_id: str,
            propina_porcentaje: 0|10|15|20,   (default 0)
            division_parte: int,               (default 0 = pago completo)
            monto_parte: float                 (requerido si division_parte > 0)
        }
        Devuelve {pago_id, init_point, preference_id, total_final}.
        """
        cliente_id = request.jwt_payload["sub"]
        data = request.get_json(silent=True) or {}

        pedido_id = data.get("pedido_id", "")
        if not pedido_id:
            return jsonify({"status": "error", "message": "pedido_id es requerido"}), 400

        doc = PedidoMovil.find_by_id(pedido_id)
        if not doc:
            return jsonify({"status": "error", "message": "Pedido no encontrado"}), 404
        if doc.get("cliente_id") != cliente_id:
            return jsonify({"status": "error", "message": "Sin permisos"}), 403
        if doc.get("estado") in ("entregado", "cancelado"):
            return jsonify({"status": "error", "message": "El pedido ya está cerrado"}), 400

        # Propina
        try:
            propina_pct = int(data.get("propina_porcentaje", 0))
        except (ValueError, TypeError):
            propina_pct = 0
        if propina_pct not in _PROPINA_PERMITIDAS:
            return jsonify({"status": "error", "message": f"propina_porcentaje debe ser 0, 10, 15 ó 20"}), 400

        # División
        try:
            division_parte = int(data.get("division_parte", 0))
        except (ValueError, TypeError):
            division_parte = 0

        if division_parte > 0:
            # Pago de una parte específica — el monto ya fue calculado en /dividir
            try:
                monto_base = round(float(data.get("monto_parte", 0)), 2)
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": "monto_parte inválido para pago de parte"}), 400
            if monto_base <= 0:
                return jsonify({"status": "error", "message": "monto_parte debe ser mayor a 0"}), 400
            subtotal    = monto_base
            num_partes  = int(data.get("num_partes", 1))
        else:
            # Pago completo
            subtotal   = round(doc.get("total", 0.0), 2)
            num_partes = 1

        propina_monto = round(subtotal * propina_pct / 100, 2)
        total_final   = round(subtotal + propina_monto, 2)

        if total_final <= 0:
            return jsonify({"status": "error", "message": "El total debe ser mayor a 0"}), 400

        # Crear registro de pago
        try:
            pago_id = PagoMovil.crear(
                pedido_id=pedido_id,
                cliente_id=cliente_id,
                monto=subtotal,
                propina_monto=propina_monto,
                propina_porcentaje=propina_pct,
                total_final=total_final,
                division_parte=division_parte,
                num_partes=num_partes,
            )
        except Exception as e:
            logger.error("Error creando PagoMovil: %s", e)
            return jsonify({"status": "error", "message": "Error al iniciar el pago"}), 500

        # Crear preferencia en MercadoPago
        folio       = doc.get("folio", pedido_id)
        mesa_numero = doc.get("mesa_numero", "?")
        parte_label = f" (Parte {division_parte}/{num_partes})" if division_parte > 0 else ""

        preference_data = {
            "items": [
                {
                    "title":       f"Mesa {mesa_numero} — {folio}{parte_label}",
                    "description": (
                        f"Consumo: ${subtotal:.2f}"
                        + (f" + Propina {propina_pct}%: ${propina_monto:.2f}" if propina_monto > 0 else "")
                    ),
                    "quantity":    1,
                    "currency_id": "MXN",
                    "unit_price":  total_final,
                }
            ],
            "external_reference": f"MOVIL_{pago_id}",
            "statement_descriptor": "RESTAURANTE",
            "back_urls": {
                "success": f"{_NGROK_URL}/api/v1/pagos/resultado?estado=aprobado&pago_id={pago_id}",
                "failure": f"{_NGROK_URL}/api/v1/pagos/resultado?estado=rechazado&pago_id={pago_id}",
                "pending": f"{_NGROK_URL}/api/v1/pagos/resultado?estado=pendiente&pago_id={pago_id}",
            },
            "notification_url": f"{_NGROK_URL}/api/webhook/mercadopago",
        }

        try:
            sdk = _get_sdk()
            result = sdk.preference().create(preference_data)
        except Exception as e:
            logger.error("Error al llamar a MercadoPago: %s", e)
            return jsonify({"status": "error", "message": "Error al conectar con MercadoPago"}), 502

        if result["status"] not in (200, 201):
            msg = result.get("response", {}).get("message", "Error en MercadoPago")
            return jsonify({"status": "error", "message": msg}), 400

        preference  = result["response"]
        preference_id = preference.get("id")
        # En sandbox se usa sandbox_init_point; en producción, init_point
        init_point  = preference.get("sandbox_init_point") or preference.get("init_point")

        PagoMovil.set_preferencia(pago_id, preference_id)

        return jsonify({
            "status":        "success",
            "pago_id":       pago_id,
            "preference_id": preference_id,
            "init_point":    init_point,
            "monto":         subtotal,
            "propina":       propina_monto,
            "total_final":   total_final,
        }), 201

    # ----------------------------------------------------------
    # VERIFICAR ESTADO DEL PAGO (polling)
    # ----------------------------------------------------------
    @staticmethod
    def verificar_estado(pago_id: str):
        """
        GET /api/v1/pagos/<pago_id>/estado
        Consulta el estado del pago directamente en MercadoPago.
        """
        cliente_id = request.jwt_payload["sub"]
        doc = PagoMovil.find_by_id(pago_id)

        if not doc:
            return jsonify({"status": "error", "message": "Pago no encontrado"}), 404
        if doc.get("cliente_id") != cliente_id:
            return jsonify({"status": "error", "message": "Sin permisos"}), 403

        # Si ya está registrado como aprobado, devolver directamente
        if doc.get("estado") == "aprobado":
            return jsonify({
                "status": "success",
                "pago": PagoMovil.to_public(doc),
                "mp_estado": "approved",
            }), 200

        preference_id = doc.get("mp_preference_id")
        if not preference_id:
            return jsonify({
                "status": "success",
                "pago": PagoMovil.to_public(doc),
                "mp_estado": "sin_preferencia",
            }), 200

        # Consultar en MercadoPago
        try:
            sdk = _get_sdk()
            search = sdk.payment().search(
                filters={"external_reference": f"MOVIL_{pago_id}"}
            )
        except Exception as e:
            logger.error("Error consultando MP: %s", e)
            return jsonify({"status": "error", "message": "Error al consultar MercadoPago"}), 502

        mp_estado = "pending"
        if search["status"] == 200:
            results = search["response"].get("results", [])
            if results:
                pago_mp = results[0]
                mp_estado   = pago_mp.get("status", "pending")
                mp_pago_id  = str(pago_mp.get("id", ""))

                if mp_estado == "approved":
                    PagoMovil.set_aprobado(pago_id, mp_pago_id)
                    _notificar_pago_aprobado(doc)
                elif mp_estado in ("rejected", "cancelled"):
                    PagoMovil.set_rechazado(pago_id)

        doc = PagoMovil.find_by_id(pago_id)
        return jsonify({
            "status":   "success",
            "pago":     PagoMovil.to_public(doc),
            "mp_estado": mp_estado,
        }), 200

    # ----------------------------------------------------------
    # RESULTADO DESPUÉS DE REDIRECCION (back_url)
    # ----------------------------------------------------------
    @staticmethod
    def resultado_redireccion():
        """
        GET /api/v1/pagos/resultado
        MercadoPago redirige aquí después del checkout.
        La app móvil puede abrir este URL en un WebView y detectar la URL.
        """
        from flask import request as req
        estado  = req.args.get("estado", "pendiente")
        pago_id = req.args.get("pago_id", "")

        return jsonify({
            "status":   "success",
            "estado":   estado,
            "pago_id":  pago_id,
            "message":  f"Pago {estado}. Cierra esta ventana y regresa a la app.",
        }), 200


def _notificar_pago_aprobado(pago_doc: dict):
    """Emite a la sala del cliente y a la sala de meseros cuando se aprueba el pago."""
    try:
        from extensions import socketio
        from datetime import datetime
        payload = {
            "pedido_id":  pago_doc.get("pedido_id"),
            "pago_id":    str(pago_doc["_id"]),
            "total_final": pago_doc.get("total_final"),
            "timestamp":  datetime.utcnow().isoformat(),
        }
        socketio.emit("pago_aprobado", payload,
                      room=f"cliente_{pago_doc.get('cliente_id')}", namespace="/")
        socketio.emit("pago_aprobado_movil", payload,
                      room="meseros", namespace="/")
    except Exception as e:
        logger.warning("No se pudo emitir pago_aprobado: %s", e)
