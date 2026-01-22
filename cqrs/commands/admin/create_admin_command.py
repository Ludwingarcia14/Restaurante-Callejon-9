# application/commands/admin/create_admin_command.py
from models.user_model import Usuario  # Asume que tienes un modelo Usuario
from services.security.password_service import PasswordService # Asume un servicio para hashear
from bson.objectid import ObjectId
import re
import uuid
from datetime import datetime

class CreateAdminCommand:
    def __init__(self, data: dict):
        self.data = data
        self.email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def _validate(self):
        print("Validando datos de entrada...")
        print(f"Datos recibidos: {self.data}")
        """Realiza la validación de los datos de entrada."""
        required_fields = ["nombre", "correo", "contrasena", "tipo_persona"]
        
        for field in required_fields:
            if not self.data.get(field):
                return False, f"El campo '{field}' es obligatorio."

        if not self.email_regex.match(self.data["correo"]):
            return False, "Formato de email inválido."

        if Usuario.find_by_email(self.data["correo"]): # Asume este método en el modelo
            return False, "Ya existe un usuario con este email."
            
        try:
            # Asegura que rol_id sea un ObjectId válido si se usa Mongo u otra validación
            self.data["tipo_persona"]
        except Exception:
            return False, "ID de rol inválido."

        return True, None

    def execute(self):
        """Ejecuta el comando para crear el administrador."""
        is_valid, error = self._validate()
        if not is_valid:
            return False, error

        # 1. Hashear la contraseña
        hashed_password = PasswordService.hash_password(self.data["contrasena"])
        # 4️⃣ Generar permisos dinámicos según rol
        permisos_por_rol = {
            "1": {  # SuperAdmin
                "asesores": {"editar": True, "eliminar": True, "consultas": True},
                "clientes": {"editar": True, "eliminar": True, "consultas": True},
                "documentos": {"editar": True, "eliminar": True, "consultas": True},
                "reportes": {"ver": True, "exportar": True}
            },
            "2": {  # Admin básico
                "asesores": {"editar": True, "eliminar": False, "consultas": True},
                "clientes": {"editar": True, "eliminar": False, "consultas": True},
                "documentos": {"editar": True, "eliminar": False, "consultas": True}
            },
            "3": {  # Solo lectura
                "asesores": {"editar": False, "eliminar": False, "consultas": True},
                "clientes": {"editar": False, "eliminar": False, "consultas": True},
                "documentos": {"editar": False, "eliminar": False, "consultas": True}
            },
            # Puedes extender/ajustar roles 4,5,6...
            "4": {
                "asesores": {"editar": True, "eliminar": True, "consultas": True},
                "clientes": {"editar": True, "eliminar": True, "consultas": True},
                "documentos": {"editar": True, "eliminar": True, "consultas": True},
                "reportes": {"ver": True, "exportar": True}
            },
            "5": {
                "asesores": {"editar": True, "eliminar": True, "consultas": True},
                "clientes": {"editar": True, "eliminar": True, "consultas": True},
                "documentos": {"editar": True, "eliminar": True, "consultas": True},
                "reportes": {"ver": True, "exportar": True}
            },
            "6": {
                "asesores": {"editar": True, "eliminar": True, "consultas": True},
                "clientes": {"editar": True, "eliminar": True, "consultas": True},
                "documentos": {"editar": True, "eliminar": True, "consultas": True},
                "reportes": {"ver": True, "exportar": True}
            }
        }
        permisos = permisos_por_rol.get(self.data["tipo_persona"], {})
        # 2. Preparar los datos del nuevo usuario
        new_user_data = {
            "usuario_id": str(uuid.uuid4()),
            "usuario_nombre": self.data["nombre"],
            "usuario_apellidos": self.data["apellido"],
            "usuario_email": self.data["correo"],
            "usuario_clave": hashed_password,
            "usuario_foto": None,
            "usuario_rol": self.data["tipo_persona"],
            "usuario_idEstado": self.data["estado_id"] ,
            "usuario_idMunicipio": self.data["municipio_id"],
            "usuario_idColonia": self.data["colonia_id"],
            "usuario_cp": self.data["cp"],
            "usuario_idFinanciera": None,
            "usuario_status": 0,
            "usuario_token": "",
            "usuario_tokensession": None,
            "usuario_permisos": permisos,
            "usuario_direccion": self.data.get("direccion", ""),
            "usuario_telefono": self.data.get("telefono", ""),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # 3. Crear el usuario en la DB (función de modelo asumida)
        try:
            new_user_id = Usuario.create(new_user_data) 
            return True, {"message": "Administrador creado con éxito", "id": str(new_user_id)}
        except Exception as e:
            # Registrar el error real en la aplicación
            return False, f"Error interno al guardar en la base de datos: {e}"