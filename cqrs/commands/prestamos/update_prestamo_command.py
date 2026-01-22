from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
from typing import Dict

class UpdatePrestamoCommand:
    def __init__(self, prestamo_id: str, data: Dict[str, str], session_user_id: str):
        self.prestamo_id = prestamo_id
        self.data = data
        self.session_user_id = session_user_id

    def execute(self) -> Dict[str, int]:
        """
        Actualiza el documento de préstamo en la colección 'prestamos'.
        Retorna el número de documentos modificados.
        """
        try:
            update_fields = {
                "prestamo_monto": float(self.data.get("monto")),
                "prestamo_plazo": int(self.data.get("plazo")),
                "prestamo_tasa_interes": float(self.data.get("tasa")),
                "prestamo_estado": self.data.get("estado"),
                "prestamo_motivo": self.data.get("motivo"),
                "prestamo_fecha_vencimiento": datetime.strptime(self.data.get("fecha_vencimiento"), "%Y-%m-%d"),
                "prestamo_observaciones": self.data.get("observaciones"),
                "actualizado_por": ObjectId(self.session_user_id),
                "updated_at": datetime.now()
            }
            
            result = db.prestamos.update_one(
                {"_id": ObjectId(self.prestamo_id)},
                {"$set": update_fields}
            )
            return {"matched_count": result.matched_count, "modified_count": result.modified_count}
            
        except ValueError:
            raise ValueError("Error de formato en los datos (monto, plazo, fecha, etc.).")
        except Exception as e:
            raise Exception(f"Error al actualizar el préstamo: {e}")