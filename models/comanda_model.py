from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Comanda:

    @staticmethod
    def _collection():
        return db["comandas"]

    @classmethod
    def crear_comanda(cls, numero_mesa, num_comensales, mesero_id, mesero_nombre="Mesero"):
        """
        Crea una nueva comanda con estructura mejorada para cocina
        """
        print("MESERO_ID RECIBIDO:", mesero_id, type(mesero_id))
        
        nueva_comanda = {
            "mesa_numero": int(numero_mesa),
            "num_comensales": int(num_comensales),
            "mesero_id": ObjectId(mesero_id),
            "mesero_nombre": mesero_nombre,  # 🆕 Nombre del mesero
            "estado": "nueva",  # nueva, enviada, lista, pagada
            "items": [],
            "total": 0.0,
            "fecha_apertura": datetime.utcnow(),
            "folio": f"COM-{datetime.now().strftime('%y%m%d%H%M%S')}"
        }
        
        res = cls._collection().insert_one(nueva_comanda)
        return str(res.inserted_id)

    @classmethod
    def agregar_items(cls, cuenta_id, lista_items):
        """
        Agrega items a una comanda existente
        Ahora inicializa el estado de cocina para cada item
        """
        # Agregar estado de cocina a cada item
        items_con_estado = []
        for item in lista_items:
            item_con_estado = {
                **item,
                "estado_cocina": "pendiente",  # pendiente, en_preparacion, listo, entregado
                "fecha_pedido": datetime.utcnow()
            }
            items_con_estado.append(item_con_estado)
        
        total = sum(
            float(item["precio"]) * int(item["cantidad"])
            for item in items_con_estado
        )

        cls._collection().update_one(
            {"_id": ObjectId(cuenta_id)},
            {
                "$set": {
                    "items": items_con_estado,
                    "total": total,
                    "estado": "enviada",
                    "fecha_envio_cocina": datetime.utcnow()
                }
            }
        )
        return True

    @classmethod
    def actualizar_estado_item(cls, cuenta_id, producto_id, nuevo_estado):
        """
        Actualiza el estado de cocina de un item específico
        Estados: pendiente -> en_preparacion -> listo -> entregado
        """
        campo_fecha = f"items.$.fecha_{nuevo_estado}"
        
        cls._collection().update_one(
            {
                "_id": ObjectId(cuenta_id),
                "items.producto_id": producto_id
            },
            {
                "$set": {
                    "items.$.estado_cocina": nuevo_estado,
                    campo_fecha: datetime.utcnow()
                }
            }
        )
        return True

    @classmethod
    def obtener_items_por_estado(cls, cuenta_id, estado_cocina):
        """
        Obtiene los items de una comanda filtrados por estado de cocina
        """
        comanda = cls._collection().find_one({"_id": ObjectId(cuenta_id)})
        
        if not comanda:
            return []
        
        items_filtrados = [
            item for item in comanda.get("items", [])
            if item.get("estado_cocina") == estado_cocina
        ]
        
        return items_filtrados