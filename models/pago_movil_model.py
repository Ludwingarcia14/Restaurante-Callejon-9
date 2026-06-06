"""
Modelo PagoMovil — registro de pagos desde la app móvil.
Separado de PedidoMovil para soportar división (N pagos por 1 pedido).
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

ESTADOS_PAGO = ("pendiente", "iniciado", "aprobado", "rechazado", "cancelado")


class PagoMovil:
    collection = db["pagos_movil"]

    # =========================================================
    # COMANDOS
    # =========================================================

    @classmethod
    def crear(cls, pedido_id: str, cliente_id: str, monto: float,
              propina_monto: float, propina_porcentaje: int,
              total_final: float, division_parte: int = 0,
              num_partes: int = 1) -> str:
        now = datetime.utcnow()
        doc = {
            "pedido_id":           pedido_id,
            "cliente_id":          cliente_id,
            "monto":               round(monto, 2),
            "propina_monto":       round(propina_monto, 2),
            "propina_porcentaje":  propina_porcentaje,
            "total_final":         round(total_final, 2),
            "division_parte":      division_parte,   # 0 = pago completo, 1..N = parte
            "num_partes":          num_partes,
            "estado":              "pendiente",
            "mp_preference_id":    None,
            "mp_payment_id":       None,
            "metodo":              "mercadopago",
            "created_at":          now,
            "updated_at":          now,
        }
        result = cls.collection.insert_one(doc)
        return str(result.inserted_id)

    @classmethod
    def set_preferencia(cls, pago_id: str, preference_id: str):
        return cls.collection.update_one(
            {"_id": ObjectId(pago_id)},
            {"$set": {"mp_preference_id": preference_id,
                      "estado": "iniciado",
                      "updated_at": datetime.utcnow()}}
        )

    @classmethod
    def set_aprobado(cls, pago_id: str, mp_payment_id: str):
        return cls.collection.update_one(
            {"_id": ObjectId(pago_id)},
            {"$set": {"mp_payment_id": mp_payment_id,
                      "estado": "aprobado",
                      "fecha_pago": datetime.utcnow(),
                      "updated_at": datetime.utcnow()}}
        )

    @classmethod
    def set_rechazado(cls, pago_id: str):
        return cls.collection.update_one(
            {"_id": ObjectId(pago_id)},
            {"$set": {"estado": "rechazado", "updated_at": datetime.utcnow()}}
        )

    # =========================================================
    # CONSULTAS
    # =========================================================

    @classmethod
    def find_by_id(cls, pago_id: str):
        try:
            return cls.collection.find_one({"_id": ObjectId(pago_id)})
        except Exception:
            return None

    @classmethod
    def find_by_pedido(cls, pedido_id: str) -> list:
        return list(cls.collection.find({"pedido_id": pedido_id}).sort("division_parte", 1))

    @classmethod
    def find_by_preference(cls, preference_id: str):
        return cls.collection.find_one({"mp_preference_id": preference_id})

    @classmethod
    def todos_aprobados(cls, pedido_id: str) -> bool:
        """True si todos los pagos del pedido están aprobados."""
        pagos = cls.find_by_pedido(pedido_id)
        if not pagos:
            return False
        return all(p.get("estado") == "aprobado" for p in pagos)

    # =========================================================
    # SERIALIZACIÓN
    # =========================================================

    @classmethod
    def to_public(cls, doc: dict) -> dict:
        if not doc:
            return {}
        return {
            "id":                  str(doc["_id"]),
            "pedido_id":           doc.get("pedido_id"),
            "monto":               doc.get("monto"),
            "propina_monto":       doc.get("propina_monto"),
            "propina_porcentaje":  doc.get("propina_porcentaje"),
            "total_final":         doc.get("total_final"),
            "division_parte":      doc.get("division_parte"),
            "num_partes":          doc.get("num_partes"),
            "estado":              doc.get("estado"),
            "metodo":              doc.get("metodo"),
            "mp_preference_id":    doc.get("mp_preference_id"),
            "created_at":          doc["created_at"].isoformat() if doc.get("created_at") else None,
        }

    # =========================================================
    # ÍNDICES
    # =========================================================

    @classmethod
    def ensure_indexes(cls):
        cls.collection.create_index("pedido_id")
        cls.collection.create_index("mp_preference_id")
        cls.collection.create_index([("pedido_id", 1), ("estado", 1)])
