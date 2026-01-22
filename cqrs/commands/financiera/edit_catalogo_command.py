from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
from typing import Dict, Any

class EditCatalogoCommand:
    def __init__(self, catalogo_id: str, data: Dict[str, Any], session_data: Dict[str, Any]):
        self.catalogo_id = catalogo_id
        self.data = data
        self.session_data = session_data

    def execute(self) -> Dict[str, int]:
        """
        Actualiza un elemento de catálogo por su ID.
        Retorna el número de documentos modificados.
        """
        try:
            object_id = ObjectId(self.catalogo_id)
        except:
            raise ValueError("ID inválido")

        # 1. Preparar datos (solo actualiza los campos permitidos y convierte tipos)
        update_fields = {
            "nombre": str(self.data.get("nombre")).strip(),
            "descripcion": str(self.data.get("descripcion", "")).strip(),
            "valor": str(self.data.get("valor", "")).strip(),
            "orden": int(self.data.get("orden", 0)),
            "activo": str(self.data.get("activo")).lower() == "true" if isinstance(self.data.get("activo"), str) else bool(self.data.get("activo", True)),
            "icono": str(self.data.get("icono", "")).strip(),
            "color": str(self.data.get("color", "#000000")).strip(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Eliminar campos que no deben cambiarse (ej. tipo o catalogo_id) si vinieran en el payload
        update_fields = {k: v for k, v in update_fields.items() if k != "tipo"}

        # 2. Ejecutar la actualización
        result = db.catalogos.update_one({"_id": object_id}, {"$set": update_fields})

        # 3. Registrar Auditoría
        if result.matched_count > 0:
            db.auditoria.insert_one({
                "usuario_id": self.session_data.get("usuario_id"),
                "usuario_nombre": self.session_data.get("usuario_nombre"),
                "accion": "Actualización de catálogo",
                "modulo": "catalogos",
                "detalles": {"catalogo_id": self.catalogo_id, "actualizacion": update_fields},
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return {"matched_count": result.matched_count}