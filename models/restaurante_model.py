"""
Modelo de Restaurante (tenant).

Es el registro GLOBAL de negocios del SaaS: cada documento es un restaurante
cliente con su marca (y, mas adelante, su logo/tema). NO es tenant-scoped (no
extiende BaseModel): es precisamente la lista de tenants.
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId


class Restaurante:
    collection = db["restaurantes"]
    DEFAULT_NOMBRE = "Callejón 9"

    @classmethod
    def find_default(cls):
        """Devuelve el restaurante por defecto (datos historicos) o None."""
        return cls.collection.find_one({"nombre": cls.DEFAULT_NOMBRE})

    @classmethod
    def ensure_default(cls):
        """Crea (si falta) el restaurante por defecto y devuelve su _id. Idempotente."""
        doc = cls.find_default()
        if doc:
            return doc["_id"]
        return cls.collection.insert_one({
            "nombre": cls.DEFAULT_NOMBRE,
            "slug": "callejon9",
            "activo": True,
            "created_at": datetime.utcnow(),
        }).inserted_id

    @classmethod
    def find_by_id(cls, restaurante_id):
        return cls.collection.find_one({"_id": ObjectId(restaurante_id)})

    @classmethod
    def update_config(cls, restaurante_id, update_dict):
        """Actualiza campos de configuracion del tenant (update con notacion de punto)."""
        if not update_dict:
            return None
        update_dict["updated_at"] = datetime.utcnow()
        return cls.collection.update_one(
            {"_id": ObjectId(restaurante_id)},
            {"$set": update_dict}
        )

    @classmethod
    def find_all(cls):
        return list(cls.collection.find().sort("nombre", 1))
