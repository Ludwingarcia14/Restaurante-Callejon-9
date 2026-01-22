from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Notificacion:
    collection = db["notificaciones"]

    def __init__(self, tipo=None, mensaje=None, id_usuario=None,
                 leida=False, fecha=None, created_at=None, updated_at=None, _id=None):
        
        self._id = _id
        self.tipo = tipo
        self.mensaje = mensaje
        self.id_usuario = ObjectId(id_usuario) if id_usuario else None
        self.leida = leida
        self.fecha = fecha or datetime.utcnow()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    # -----------------------------------------
    # Convertir a diccionario (MongoDB)
    # -----------------------------------------
    def to_dict(self):
        return {
            "tipo": self.tipo,
            "mensaje": self.mensaje,
            "id_usuario": self.id_usuario,
            "leida": self.leida,
            "fecha": self.fecha,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    # -----------------------------------------
    # Métodos CRUD
    # -----------------------------------------

    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})

    @classmethod
    def get_by_user(cls, id_usuario):
        return list(cls.collection.find(
            {"id_usuario": ObjectId(id_usuario)}
        ).sort("fecha", -1))

    @classmethod
    def create(cls, data):
        data["fecha"] = datetime.utcnow()
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, id, data):
        data["updated_at"] = datetime.utcnow()

        return cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )

    @classmethod
    def marcar_todas_leidas(cls, id_usuario):
        return cls.collection.update_many(
            {"id_usuario": ObjectId(id_usuario)},
            {"$set": {"leida": True, "updated_at": datetime.utcnow()}}
        )

    @classmethod
    def delete(cls, id):
        return cls.collection.delete_one({"_id": ObjectId(id)})

    @classmethod
    def get_all(cls, limit=None):
        cursor = cls.collection.find().sort("fecha", -1)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
