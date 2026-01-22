from config.db import db
from datetime import datetime

class CreateAsesorProfileCommand:
    def __init__(self, usuario: dict, usuario_id: str):
        self.usuario = usuario
        self.usuario_id = usuario_id

    def execute(self) -> dict:
        """
        Crea un registro en 'asesores' si no existe, basado en 'usuarios'.
        Retorna el documento del asesor recién creado.
        """
        if not self.usuario:
            return None
            
        # Obtener RFC, manejando posibles nombres de campos diferentes
        rfc_value = self.usuario.get("usuario_rfc", "") or self.usuario.get("asesor_rfc", "") or ""
        
        asesor_data = {
            "usuario_id": self.usuario_id,
            "nombre": self.usuario.get("usuario_nombre", ""),
            "apellidos": self.usuario.get("usuario_apellidos", ""),
            "rfc": rfc_value,
            "correo": self.usuario.get("usuario_email", ""),
            "telefono": self.usuario.get("usuario_telefono", ""),
            "zona": self.usuario.get("zona", "Sin asignar"),
            "supervisor": self.usuario.get("supervisor", "Sin asignar"),
            "estado": "activo",
            "fecha_ingreso": self.usuario.get("created_at") or datetime.utcnow(),
            "desempeño_historico": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insertar y retornar el nuevo registro
        result = db["asesores"].insert_one(asesor_data)
        return db["asesores"].find_one({"_id": result.inserted_id})