# application/commands/admin/create_financiera_command.py
from models.financiera import Financiera # Asume un modelo Financiera
from datetime import datetime

class CreateFinancieraCommand:
    def __init__(self, data: dict):
        self.data = data

    def _validate(self):
        """Realiza la validación de los datos de la financiera."""
        required_fields = ["nombre_fiscal", "nombre_comercial", "contacto_email"]
        
        for field in required_fields:
            if not self.data.get(field):
                return False, f"El campo '{field}' es obligatorio."

        # Validación de unicidad
        if Financiera.find_by_name(self.data["nombre_fiscal"]):
            return False, "Ya existe una financiera con este nombre fiscal."

        return True, None

    def execute(self):
        """Ejecuta el comando para crear la financiera."""
        is_valid, error = self._validate()
        if not is_valid:
            return False, None, error

        # 1. Preparar los datos
        new_financiera_data = {
            "nombre_fiscal": self.data["nombre_fiscal"],
            "nombre_comercial": self.data["nombre_comercial"],
            "contacto_email": self.data["contacto_email"],
            "telefono": self.data.get("telefono", None),
            "created_at": datetime.now(),
            # Otros campos por defecto...
        }
        
        # 2. Crear la financiera en la DB (función de modelo asumida)
        try:
            new_id = Financiera.create(new_financiera_data)
            return True, {"message": "Financiera creada con éxito", "id": str(new_id)}, None
        except Exception as e:
            return False, None, f"Error interno al guardar la financiera: {e}"