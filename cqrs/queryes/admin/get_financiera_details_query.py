"""
Query para obtener los detalles de una financiera por su _id.
"""
from config.db import db
from bson.objectid import ObjectId

class GetFinancieraDetailsQuery:
    """
    Recupera un único documento de la colección 'financieras' por su _id.
    """
    @staticmethod
    def execute(id):
        """
        Ejecuta la consulta para obtener los detalles de la financiera.

        Args:
            id (str): El ID de MongoDB (ObjectId) de la financiera.

        Returns:
            tuple: (dict de financiera, error)
        """
        try:
            object_id = ObjectId(id)
        except:
            return None, "ID de financiera inválido."

        try:
            financiera = db.financieras.find_one({"_id": object_id})
            
            if financiera:
                # Limpiar el objeto para JSON
                financiera["_id"] = str(financiera["_id"])
                return financiera, None
            else:
                return None, "Financiera no encontrada."
        except Exception as e:
            return None, str(e)