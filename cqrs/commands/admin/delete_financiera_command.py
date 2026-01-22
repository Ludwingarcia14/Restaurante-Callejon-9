# application/commands/admin/delete_financiera_command.py
from models.financiera import Financiera
from bson.objectid import ObjectId

class DeleteFinancieraCommand:
    def __init__(self, financiera_ids: list):
        # financiera_ids es una lista, incluso para la eliminación individual
        self.financiera_ids = financiera_ids

    def _validate_ids(self):
        """Valida que todos los IDs sean ObjectIds válidos."""
        validated_ids = []
        for id_str in self.financiera_ids:
            try:
                validated_ids.append(ObjectId(id_str))
            except Exception:
                return False, f"ID de financiera inválido encontrado: {id_str}"
        return True, validated_ids

    def execute_single(self):
        """Elimina una sola financiera."""
        if len(self.financiera_ids) != 1:
            return False, 0, "Este método solo debe usarse para un solo ID."
        
        is_valid, obj_id_list = self._validate_ids()
        if not is_valid:
            return False, 0, obj_id_list
        
        try:
            # Asume que 'delete_one' es un método que elimina por ObjectId
            deleted_count = Financiera.delete_one(obj_id_list[0]) 
            if deleted_count == 0:
                return False, 0, "Financiera no encontrada para eliminar."
            return True, deleted_count, None
        except Exception as e:
            return False, 0, f"Error de base de datos al eliminar financiera: {e}"

    def execute_batch(self):
        """Elimina una lista de financieras."""
        is_valid, obj_id_list = self._validate_ids()
        if not is_valid:
            return False, 0, obj_id_list

        if not obj_id_list:
            return False, 0, "Lista de IDs vacía."

        try:
            # Asume que 'delete_many' es un método que elimina múltiples IDs
            deleted_count = Financiera.delete_many(obj_id_list) 
            return True, deleted_count, None
        except Exception as e:
            return False, 0, f"Error de base de datos al eliminar en lote: {e}"