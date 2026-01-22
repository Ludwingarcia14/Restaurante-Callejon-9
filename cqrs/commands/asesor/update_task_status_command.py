from config.db import db
from bson.objectid import ObjectId

class UpdateTaskStatusCommand:
    def __init__(self, tarea_id: str, asesor_id: str, status: str):
        self.tarea_id = tarea_id
        self.asesor_id = asesor_id
        self.status = status

    def execute(self) -> int:
        """Actualiza el estado de una tarea."""
        result = db["asesor_tasks"].update_one(
            {"_id": ObjectId(self.tarea_id), "asesor_id": self.asesor_id},
            {"$set": {"status": self.status}}
        )
        return result.modified_count