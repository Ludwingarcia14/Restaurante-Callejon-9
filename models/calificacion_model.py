"""
Modelo Calificacion — calificación del repartidor por parte del cliente
al finalizar un pedido a domicilio (Funcionalidad 3: historial "Mis pedidos").

Relación: una calificación por pedido (índice único), enlazada a
pedido_movil, cliente y repartidor.
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId


class Calificacion:
    collection = db["calificaciones"]

    @classmethod
    def crear(cls, pedido_id: str, cliente_id: str, repartidor_id,
              repartidor_nombre: str, estrellas: int, comentario: str = "",
              tenant_id: str = "") -> str:
        doc = {
            "pedido_id": ObjectId(pedido_id),
            "cliente_id": str(cliente_id),
            "repartidor_id": ObjectId(repartidor_id) if repartidor_id else None,
            "repartidor_nombre": repartidor_nombre or "",
            "estrellas": int(estrellas),
            "comentario": (comentario or "").strip(),
            "tenant_id": tenant_id or "",
            "created_at": datetime.utcnow(),
        }
        res = cls.collection.insert_one(doc)
        return str(res.inserted_id)

    @classmethod
    def find_by_pedido(cls, pedido_id: str):
        try:
            return cls.collection.find_one({"pedido_id": ObjectId(pedido_id)})
        except Exception:
            return None

    @classmethod
    def find_by_pedidos(cls, pedido_ids: list) -> dict:
        """Mapa {pedido_id(str): calificacion} para pintar el historial en lote."""
        oids = []
        for pid in pedido_ids:
            try:
                oids.append(ObjectId(pid))
            except Exception:
                continue
        out = {}
        for c in cls.collection.find({"pedido_id": {"$in": oids}}):
            out[str(c["pedido_id"])] = c
        return out

    @classmethod
    def to_public(cls, doc: dict) -> dict:
        if not doc:
            return None
        return {
            "estrellas": doc.get("estrellas", 0),
            "comentario": doc.get("comentario", ""),
            "repartidor_nombre": doc.get("repartidor_nombre", ""),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        }

    @classmethod
    def ensure_indexes(cls):
        # Una calificación por pedido; el índice hace la regla atómica.
        cls.collection.create_index("pedido_id", unique=True, name="uniq_pedido_id")
        cls.collection.create_index("repartidor_id")
