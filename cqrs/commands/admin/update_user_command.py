# application/commands/admin/update_user_command.py
from models.user_model import Usuario
from services.security.password_service import PasswordService
from bson.objectid import ObjectId
from datetime import datetime

class UpdateUserCommand:
    def __init__(self, user_id: str, data: dict):
        self.user_id = user_id
        self.data = data

    def _validate(self):
        """Valida el ID de usuario y los datos proporcionados."""
        try:
            obj_id = ObjectId(self.user_id)
        except Exception:
            return False, "ID de usuario inválido."

        if not Usuario.find_by_id(obj_id):
            return False, "Usuario no encontrado."

        # Validaciones de campos (ej. email único, formato de rol_id, etc.)
        if "rol_id" in self.data:
            try:
                ObjectId(self.data["rol_id"])
            except Exception:
                return False, "ID de rol inválido en los datos de actualización."

        return True, None

    def execute(self):
        """Ejecuta el comando para actualizar el usuario."""
        is_valid, error = self._validate()
        if not is_valid:
            return False, error

        update_data = self.data.copy()

        # 1. Procesar la contraseña si se está actualizando
        if "password" in update_data and update_data["password"]:
            update_data["password"] = PasswordService.hash_password(update_data["password"])
        else:
            update_data.pop("password", None) # Eliminar si está vacío o no se proporcionó

        # 2. Convertir IDs a ObjectId si es necesario
        if "rol_id" in update_data:
            update_data["rol_id"] = ObjectId(update_data["rol_id"])

        update_data["updated_at"] = datetime.now()

        # 3. Actualizar el usuario en la DB (función de modelo asumida)
        try:
            # Asume que 'update_one' es un método que actualiza por ObjectId
            success = Usuario.update_one(ObjectId(self.user_id), update_data)
            if success:
                return True, None
            else:
                return False, "No se pudo actualizar el usuario (posiblemente no se encontraron cambios)."
        except Exception as e:
            return False, f"Error de base de datos al actualizar: {e}"