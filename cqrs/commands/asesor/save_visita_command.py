from config.db import db
from datetime import datetime

class SaveVisitaCommand:
    def __init__(self, id_cliente: str, asesor_id: str, data: dict):
        self.cliente_id = id_cliente
        self.asesor_id = asesor_id
        self.data = data

    def execute(self):
        """
        Guarda un nuevo registro de visita domiciliaria en la colección 'visitas'.
        """
        visita = {
            "cliente_id": self.cliente_id,
            "asesor_id": self.asesor_id,
            "direccion": self.data.get("direccion"),
            "fecha": datetime.utcnow(),
            "resultado": self.data.get("resultado"),
            "observaciones": self.data.get("observaciones")
        }
        db["visitas"].insert_one(visita)