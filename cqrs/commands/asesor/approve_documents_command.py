from config.db import db
from bson.objectid import ObjectId
from datetime import datetime

class ApproveDocumentsCommand:
    def __init__(self, cliente_id: str, es_aprobado: bool):
        self.cliente_obj_id = ObjectId(cliente_id)
        self.estatus_final = "APROBADO" if es_aprobado else "RECHAZADO"

    def execute(self) -> list:
        """Aprueba o rechaza los documentos de PF y PM."""
        mensajes_acciones = []
        fecha_revision = datetime.now() 
        
        # Bloque 1: Persona Física
        docs_fisica_raw = db["documentofisica"].find_one({"usuario_id": self.cliente_obj_id})
        if docs_fisica_raw:
            db['documentofisica'].update_one(
                { "_id": docs_fisica_raw['_id'] }, 
                { "$set": { 
                    "estatus": self.estatus_final,
                    "observaciones": f"Revisión Persona Física {self.estatus_final}.", 
                    "fecha_revision": fecha_revision 
                } }
            )
            mensajes_acciones.append(f"Física: {self.estatus_final}")
        
        # Bloque 2: Persona Moral
        docs_moral_raw = db["documentomoral"].find_one({"usuario_id": self.cliente_obj_id})
        if docs_moral_raw:
            db['documentomoral'].update_one(
                { "_id": docs_moral_raw['_id'] }, 
                { "$set": { 
                    "estatus": self.estatus_final,
                    "observaciones": f"Revisión Persona Moral {self.estatus_final}.", 
                    "fecha_revision": fecha_revision 
                } }
            )
            mensajes_acciones.append(f"Moral: {self.estatus_final}")

        return mensajes_acciones