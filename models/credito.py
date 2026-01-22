from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client.pyme  # tu base de datos
solicitudes = db.solicitudes_credito

class SolicitudCredito:
    def __init__(self, cliente_id, monto, plazo, interes, asesor=None, estado="Pendiente", fecha=None):
        self.cliente_id = cliente_id
        self.monto = monto
        self.plazo = plazo
        self.interes = interes
        self.asesor = asesor
        self.estado = estado
        self.fecha = fecha or datetime.now()

    def guardar(self):
        data = {
            "cliente_id": self.cliente_id,
            "monto": self.monto,
            "plazo": self.plazo,
            "interes": self.interes,
            "asesor": self.asesor,
            "estado": self.estado,
            "fecha": self.fecha
        }
        return solicitudes.insert_one(data)

    @staticmethod
    def obtener_por_cliente(cliente_id):
        return list(solicitudes.find({"cliente_id": cliente_id}))

    @staticmethod
    def obtener_por_id(solicitud_id):
        return solicitudes.find_one({"_id": ObjectId(solicitud_id)})

    @staticmethod
    def actualizar(solicitud_id, data):
        return solicitudes.update_one({"_id": ObjectId(solicitud_id)}, {"$set": data})

    @staticmethod
    def eliminar(solicitud_id):
        return solicitudes.delete_one({"_id": ObjectId(solicitud_id)})
