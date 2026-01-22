from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
from typing import Dict, Any

class UpdateAsesorCommand:
    def __init__(self, asesor_id: str, data: Dict[str, str]):
        self.asesor_id = asesor_id
        self.data = data
        
    def execute(self) -> Dict[str, int]:
        """
        Actualiza los datos del asesor en la colección 'usuarios' por su _id.
        """
        try:
            asesor_obj_id = ObjectId(self.asesor_id)
        except Exception:
            raise ValueError("ID de asesor inválido.")

        # Preparar datos a actualizar, asegurando que los campos de ubicación estén presentes
        update_data = {
            "usuario_nombre": str(self.data.get("usuario_nombre")).strip(),
            "usuario_apellidos": str(self.data.get("usuario_apellidos")).strip(),
            "usuario_email": str(self.data.get("usuario_email")).strip().lower(),
            "usuario_telefono": str(self.data.get("usuario_telefono")).strip(),
            "usuario_cp": str(self.data.get("usuario_cp")).strip(),
            "usuario_idEstado": self.data.get("usuario_idEstado"),
            "usuario_idMunicipio": self.data.get("usuario_idMunicipio"),
            "usuario_idColonia": self.data.get("usuario_idColonia"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        result = db.usuarios.update_one(
            {"_id": asesor_obj_id, "usuario_rol": "3"}, # Filtro de seguridad por rol
            {"$set": update_data}
        )
        
        return {"matched_count": result.matched_count, "modified_count": result.modified_count}