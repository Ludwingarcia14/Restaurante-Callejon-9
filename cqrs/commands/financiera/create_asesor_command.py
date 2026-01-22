from config.db import db
from datetime import datetime
import uuid
import bcrypt
from typing import Dict

class CreateAsesorCommand:
    def __init__(self, data: Dict[str, str], permisos: Dict):
        self.data = data
        self.permisos = permisos
        
    def execute(self):
        correo = str(self.data.get("correo")).strip().lower()
        contrasena = str(self.data.get("contrasena"))
        
        # Validar si ya existe
        existing = db.usuarios.find_one({"usuario_email": correo})
        if existing:
            raise ValueError("Ya existe un usuario con ese correo")
        
        # Encriptar contraseña
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed_password = bcrypt.hashpw(contrasena.encode("utf-8"), salt)
            hashed_str = hashed_password.decode("utf-8")
        except Exception:
            raise Exception("Error al procesar la contraseña")

        # Construir el documento
        usuario = {
            "usuario_id": str(uuid.uuid4()),
            "usuario_nombre": str(self.data.get("nombre")).strip(),
            "usuario_apellidos": str(self.data.get("apellido")).strip(),
            "usuario_telefono": str(self.data.get("telefono")).strip() if self.data.get("telefono") else None,
            "usuario_email": correo,
            "usuario_clave": hashed_str,
            "usuario_rol": str(self.data.get("tipo_persona")).strip(),
            "usuario_idEstado": self.data.get("estado_id"),
            "usuario_idMunicipio": self.data.get("municipio_id"),
            "usuario_idColonia": self.data.get("colonia_id"),
            "usuario_cp": self.data.get("cp"),
            "usuario_idFinanciera": None,
            "usuario_status": "0",
            "usuario_permisos": self.permisos,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardar en la DB
        try:
            db.usuarios.insert_one(usuario)
            return usuario["usuario_id"]
        except Exception as e:
            raise Exception(f"Error al guardar el usuario en la DB: {e}")