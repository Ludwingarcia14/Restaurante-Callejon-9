from config.db import db
from datetime import datetime

class CreateTaskCommand:
    def __init__(self, asesor_id: str, data: dict):
        self.asesor_id = asesor_id
        self.data = data

    def execute(self):
        """Crea una nueva tarea para un asesor."""
        tarea = {
            "asesor_id": self.asesor_id,
            "titulo": self.data.get("titulo"),
            "detalle": self.data.get("detalle"),
            "status": "pendiente",
            "created_at": datetime.utcnow()
        }
        db["asesor_tasks"].insert_one(tarea)