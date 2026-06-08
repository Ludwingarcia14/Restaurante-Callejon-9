"""
Pedidos desde la app móvil.
- Crear pedido: valida QR, valida items contra BD, precios siempre del servidor.
- Seguimiento: polling + Socket.IO en sala cliente_{id}.
- Estado: cocina/admin pueden actualizar via PATCH.
"""
import logging
from bson.objectid import ObjectId

from flask import request, jsonify
from models.pedido_movil_model import PedidoMovil, ESTADOS_VALIDOS
from models.menu_model import Platillo
from models.mesa_model import Mesa
from utils.validators import sanitize_str
from utils.pagination import get_pagination_params, paginate_response

logger = logging.getLogger(__name__)


def _emitir_a_cocina(pedido_doc: dict):
    """Notifica a la sala 'cocina' sobre el nuevo pedido móvil."""
    try:
        from extensions import socketio
        from datetime import datetime
        socketio.emit(
            "nuevo_pedido_movil",
            {
                "pedido_id": str(pedido_doc["_id"]),
                "folio": pedido_doc.get("folio"),
                "mesa": pedido_doc.get("mesa_numero"),
                "total": pedido_doc.get("total"),
                "num_items": len(pedido_doc.get("items", [])),
                "timestamp": datetime.utcnow().isoformat(),
            },
            room="cocina",
            namespace="/",
        )
    except Exception as e:
        logger.warning("No se pudo emitir a cocina: %s", e)


def _emitir_actualizacion_cliente(cliente_id: str, pedido_doc: dict):
    """Notifica al cliente el nuevo estado de su pedido."""
    try:
        from extensions import socketio
        socketio.emit(
            "pedido_actualizado",
            {
                "pedido_id": str(pedido_doc["_id"]),
                "estado": pedido_doc.get("estado"),
                "folio": pedido_doc.get("folio"),
            },
            room=f"cliente_{cliente_id}",
            namespace="/",
        )
    except Exception as e:
        logger.warning("No se pudo emitir actualización al cliente: %s", e)


class PedidoMovilController:

    # ----------------------------------------------------------
    # CREAR PEDIDO
    # ----------------------------------------------------------
    @staticmethod
    def crear_pedido():
        """
        POST /api/v1/pedidos
        Body: {mesa_numero, items: [{platillo_id, cantidad, notas?}], notas?}
        Los precios se obtienen del servidor, no del cliente.
        """
        cliente_id = request.jwt_payload["sub"]
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Se requiere body JSON"}), 400

        mesa_numero = data.get("mesa_numero")
        items_raw   = data.get("items", [])
        notas       = sanitize_str(data.get("notas", ""), 300)

        # --- Validar mesa ---
        if mesa_numero is None:
            return jsonify({"status": "error", "message": "mesa_numero es requerido"}), 400

        mesa_doc = Mesa.find_by_numero(mesa_numero)
        if not mesa_doc:
            return jsonify({"status": "error", "message": "Mesa no encontrada"}), 404

        # --- Validar items ---
        if not items_raw or not isinstance(items_raw, list):
            return jsonify({"status": "error", "message": "items es requerido y debe ser una lista"}), 400

        if len(items_raw) > 20:
            return jsonify({"status": "error", "message": "Máximo 20 items por pedido"}), 400

        items_validados = []
        errores = []

        for idx, item in enumerate(items_raw):
            platillo_id = item.get("platillo_id", "")
            cantidad    = item.get("cantidad", 0)

            if not platillo_id:
                errores.append(f"Item {idx + 1}: platillo_id requerido")
                continue

            try:
                cantidad = int(cantidad)
            except (ValueError, TypeError):
                errores.append(f"Item {idx + 1}: cantidad inválida")
                continue

            if cantidad < 1 or cantidad > 50:
                errores.append(f"Item {idx + 1}: cantidad debe ser entre 1 y 50")
                continue

            try:
                platillo = Platillo.find_by_id(platillo_id)
            except Exception:
                errores.append(f"Item {idx + 1}: platillo_id inválido")
                continue

            if not platillo:
                errores.append(f"Item {idx + 1}: platillo no encontrado")
                continue

            if not platillo.get("disponible", True):
                errores.append(f"Item {idx + 1}: '{platillo.get('nombre')}' no está disponible")
                continue

            items_validados.append({
                "platillo_id": str(platillo["_id"]),
                "nombre":     platillo.get("nombre", ""),
                "precio":     float(platillo.get("precio", 0)),
                "cantidad":   cantidad,
                "notas":      sanitize_str(item.get("notas", ""), 200),
            })

        if errores:
            return jsonify({"status": "error", "message": "Errores en los items", "errores": errores}), 400

        if not items_validados:
            return jsonify({"status": "error", "message": "No hay items válidos en el pedido"}), 400

        # --- Crear pedido ---
        try:
            pedido_id = PedidoMovil.crear(
                cliente_id=cliente_id,
                mesa_numero=mesa_doc.get("numero"),
                items=items_validados,
                notas=notas,
            )
        except Exception as e:
            logger.error("Error creando pedido móvil: %s", e)
            return jsonify({"status": "error", "message": "Error al crear el pedido"}), 500

        pedido_doc = PedidoMovil.find_by_id(pedido_id)
        _emitir_a_cocina(pedido_doc)

        return jsonify({
            "status": "success",
            "message": "Pedido enviado a cocina",
            "data": PedidoMovil.to_public(pedido_doc),
        }), 201

    # ----------------------------------------------------------
    # PEDIDO ACTIVO DEL CLIENTE
    # ----------------------------------------------------------
    @staticmethod
    def get_pedido_activo():
        """GET /api/v1/pedidos/activo"""
        cliente_id = request.jwt_payload["sub"]
        doc = PedidoMovil.find_activo_por_cliente(cliente_id)
        if not doc:
            return jsonify({"status": "success", "data": None, "message": "Sin pedido activo"}), 200
        return jsonify({"status": "success", "data": PedidoMovil.to_public(doc)}), 200

    # ----------------------------------------------------------
    # DETALLE DE PEDIDO POR ID
    # ----------------------------------------------------------
    @staticmethod
    def get_pedido(pedido_id: str):
        """GET /api/v1/pedidos/<pedido_id>"""
        cliente_id = request.jwt_payload["sub"]
        doc = PedidoMovil.find_by_id(pedido_id)

        if not doc:
            return jsonify({"status": "error", "message": "Pedido no encontrado"}), 404

        # El cliente solo puede ver sus propios pedidos
        if doc.get("cliente_id") != cliente_id:
            return jsonify({"status": "error", "message": "Sin permisos"}), 403

        return jsonify({"status": "success", "data": PedidoMovil.to_public(doc)}), 200

    # ----------------------------------------------------------
    # ACTUALIZAR ESTADO (cocina / admin)
    # ----------------------------------------------------------
    @staticmethod
    def actualizar_estado(pedido_id: str):
        """
        PATCH /api/v1/admin/pedidos-movil/<pedido_id>/estado
        Body: {estado: "en_cocina" | "listo" | "entregado" | "cancelado"}
        Requiere rol 1 (admin) o 3 (cocina).
        """
        data = request.get_json(silent=True)
        if not data or not data.get("estado"):
            return jsonify({"status": "error", "message": "estado es requerido"}), 400

        nuevo_estado = data["estado"].strip().lower()
        if nuevo_estado not in ESTADOS_VALIDOS:
            return jsonify({
                "status": "error",
                "message": f"Estado inválido. Opciones: {', '.join(ESTADOS_VALIDOS)}"
            }), 400

        doc = PedidoMovil.find_by_id(pedido_id)
        if not doc:
            return jsonify({"status": "error", "message": "Pedido no encontrado"}), 404

        try:
            PedidoMovil.update_estado(pedido_id, nuevo_estado)
        except Exception as e:
            logger.error("Error actualizando estado: %s", e)
            return jsonify({"status": "error", "message": "Error al actualizar el estado"}), 500

        doc["estado"] = nuevo_estado
        _emitir_actualizacion_cliente(doc.get("cliente_id", ""), doc)

        return jsonify({
            "status": "success",
            "message": f"Estado actualizado a '{nuevo_estado}'",
            "data": PedidoMovil.to_public(doc),
        }), 200

    # ----------------------------------------------------------
    # LISTAR PEDIDOS MÓVILES PARA COCINA
    # ----------------------------------------------------------
    @staticmethod
    def listar_para_cocina():
        """GET /api/v1/admin/pedidos-movil  — para la vista de cocina/admin"""
        try:
            pedidos = PedidoMovil.find_pendientes_cocina()
        except Exception as e:
            logger.error("Error listando pedidos cocina: %s", e)
            return jsonify({"status": "error", "message": "Error al obtener pedidos"}), 500

        return jsonify({
            "status": "success",
            "data": [PedidoMovil.to_public(p) for p in pedidos],
            "total": len(pedidos),
        }), 200
