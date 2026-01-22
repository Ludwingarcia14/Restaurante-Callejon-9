from config.db import db
from bson.objectid import ObjectId

class GetAsesorQueries:
    @staticmethod
    def get_user_by_id(usuario_id_str: str) -> dict:
        """Busca el documento de usuario (asesor) por _id (ObjectId)."""
        try:
            usuario_obj_id = ObjectId(usuario_id_str)
            return db["usuarios"].find_one({"_id": usuario_obj_id})
        except Exception:
            return None

    @staticmethod
    def get_asesor_by_usuario_id(usuario_id: str) -> dict:
        """Busca el documento de asesor por 'usuario_id' (string)."""
        return db["asesores"].find_one({"usuario_id": usuario_id})

    @staticmethod
    def get_asesor_tasks(asesor_id_str: str) -> list:
        """Obtiene las últimas 50 tareas de un asesor."""
        return list(
            db["asesor_tasks"]
            .find({"asesor_id": asesor_id_str})
            .sort("created_at", -1)
            .limit(50)
        )
    
    @staticmethod
    def get_user_by_id_or_usuario_id(usuario_id: str) -> dict:
        """
        Busca el documento de usuario, primero por 'usuario_id' (string) 
        y luego intenta por '_id' (ObjectId) como fallback.
        """
        # 1. Intentar buscar por el campo 'usuario_id' (como string)
        usuario = db["usuarios"].find_one({"usuario_id": usuario_id})
        
        if not usuario:
            # 2. Si no se encuentra, intentar buscar por el campo '_id' (como ObjectId)
            try:
                usuario = db["usuarios"].find_one({"_id": ObjectId(usuario_id)})
            except Exception:
                # El string de entrada no pudo convertirse a ObjectId, se ignora.
                pass
        
        return usuario