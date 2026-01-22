# application/commands/admin/update_financiera_command.py
from models.financiera import Financiera
from bson.objectid import ObjectId
from datetime import datetime

class UpdateFinancieraCommand:
    def __init__(self, financiera_id: str, data: dict):
        self.financiera_id = financiera_id
        self.data = data

    def _validate(self):
        """Valida el ID de la financiera y los datos proporcionados."""
        try:
            obj_id = ObjectId(self.financiera_id)
        except Exception:
            return False, "ID de financiera inválido."

        if not Financiera.find_by_id(obj_id):
            return False, "Financiera no encontrada."

        # Validaciones de campos (ej. unicidad de nombre_fiscal si se cambia)
        if "nombre_fiscal" in self.data:
            existing = Financiera.find_by_name(self.data["nombre_fiscal"])
            if existing and str(existing.id) != self.financiera_id:
                return False, "Ya existe otra financiera con este nombre fiscal."

        return True, None

    def execute(self):
        """Ejecuta el comando para actualizar la financiera."""
        is_valid, error = self._validate()
        if not is_valid:
            return False, error

        update_data = self.data.copy()
        update_data["updated_at"] = datetime.now()

        # 1. Actualizar la financiera en la DB (función de modelo asumida)
        try:
            # Asume que 'update_one' actualiza por ObjectId
            success = Financiera.update_one(ObjectId(self.financiera_id), update_data)
            if success:
                return True, None
            else:
                return False, "No se pudo actualizar la financiera."
        except Exception as e:
            return False, f"Error de base de datos al actualizar: {e}"