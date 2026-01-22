# cqrs/commands/handlers/notificacion_leida_handler.py

from bson import ObjectId

class MarcarLeidasCommandHandler:
    @staticmethod
    def handle(id_usuario_str: str, Notificacion_Model):
        """
        Maneja el comando de marcar todas las notificaciones como leídas.
        Notificacion_Model es el modelo (ORM/ODM) inyectado.
        """
        
        try:
            id_usuario = ObjectId(id_usuario_str)
        except:
            # Manejar el caso de que el ID no sea un ObjectId válido si lo requiere Mongo
            raise ValueError("ID de usuario inválido.")

        # Operación de Escritura
        result = Notificacion_Model.update_many(
            {"id_usuario": id_usuario, "leida": False}, # Solo actualiza las no leídas
            {"$set": {"leida": True}}
        )

        return {"ok": True, "msg": f"Se marcaron {result.modified_count} notificaciones como leídas."}