from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
from typing import Dict, Any

class DeleteCatalogoCommand:
    def __init__(self, catalogo_id: str, session_data: Dict[str, Any]):
        self.catalogo_id = catalogo_id
        self.session_data = session_data

    def execute(self):
        """
        Elimina un elemento de catálogo por su ID y registra la auditoría.
        """
        try:
            object_id = ObjectId(self.catalogo_id)
        except:
            raise ValueError("ID inválido")
            
        # 1. Obtener info antes de eliminar para auditoría
        catalogo = db.catalogos.find_one({"_id": object_id})
        
        # 2. Eliminar de la DB
        result = db.catalogos.delete_one({"_id": object_id})
        
        # 3. Registrar Auditoría
        if catalogo and result.deleted_count > 0:
            db.auditoria.insert_one({
                "usuario_id": self.session_data.get("usuario_id"),
                "usuario_nombre": self.session_data.get("usuario_nombre"),
                "accion": "Eliminación de catálogo",
                "modulo": "catalogos",
                "detalles": {"tipo": catalogo.get("tipo"), "nombre": catalogo.get("nombre"), "_id": self.catalogo_id},
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        if result.deleted_count == 0:
            raise ValueError("Catálogo no encontrado o no se pudo eliminar.")