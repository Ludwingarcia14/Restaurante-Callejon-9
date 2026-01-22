from config.db import db
from bson.objectid import ObjectId
from typing import Optional, Dict

class GetClientQueries:
    @staticmethod
    def get_client_by_id(id_cliente: str) -> dict:
        """Obtiene un cliente por su _id."""
        try:
            cliente_obj_id = ObjectId(id_cliente)
            return db["clientes"].find_one({"_id": cliente_obj_id})
        except Exception:
            return None

    @staticmethod
    def get_asesor_clients(usuario_obj_id: ObjectId) -> list:
        """Obtiene la lista de clientes asignados a un asesor mediante agregación."""
        pipeline = [
            {"$match": {"asesor_id": usuario_obj_id}},
            {"$lookup": {"from": "clientes", "localField": "cliente_id", "foreignField": "_id", "as": "cliente_info"}},
            {"$unwind": "$cliente_info"},
            {"$replaceRoot": {"newRoot": "$cliente_info"}}
        ]
        return list(db.asesor_asignado.aggregate(pipeline))

# ------------------------------------------------------------
    # DOCUMENTOS DEL CLIENTE - MÉTODO UNIFICADO
    # ------------------------------------------------------------
    @staticmethod
    def get_client_all_documents(cliente_obj_id: ObjectId) -> Dict[str, Optional[Dict]]:
        """
        Obtiene los sub-documentos de 'documentos' para Persona Física y Persona Moral 
        en una sola llamada.
        
        Retorna un diccionario con las claves 'docs_fisica' y 'docs_moral'.
        """
        
                   # Obtener documentos FISICA
        docs_fisica_raw = db["documentofisica"].find_one({"usuario_id": cliente_obj_id})
        docs_fisica = docs_fisica_raw.get("documentos", {}) if docs_fisica_raw else None

            # Obtener documentos MORAL
        docs_moral_raw = db["documentomoral"].find_one({"usuario_id": cliente_obj_id})
        docs_moral = docs_moral_raw.get("documentos", {}) if docs_moral_raw else None
        
        # 5. Devolver el resultado unificado
        return {
            "docs_fisica": docs_fisica,
            "docs_moral": docs_moral
        }