# application/commands/admin/create_client_command.py
import uuid
import re
from datetime import datetime
from config.db import db # Necesario para la comprobación de unicidad
# No se necesita PasswordService porque un cliente creado por el administrador
# probablemente se registrará sin contraseña o con una contraseña temporal
# que se gestionará en el AuthController o en el modelo Cliente/Usuario.

# Se utiliza la misma regex para consistencia
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class CreateClientCommand:
    """
    Comando para crear un nuevo cliente en la colección 'clientes'.
    """
    def __init__(self, data: dict):
        self.data = data

    def _validate(self):
        """Realiza la validación de los datos de entrada del cliente."""
        required_fields = ["nombre", "apellido", "correo"]
        
        for field in required_fields:
            if not self.data.get(field) or not str(self.data.get(field)).strip():
                return False, f"El campo '{field}' es obligatorio."

        correo = str(self.data.get("correo")).strip().lower()

        if not EMAIL_REGEX.match(correo):
            return False, "El correo no tiene un formato válido."

        # 1. Verificar unicidad del email en la colección de clientes
        existing = db.clientes.find_one({"cliente_email": correo})
        if existing:
            return False, "Ya existe un cliente con ese correo."
            
        return True, None

    def execute(self):
        """Ejecuta el comando para crear el cliente."""
        is_valid, error = self._validate()
        if not is_valid:
            # Retorna el mensaje de error para que el controlador lo devuelva
            return False, error

        nombre = str(self.data.get("nombre")).strip()
        apellido = str(self.data.get("apellido")).strip()
        correo = str(self.data.get("correo")).strip().lower()

        # 1. Preparar el documento del cliente
        cliente = {
            "cliente_id": str(uuid.uuid4()),
            "cliente_nombre": nombre,
            "cliente_apellidos": apellido,
            "cliente_email": correo,
            "cliente_telefono": self.data.get("telefono"),
            "cliente_status": self.data.get("status", 0), # Asume un status por defecto
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 2. Guardar en la DB
        try:
            db.clientes.insert_one(cliente)
            return True, {"success": True, "cliente_id": cliente["cliente_id"]}
        except Exception as e:
            # Registrar el error real
            return False, f"Error interno al guardar el cliente en la base de datos: {e}"