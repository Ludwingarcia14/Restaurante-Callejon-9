# application/commands/admin/delete_user_command.py
from models.empleado_model import Usuario
from bson.objectid import ObjectId

class DeleteUserCommand:
    def __init__(self, user_ids: list):
        # user_ids es una lista, incluso para la eliminación individual
        self.user_ids = user_ids

    def _validate_ids(self):
        """Valida que todos los IDs sean ObjectIds válidos."""
        validated_ids = []
        for id_str in self.user_ids:
            try:
                validated_ids.append(ObjectId(id_str))
            except Exception:
                return False, f"ID de usuario inválido encontrado: {id_str}"
        return True, validated_ids

    def execute_single(self):
        """Elimina un solo usuario."""
        if len(self.user_ids) != 1:
            return False, 0, "Este método solo debe usarse para un solo ID."
        
        is_valid, obj_id_list = self._validate_ids()
        if not is_valid:
            return False, 0, obj_id_list # obj_id_list contiene el mensaje de error aquí
        
        try:
            # Asume que 'delete_one' es un método que elimina por ObjectId y devuelve el conteo
            deleted_count = Usuario.delete_one(obj_id_list[0]) 
            if deleted_count == 0:
                return False, 0, "Usuario no encontrado para eliminar."
            return True, deleted_count, None
        except Exception as e:
            return False, 0, f"Error de base de datos al eliminar usuario: {e}"

    def execute_batch(self):
        """Elimina una lista de usuarios."""
        is_valid, obj_id_list = self._validate_ids()
        if not is_valid:
            return False, 0, obj_id_list # obj_id_list contiene el mensaje de error aquí

        if not obj_id_list:
            return False, 0, "Lista de IDs vacía."

        try:
            # Asume que 'delete_many' es un método que elimina múltiples IDs y devuelve el conteo
            deleted_count = Usuario.delete_many(obj_id_list) 
            return True, deleted_count, None
        except Exception as e:
            return False, 0, f"Error de base de datos al eliminar en lote: {e}"