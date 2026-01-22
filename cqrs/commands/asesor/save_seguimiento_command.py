from config.db import db
from bson.objectid import ObjectId
from datetime import datetime

class SaveSeguimientoCommand:
    def __init__(self, solicitud_id: str, asesor_id: str, data: dict):
        self.solicitud_id = solicitud_id
        self.asesor_id = asesor_id
        self.data = data

    def execute(self):
        """Guarda un nuevo registro de contacto y actualiza la solicitud."""
        solicitud_obj_id = ObjectId(self.solicitud_id)
        
        contacto = {
            "solicitud_id": self.solicitud_id,
            "asesor_id": self.asesor_id,
            "fecha": datetime.utcnow(),
            "medio": self.data.get("medio"),
            "comentarios": self.data.get("comentarios"),
            "resultado": self.data.get("resultado"),
            "created_at": datetime.utcnow()
        }
        db["contactos"].insert_one(contacto)
        
        # Actualizar la fecha de último contacto en la solicitud
        db["solicitudes"].update_one(
            {"_id": solicitud_obj_id},
            {"$set": {"ultimo_contacto": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )