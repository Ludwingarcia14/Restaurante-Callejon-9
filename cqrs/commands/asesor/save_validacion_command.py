from config.db import db
from datetime import datetime

class SaveValidacionCommand:
    def __init__(self, solicitud_id: str, asesor_id: str, estado: str, comentario: str):
        self.solicitud_id = solicitud_id
        self.asesor_id = asesor_id
        self.estado = estado
        self.comentario = comentario

    def execute(self):
        """
        Registra la acción de validación documental del asesor en la colección 'validaciones'.
        """
        validacion_log = {
            "solicitud_id": self.solicitud_id,
            "asesor_id": self.asesor_id,
            "estado": self.estado,
            "comentario": self.comentario,
            "fecha": datetime.utcnow()
        }
        db["validaciones"].insert_one(validacion_log)