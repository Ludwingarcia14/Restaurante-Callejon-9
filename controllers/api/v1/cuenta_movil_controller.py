"""
Ver la cuenta del pedido, solicitar que el mesero venga a cobrar,
y calcular la división entre comensales.
"""
import logging
from flask import request, jsonify
from models.pedido_movil_model import PedidoMovil
from models.pago_movil_model import PagoMovil
from models.mesa_model import Mesa

logger = logging.getLogger(__name__)

_PROPINA_OPCIONES = {0: 0, 10: 10, 15: 15, 20: 20}


def _calcular_propina(total: float, porcentaje: int) -> float:
    return round(total * porcentaje / 100, 2)


class CuentaMovilController:

    # ----------------------------------------------------------
    # VER CUENTA (total en tiempo real)
    # ----------------------------------------------------------
    @staticmethod
    def get_cuenta(pedido_id: str):
        """
        GET /api/v1/cuenta/<pedido_id>
        Devuelve el desglose de la cuenta con opciones de propina.
        """
        cliente_id = request.jwt_payload["sub"]
        doc = PedidoMovil.find_by_id(pedido_id)

        if not doc:
            return jsonify({"status": "error", "message": "Pedido no encontrado"}), 404
        if doc.get("cliente_id") != cliente_id:
            return jsonify({"status": "error", "message": "Sin permisos"}), 403

        subtotal = round(doc.get("total", 0.0), 2)

        # Pagos ya realizados para este pedido
        pagos = PagoMovil.find_by_pedido(pedido_id)
        monto_pagado = round(
            sum(p.get("total_final", 0) for p in pagos if p.get("estado") == "aprobado"), 2
        )
        todo_pagado = PagoMovil.todos_aprobados(pedido_id) if pagos else False

        return jsonify({
            "status": "success",
            "data": {
                "pedido_id":    pedido_id,
                "folio":        doc.get("folio"),
                "mesa_numero":  doc.get("mesa_numero"),
                "estado_pedido": doc.get("estado"),
                "items":        doc.get("items", []),
                "subtotal":     subtotal,
                "propina_opciones": {
                    str(p): round(subtotal * p / 100, 2)
                    for p in [0, 10, 15, 20]
                },
                "totales_con_propina": {
                    str(p): round(subtotal + subtotal * p / 100, 2)
                    for p in [0, 10, 15, 20]
                },
                "monto_pagado": monto_pagado,
                "todo_pagado":  todo_pagado,
                "pagos":        [PagoMovil.to_public(p) for p in pagos],
            },
        }), 200

    # ----------------------------------------------------------
    # SOLICITAR LA CUENTA (notificar al mesero)
    # ----------------------------------------------------------
    @staticmethod
    def solicitar_cuenta(pedido_id: str):
        """
        POST /api/v1/cuenta/<pedido_id>/solicitar
        Emite un evento Socket.IO al mesero de la mesa para que venga a cobrar.
        """
        cliente_id = request.jwt_payload["sub"]
        doc = PedidoMovil.find_by_id(pedido_id)

        if not doc:
            return jsonify({"status": "error", "message": "Pedido no encontrado"}), 404
        if doc.get("cliente_id") != cliente_id:
            return jsonify({"status": "error", "message": "Sin permisos"}), 403

        mesa_numero = doc.get("mesa_numero")

        # Notificar al mesero de la mesa
        try:
            from extensions import socketio
            from datetime import datetime
            socketio.emit(
                "solicitud_cuenta",
                {
                    "pedido_id":   pedido_id,
                    "folio":       doc.get("folio"),
                    "mesa":        mesa_numero,
                    "total":       doc.get("total"),
                    "timestamp":   datetime.utcnow().isoformat(),
                    "origen":      "movil",
                },
                room="meseros",
                namespace="/",
            )
        except Exception as e:
            logger.warning("No se pudo emitir solicitud_cuenta: %s", e)

        return jsonify({
            "status": "success",
            "message": "Solicitud enviada. El mesero se acercará en breve.",
        }), 200

    # ----------------------------------------------------------
    # DIVIDIR LA CUENTA
    # ----------------------------------------------------------
    @staticmethod
    def dividir_cuenta(pedido_id: str):
        """
        POST /api/v1/cuenta/<pedido_id>/dividir
        Body: {num_personas: 3, tipo: "equitativo"}
               o {tipo: "personalizado", montos: [150.0, 200.0, 100.5]}
        Devuelve los montos por persona. El pago de cada parte se hace
        llamando a POST /api/v1/pagos con division_parte=N.
        """
        cliente_id = request.jwt_payload["sub"]
        doc = PedidoMovil.find_by_id(pedido_id)

        if not doc:
            return jsonify({"status": "error", "message": "Pedido no encontrado"}), 404
        if doc.get("cliente_id") != cliente_id:
            return jsonify({"status": "error", "message": "Sin permisos"}), 403

        data = request.get_json(silent=True) or {}
        tipo = data.get("tipo", "equitativo")
        subtotal = round(doc.get("total", 0.0), 2)

        if tipo == "equitativo":
            try:
                num_personas = int(data.get("num_personas", 2))
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": "num_personas inválido"}), 400

            if num_personas < 2 or num_personas > 20:
                return jsonify({"status": "error", "message": "num_personas debe ser entre 2 y 20"}), 400

            monto_base = subtotal / num_personas
            # Distribuir centavos de redondeo a la primera parte
            monto_redond = round(monto_base, 2)
            diferencia   = round(subtotal - monto_redond * num_personas, 2)
            partes = []
            for i in range(num_personas):
                extra = diferencia if i == 0 else 0.0
                partes.append({
                    "parte":  i + 1,
                    "monto":  round(monto_redond + extra, 2),
                })

        elif tipo == "personalizado":
            montos_raw = data.get("montos", [])
            if not isinstance(montos_raw, list) or len(montos_raw) < 2:
                return jsonify({"status": "error", "message": "montos debe ser una lista con al menos 2 elementos"}), 400
            try:
                montos = [round(float(m), 2) for m in montos_raw]
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": "montos inválidos"}), 400

            suma = round(sum(montos), 2)
            if abs(suma - subtotal) > 0.10:
                return jsonify({
                    "status": "error",
                    "message": f"La suma de los montos ({suma}) no coincide con el total ({subtotal})",
                }), 400

            partes = [{"parte": i + 1, "monto": m} for i, m in enumerate(montos)]
        else:
            return jsonify({"status": "error", "message": "tipo debe ser 'equitativo' o 'personalizado'"}), 400

        return jsonify({
            "status": "success",
            "data": {
                "pedido_id":   pedido_id,
                "subtotal":    subtotal,
                "num_partes":  len(partes),
                "partes":      partes,
                "instruccion": "Usa POST /api/v1/pagos con pedido_id, division_parte y propina_porcentaje para pagar cada parte.",
            },
        }), 200
