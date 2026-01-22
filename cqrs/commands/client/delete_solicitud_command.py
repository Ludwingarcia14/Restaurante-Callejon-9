from config.db import db
from bson.objectid import ObjectId

class DeleteSolicitudCommand:
    def __init__(self, solicitud_id: str):
        self.solicitud_id = solicitud_id

    def execute(self):
        """
        Elimina una solicitud de crédito por su ID.
        """
        try:
            db.credito.delete_one({"_id": ObjectId(self.solicitud_id)})
        except Exception as e:
            # Es importante manejar excepciones si el ID no es válido
            raise ValueError(f"ID de solicitud inválido o error al eliminar: {e}")