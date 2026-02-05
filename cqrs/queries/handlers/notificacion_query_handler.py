# cqrs/queries/handlers/notificacion_query_handler.py

from bson import ObjectId

class NotificacionQueryHandler:
    @staticmethod
    def get_notificaciones(id_usuario_str: str, Notificacion_Model):
        """Obtiene y formatea las notificaciones de un usuario."""
        
        try:
            query_id = ObjectId(id_usuario_str)
        except:
            raise ValueError("ID de usuario inválido.")
            
        # Operación de Lectura
        data = list(Notificacion_Model.find(
            {"id_usuario": query_id},
            {"id_usuario": 0} 
        ).sort("fecha", -1))

        # Transformación DTO/serialización
        for n in data:
            if "_id" in n:
                n["_id"] = str(n["_id"])
            if n.get("fecha"):
                 n["fecha"] = n["fecha"].isoformat()

        return data