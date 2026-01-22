from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
import random

class CreateSolicitudCommand:
    def __init__(self, usuario_id: ObjectId, data: dict):
        self.usuario_id = usuario_id
        self.data = data

    def execute(self):
        """Crea una nueva solicitud de crédito y asigna un asesor aleatorio."""
        # 1. Elegir un asesor aleatorio
        asesores = list(db.asesores.find())
        if asesores:
            asesor = random.choice(asesores)
            asesor_id = asesor["_id"]
            nombre_asesor = asesor.get("nombre", "-")
            telefono_asesor = asesor.get("telefono", "-")
            correo_asesor = asesor.get("correo", "-")
        else:
            asesor_id = None
            nombre_asesor = "-"
            telefono_asesor = "-"
            correo_asesor = "-"

        # 2. Construir la solicitud
        solicitud = {
            "cliente_id": self.usuario_id,
            "monto": float(self.data["monto"]),
            "plazo": int(self.data["plazo"]),
            "interes": float(self.data["interes"]),
            "asesor": asesor_id,
            "nombre_asesor": nombre_asesor,
            "telefono_asesor": telefono_asesor,
            "correo_asesor": correo_asesor,
            "estado": "Pendiente",
            "fecha": datetime.utcnow()
        }

        # 3. Insertar en la colección 'credito'
        db.credito.insert_one(solicitud)