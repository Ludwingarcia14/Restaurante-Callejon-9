from flask import request, session, jsonify, render_template
from models.delivery_model import DeliveryOrder, Repartidor
from models.empleado_model import Usuario
from services.security.password_service import PasswordService
from bson.objectid import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _serialize(doc):
    """Convierte ObjectId y datetime a strings para JSON."""
    if doc is None:
        return None
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.strftime("%Y-%m-%d %H:%M")
        else:
            out[k] = v
    return out


# ─────────────────────────────────────────────
# VISTAS (HTML)
# ─────────────────────────────────────────────

class RepartidorViewController:

    @staticmethod
    def dashboard():
        repartidor_id = session.get("usuario_id")
        tenant_id = session.get("tenant_id", "")
        nombre = session.get("usuario_nombre", "")

        # Entregas activas asignadas a este repartidor
        activas = DeliveryOrder.listar_por_repartidor(repartidor_id, solo_activos=True)
        stats = DeliveryOrder.stats_repartidor(repartidor_id)

        return render_template(
            "repartidor/dashboard.html",
            nombre=nombre,
            activas=[_serialize(d) for d in activas],
            stats=stats,
        )

    @staticmethod
    def mis_entregas():
        repartidor_id = session.get("usuario_id")
        activas = DeliveryOrder.listar_por_repartidor(repartidor_id, solo_activos=True)
        return render_template(
            "repartidor/mis_entregas.html",
            entregas=[_serialize(d) for d in activas],
        )

    @staticmethod
    def historial():
        repartidor_id = session.get("usuario_id")
        entregadas = DeliveryOrder.historial(repartidor_id=repartidor_id, limit=50)
        stats = DeliveryOrder.stats_repartidor(repartidor_id)
        return render_template(
            "repartidor/historial.html",
            entregas=[_serialize(d) for d in entregadas],
            stats=stats,
        )


class AdminDeliveryViewController:

    @staticmethod
    def panel():
        tenant_id = session.get("tenant_id", "")
        pendientes = DeliveryOrder.listar_pendientes(tenant_id)
        repartidores = Repartidor.listar_activos(tenant_id)
        return render_template(
            "admin/delivery_panel.html",
            pedidos=[_serialize(d) for d in pendientes],
            repartidores=[_serialize(r) for r in repartidores],
        )

    @staticmethod
    def gestion_repartidores():
        tenant_id = session.get("tenant_id", "")
        repartidores = Repartidor.listar_todos(tenant_id)
        return render_template(
            "admin/repartidores.html",
            repartidores=[_serialize(r) for r in repartidores],
        )


# ─────────────────────────────────────────────
# API — DELIVERY ORDERS
# ─────────────────────────────────────────────

class DeliveryAPIController:

    @staticmethod
    def crear():
        try:
            data = request.get_json(force=True)
            if not data:
                return jsonify({"success": False, "error": "Sin datos"}), 400

            required = ["cliente_nombre", "direccion"]
            for f in required:
                if not data.get(f):
                    return jsonify({"success": False, "error": f"Falta campo: {f}"}), 400
            if data.get("tipo") != "comanda" and not data.get("items"):
                return jsonify({"success": False, "error": "Falta campo: items"}), 400

            # Calcular total desde items si no viene
            if not data.get("total"):
                data["total"] = sum(
                    float(i.get("precio", 0)) * int(i.get("cantidad", 1))
                    for i in data["items"]
                )

            data["creado_por_id"] = session.get("usuario_id")
            data["creado_por_nombre"] = session.get("usuario_nombre", "")
            data["tenant_id"] = session.get("tenant_id", "")

            delivery_id = DeliveryOrder.crear(data)
            return jsonify({"success": True, "delivery_id": delivery_id})

        except Exception as e:
            logger.error("Error creando delivery: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def asignar(delivery_id):
        try:
            data = request.get_json(force=True)
            repartidor_id = data.get("repartidor_id")
            if not repartidor_id:
                return jsonify({"success": False, "error": "Falta repartidor_id"}), 400

            rep = Repartidor.get_by_id(repartidor_id)
            if not rep:
                return jsonify({"success": False, "error": "Repartidor no encontrado"}), 404

            nombre = f"{rep.get('usuario_nombre','')} {rep.get('usuario_apellidos','')}".strip()
            DeliveryOrder.asignar_repartidor(delivery_id, repartidor_id, nombre)
            return jsonify({"success": True})

        except Exception as e:
            logger.error("Error asignando repartidor: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def actualizar_estado(delivery_id):
        try:
            data = request.get_json(force=True)
            nuevo_estado = data.get("estado")
            estados_validos = ["pendiente", "asignado", "en_camino", "entregado", "cancelado"]
            if nuevo_estado not in estados_validos:
                return jsonify({"success": False, "error": "Estado inválido"}), 400

            DeliveryOrder.actualizar_estado(delivery_id, nuevo_estado)
            return jsonify({"success": True, "estado": nuevo_estado})

        except Exception as e:
            logger.error("Error actualizando estado: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def listar_pendientes():
        try:
            tenant_id = session.get("tenant_id", "")
            pedidos = DeliveryOrder.listar_pendientes(tenant_id)
            return jsonify({"success": True, "pedidos": [_serialize(p) for p in pedidos]})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def mis_entregas_api():
        try:
            repartidor_id = session.get("usuario_id")
            solo_activos = request.args.get("activas", "1") == "1"
            entregas = DeliveryOrder.listar_por_repartidor(repartidor_id, solo_activos)
            return jsonify({"success": True, "entregas": [_serialize(e) for e in entregas]})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def historial_api():
        try:
            tenant_id = session.get("tenant_id", "")
            repartidor_id = request.args.get("repartidor_id")
            entregadas = DeliveryOrder.historial(tenant_id=tenant_id, repartidor_id=repartidor_id)
            return jsonify({"success": True, "entregas": [_serialize(e) for e in entregadas]})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
# API — REPARTIDORES (CRUD admin)
# ─────────────────────────────────────────────

class RepartidorAPIController:

    @staticmethod
    def listar():
        try:
            tenant_id = session.get("tenant_id", "")
            reps = Repartidor.listar_todos(tenant_id)
            return jsonify({"success": True, "repartidores": [_serialize(r) for r in reps]})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def crear():
        try:
            data = request.get_json(force=True)
            required = ["usuario_nombre", "usuario_email", "usuario_clave"]
            for f in required:
                if not data.get(f):
                    return jsonify({"success": False, "error": f"Falta: {f}"}), 400

            # Verificar email único
            if Usuario.find_by_email(data["usuario_email"]):
                return jsonify({"success": False, "error": "Email ya registrado"}), 409

            doc = {
                "usuario_nombre":    data["usuario_nombre"],
                "usuario_apellidos": data.get("usuario_apellidos", ""),
                "usuario_email":     data["usuario_email"].strip().lower(),
                "usuario_clave":     PasswordService.hash_password(data["usuario_clave"]),
                "usuario_rol":       "5",
                "usuario_status":    1,
                "tenant_id":         session.get("tenant_id", ""),
                "vehiculo":          data.get("vehiculo", ""),
                "telefono":          data.get("telefono", ""),
                "notas":             data.get("notas", ""),
                "created_at":        datetime.utcnow(),
                "updated_at":        datetime.utcnow(),
            }
            res = Usuario.collection.insert_one(doc)
            return jsonify({"success": True, "id": str(res.inserted_id)})

        except Exception as e:
            logger.error("Error creando repartidor: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def actualizar(uid):
        try:
            data = request.get_json(force=True)
            update = {}
            for f in ["usuario_nombre", "usuario_apellidos", "vehiculo", "telefono", "notas", "usuario_status"]:
                if f in data:
                    update[f] = data[f]
            if data.get("usuario_clave"):
                update["usuario_clave"] = PasswordService.hash_password(data["usuario_clave"])
            update["updated_at"] = datetime.utcnow()
            Usuario.collection.update_one({"_id": ObjectId(uid)}, {"$set": update})
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def eliminar(uid):
        try:
            Usuario.collection.update_one(
                {"_id": ObjectId(uid)},
                {"$set": {"usuario_status": 0, "updated_at": datetime.utcnow()}}
            )
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
