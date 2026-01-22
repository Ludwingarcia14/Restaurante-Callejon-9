from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
import uuid
from typing import Dict, Any

class CreatePrestamoCommand:
    def __init__(self, data: Dict[str, str], session_user_id: str):
        self.data = data
        self.session_user_id = session_user_id

    def execute(self):
        """
        Crea un nuevo documento de préstamo en la colección 'prestamos'.
        """
        try:
            cliente_id = self.data.get("cliente_id")
            if not cliente_id:
                raise ValueError("El cliente es obligatorio")

            # Generar Clave Única (Simulada)
            nueva_clave = f"DB{datetime.now().strftime('%M%S')}"

            nuevo_prestamo = {
                "datbasicos_clave": self.data.get("clave") or nueva_clave,
                "cliente_id": ObjectId(cliente_id),
                "prestamo_monto": float(self.data.get("monto")),
                "prestamo_plazo": int(self.data.get("plazo")),
                "prestamo_tasa_interes": float(self.data.get("tasa")),
                "prestamo_motivo": self.data.get("motivo"),
                "prestamo_estado": "Pendiente", 
                "prestamo_fecha_solicitud": datetime.strptime(self.data.get("fecha_solicitud"), "%Y-%m-%d"),
                "prestamo_fecha_vencimiento": datetime.strptime(self.data.get("fecha_vencimiento"), "%Y-%m-%d"),
                "prestamo_observaciones": self.data.get("observaciones"),
                "creado_por": ObjectId(self.session_user_id),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None
            }

            db.prestamos.insert_one(nuevo_prestamo)
            return {"status": "success", "message": "Préstamo creado correctamente"}
            
        except Exception as e:
            raise Exception(f"Error al crear el préstamo: {e}")

# NOTA: En tu controlador, usarás esta clase, aunque el original usaba un "Handler".
# Si mantienes el archivo original con el nombre 'create_prestamo_command.py' este código es correcto.