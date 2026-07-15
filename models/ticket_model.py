from config.db import db
from bson import ObjectId
from datetime import datetime


class Ticket:

    @staticmethod
    def create(comanda: dict, metodo_pago: str, propina: float,
               porcentaje_propina: float, total_final: float,
               fecha_cierre: datetime, payment_id=None) -> str:

        comanda_id = comanda["_id"]
        total      = float(comanda.get("total", 0))

        items = []
        for item in comanda.get("items", []):
            items.append({
                "nombre":    item.get("nombre", ""),
                "cantidad":  item.get("cantidad", 1),
                "precio":    float(item.get("precio", 0)),
                "subtotal":  round(float(item.get("precio", 0)) * int(item.get("cantidad", 1)), 2),
            })

        doc = {
            "comanda_id":         comanda_id,
            "folio_comanda":      comanda.get("folio", ""),
            "mesa_numero":        comanda.get("mesa_numero"),
            "mesero_id":          comanda.get("mesero_id"),
            "mesero_nombre":      comanda.get("mesero_nombre", ""),
            "num_comensales":     comanda.get("num_comensales", 0),
            "items":              items,
            "subtotal":           total,
            "propina":            propina,
            "porcentaje_propina": porcentaje_propina,
            "total_final":        total_final,
            "metodo_pago":        metodo_pago,
            "fecha_cierre":       fecha_cierre,
            "fecha_creacion":     datetime.now(),
        }

        if payment_id:
            doc["payment_id"] = payment_id

        result = db.tickets.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    def find_by_comanda(comanda_id: str):
        return db.tickets.find_one({"comanda_id": ObjectId(comanda_id)})

    @staticmethod
    def find_by_mesa(mesa_numero: int, limit=20):
        return list(
            db.tickets.find({"mesa_numero": mesa_numero})
            .sort("fecha_cierre", -1)
            .limit(limit)
        )

    @staticmethod
    def find_recientes(limit=50):
        return list(
            db.tickets.find()
            .sort("fecha_cierre", -1)
            .limit(limit)
        )
