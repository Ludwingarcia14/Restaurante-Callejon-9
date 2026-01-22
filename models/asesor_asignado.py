from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class AsesorAsignado:
    collection = db["asesores"]

    def __init__(self, nombre=None, telefono=None, correo=None, created_at=None, updated_at=None, _id=None):
        self._id = _id
        self.nombre = nombre
        self.telefono = telefono
        self.correo = correo
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    # 📌 Convierte el objeto a dict para MongoDB
    def to_dict(self):
        return {
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    # --- Métodos CRUD ---
    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})

    @classmethod
    def create(cls, data):
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, id, data):
        data["updated_at"] = datetime.utcnow()
        return cls.collection.update_one({"_id": ObjectId(id)}, {"$set": data})

    @classmethod
    def delete(cls, id):
        return cls.collection.delete_one({"_id": ObjectId(id)})

    # --- Métodos específicos ---
    @classmethod
    def obtener_asesor_por_cliente(cls, cliente_id):
        """
        Devuelve los datos del asesor asignado a un cliente.
        """
        cliente = db["clientes"].find_one({"_id": ObjectId(cliente_id)})
        if cliente and "cliente_idAsesor" in cliente and cliente["cliente_idAsesor"]:
            return cls.find_by_id(cliente["cliente_idAsesor"])
        return None

    @classmethod
    def obtener_citas_por_asesor(cls, asesor_id):
        """
        Devuelve todas las citas asociadas a un asesor.
        """
        return list(db["citas"].find({"asesor_id": ObjectId(asesor_id)}))
