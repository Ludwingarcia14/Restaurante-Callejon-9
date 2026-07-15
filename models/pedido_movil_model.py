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
    def crear(cls, cliente_id: str, mesa_numero, items: list, notas: str = "",
              tipo_entrega: str = "mesa", direccion: str = "", referencias: str = "") -> str:
        """
        items deben venir ya validados y con precios del servidor:
        [{platillo_id, nombre, precio, cantidad, notas}]

        tipo_entrega: "mesa" (consumo en el restaurante, requiere mesa_numero) o
                      "delivery" (a domicilio, requiere direccion; la ubicacion GPS
                      se agrega despues via PedidoMovil.set_ubicacion).
        """
        total = round(sum(float(i["precio"]) * int(i["cantidad"]) for i in items), 2)
        now = datetime.utcnow()
        doc = {
            "cliente_id": cliente_id,
            "tipo_entrega": tipo_entrega,
            "mesa_numero": mesa_numero,
            "direccion": direccion.strip() if direccion else "",
            "referencias": referencias.strip() if referencias else "",
            "ubicacion": None,  # {lat, lng, accuracy, capturado_at} — se llena en set_ubicacion
            "delivery_order_id": None,
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

    @classmethod
    def set_ubicacion(cls, pedido_id: str, lat: float, lng: float, accuracy: float = None):
        """Guarda la ubicacion GPS puntual capturada por el cliente para un pedido delivery."""
        return cls.collection.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {
                "ubicacion": {
                    "lat": float(lat),
                    "lng": float(lng),
                    "accuracy": float(accuracy) if accuracy is not None else None,
                    "capturado_at": datetime.utcnow(),
                },
                "updated_at": datetime.utcnow(),
            }},
        )

    @classmethod
    def set_delivery_order_id(cls, pedido_id: str, delivery_order_id: str):
        return cls.collection.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"delivery_order_id": ObjectId(delivery_order_id), "updated_at": datetime.utcnow()}},
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
        ubicacion = doc.get("ubicacion")
        if ubicacion and ubicacion.get("capturado_at"):
            ubicacion = {**ubicacion, "capturado_at": ubicacion["capturado_at"].isoformat()}

        return {
            "id": str(doc["_id"]),
            "folio": doc.get("folio", ""),
            "tipo_entrega": doc.get("tipo_entrega", "mesa"),
            "mesa_numero": doc.get("mesa_numero"),
            "direccion": doc.get("direccion", ""),
            "referencias": doc.get("referencias", ""),
            "ubicacion": ubicacion,
            "delivery_order_id": str(doc["delivery_order_id"]) if doc.get("delivery_order_id") else None,
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