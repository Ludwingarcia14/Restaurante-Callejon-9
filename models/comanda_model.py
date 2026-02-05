from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Comanda:
    @staticmethod
    def _collection():
        return db["comandas"]

    @classmethod
    def crear_comanda(cls, numero_mesa, num_comensales, mesero_id):
        nueva_comanda = {
            "mesa_numero": int(numero_mesa),
            "num_comensales": int(num_comensales),
            "mesero_id": str(mesero_id),
            "estado": "nueva", # nueva, enviada, lista, pagada
            "items": [],
            "total": 0.0,
            "fecha_apertura": datetime.utcnow(),
            "folio": f"COM-{datetime.now().strftime('%y%m%d%H%M%S')}"
        }
        res = cls._collection().insert_one(nueva_comanda)
        return str(res.inserted_id)

@classmethod
def agregar_items(cls, cuenta_id, lista_items):
        # Aseguramos que precio y cantidad sean números antes de sumar
        total = sum(float(item['precio']) * int(item['cantidad']) for item in lista_items)
        
        cls._collection().update_one(
            {"_id": ObjectId(cuenta_id)},
            {
                "$set": {
                    "items": lista_items,
                    "total": total,
                    "estado": "enviada"
                }
            }
        )
        return True