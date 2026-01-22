from config.db import db
from bson.objectid import ObjectId
from typing import Dict

class EditSolicitudCommand:
    def __init__(self, solicitud_id: str, data: Dict[str, str]):
        self.solicitud_id = solicitud_id
        self.data = data

    def execute(self):
        """
        Actualiza el monto, plazo e interés de una solicitud de crédito.
        """
        # Convertir y validar datos
        monto = float(self.data.get("monto"))
        plazo = int(self.data.get("plazo"))
        interes = float(self.data.get("interes"))
        
        # Preparar la actualización
        update_set = {
            "monto": monto,
            "plazo": plazo,
            "interes": interes
        }
        
        # Ejecutar la actualización
        db.credito.update_one(
            {"_id": ObjectId(self.solicitud_id)},
            {"$set": update_set}
        )