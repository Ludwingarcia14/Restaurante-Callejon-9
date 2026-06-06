"""
Modelo PedidoMovil — pedido realizado desde la app móvil.
Colección separada de comandas; el restaurante ve ambas en cocina.
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

ESTADOS_VALIDOS = ("pendiente", "recibido", "en_cocina", "listo", "entregado", "cancelado")


class PedidoMovil:
    collection = db["pedidos_movil"]

    # =========================================================
    # COMANDOS
    # =========================================================

    @classmethod
    def crear(cls, cliente_id: str, mesa_numero, items: list, notas: str = "") -> str:
        """
        items deben venir ya validados y con precios del servidor:
        [{platillo_id, nombre, precio, cantidad, notas}]
        """
        total = round(sum(float(i["precio"]) * int(i["cantidad"]) for i in items), 2)
        now = datetime.utcnow()
        doc = {
            "cliente_id": cliente_id,
            "mesa_numero": mesa_numero,
            "items": [
                {
                    "platillo_id": str(i["platillo_id"]),
                    "nombre": i["nombre"],
                    "precio": float(i["precio"]),
                    "cantidad": int(i["cantidad"]),
                    "notas": i.get("notas", ""),
                    "estado": "pendiente",
                }
                for i in items
            ],
            "estado": "pendiente",
            "total": total,
            "notas": notas,
            "folio": f"MOV-{now.strftime('%y%m%d%H%M%S')}",
            "created_at": now,
            "updated_at": now,
        }
        result = cls.collection.insert_one(doc)
        return str(result.inserted_id)

    @classmethod
    def update_estado(cls, pedido_id: str, nuevo_estado: str):
        return cls.collection.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"estado": nuevo_estado, "updated_at": datetime.utcnow()}},
        )

    # =========================================================
    # CONSULTAS
    # =========================================================

    @classmethod
    def find_by_id(cls, pedido_id: str):
        try:
            return cls.collection.find_one({"_id": ObjectId(pedido_id)})
        except Exception:
            return None

    @classmethod
    def find_activo_por_cliente(cls, cliente_id: str):
        """Pedido más reciente no finalizado del cliente."""
        return cls.collection.find_one(
            {"cliente_id": cliente_id, "estado": {"$nin": ["entregado", "cancelado"]}},
            sort=[("created_at", -1)],
        )

    @classmethod
    def find_pendientes_cocina(cls):
        """Todos los pedidos móviles que aún no están entregados (para cocina)."""
        return list(
            cls.collection.find(
                {"estado": {"$in": ["pendiente", "recibido", "en_cocina", "listo"]}}
            ).sort("created_at", 1)
        )

    @classmethod
    def find_by_cliente_paginado(cls, cliente_id: str, limit: int, skip: int):
        query = {"cliente_id": cliente_id}
        total = cls.collection.count_documents(query)
        docs = list(
            cls.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )
        return docs, total

    # =========================================================
    # SERIALIZACIÓN
    # =========================================================

    @classmethod
    def to_public(cls, doc: dict) -> dict:
        if not doc:
            return {}
        return {
            "id": str(doc["_id"]),
            "folio": doc.get("folio", ""),
            "mesa_numero": doc.get("mesa_numero"),
            "items": doc.get("items", []),
            "estado": doc.get("estado", "pendiente"),
            "total": doc.get("total", 0.0),
            "notas": doc.get("notas", ""),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
        }

    # =========================================================
    # ÍNDICES
    # =========================================================

    @classmethod
    def ensure_indexes(cls):
        cls.collection.create_index("cliente_id")
        cls.collection.create_index("estado")
        cls.collection.create_index([("cliente_id", 1), ("estado", 1)])
