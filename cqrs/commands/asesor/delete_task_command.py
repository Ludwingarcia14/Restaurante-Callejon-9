from config.db import db
from bson.objectid import ObjectId

class DeleteTaskCommand:
    def __init__(self, tarea_id: str):
        self.tarea_id = tarea_id

    def execute(self):
        """Elimina una tarea."""
        db["asesor_tasks"].delete_one({"_id": ObjectId(self.tarea_id)})