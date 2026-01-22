from config.db import db
from datetime import datetime
import uuid
from typing import Dict, Any

class CreateCatalogoCommand:
    def __init__(self, data: Dict[str, Any], session_data: Dict[str, Any]):
        self.data = data
        self.session_data = session_data

    def execute(self) -> Dict[str, str]:
        """
        Crea un nuevo elemento de catálogo en la colección 'catalogos' y registra la auditoría.
        Retorna el ID del catálogo creado.
        """
        # 1. Validar campos obligatorios
        if not self.data.get("tipo") or not self.data.get("nombre"):
            raise ValueError("Tipo y nombre son obligatorios")
        
        # 2. Construir el documento
        catalogo = {
            "catalogo_id": str(uuid.uuid4()),
            "tipo": str(self.data.get("tipo")).strip(),
            "nombre": str(self.data.get("nombre")).strip(),
            "descripcion": str(self.data.get("descripcion", "")).strip(),
            # Asegurar conversión a enteros si el valor existe
            "orden": int(self.data.get("orden", 0)) if self.data.get("orden") not in [None, ""] else 0,
            "valor": str(self.data.get("valor", "")).strip(),
            # Manejar booleano o string 'true'/'false'
            "activo": str(self.data.get("activo")).lower() == "true" if isinstance(self.data.get("activo"), str) else bool(self.data.get("activo", True)),
            "icono": str(self.data.get("icono", "")).strip(),
            "color": str(self.data.get("color", "#000000")).strip(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 3. Guardar en la DB y registrar Auditoría
        db.catalogos.insert_one(catalogo)
        
        db.auditoria.insert_one({
            "usuario_id": self.session_data.get("usuario_id"),
            "usuario_nombre": self.session_data.get("usuario_nombre"),
            "accion": "Creación de catálogo",
            "modulo": "catalogos",
            "detalles": {"tipo": catalogo["tipo"], "nombre": catalogo["nombre"]},
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return {"catalogo_id": catalogo["catalogo_id"]}