from config.db import db
from bson.objectid import ObjectId

class Cliente:

    collection = db.clientes  # Nombre de la colección

    @staticmethod
    def create(data):
        """Inserta un nuevo cliente."""
        return Cliente.collection.insert_one(data)

    @staticmethod
    def find_all():
        """Obtiene todos los clientes."""
        return list(Cliente.collection.find())

    @staticmethod
    def find_by_id(id):
        """Busca cliente por ID."""
        try:
            return Cliente.collection.find_one({"_id": ObjectId(id)})
        except:
            return None

    @staticmethod
    def find_by_email(email):
        """Busca cliente por email."""
        return Cliente.collection.find_one({"email": email})

    @staticmethod
    def update(id, data):
        """Actualiza un cliente."""
        try:
            return Cliente.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
        except:
            return None

    @staticmethod
    def delete(id):
        """Elimina un cliente."""
        try:
            return Cliente.collection.delete_one({"_id": ObjectId(id)})
        except:
            return None
