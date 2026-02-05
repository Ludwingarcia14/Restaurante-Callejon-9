"""
Query para obtener los detalles de un usuario por su ObjectId.
"""
from config.db import db
from bson.objectid import ObjectId

class GetUserDetailsQuery:
    """
    Recupera un único documento de la colección 'usuarios' por su _id.
    """
    @staticmethod
    def execute(usuario_id):
        """
        Ejecuta la consulta para obtener los detalles de un usuario.

        Args:
            usuario_id (str): El ID de MongoDB (ObjectId) del usuario.

        Returns:
            tuple: (dict de usuario, error)
        """
        try:
            # Intentar convertir la cadena de ID a ObjectId
            object_id = ObjectId(usuario_id)
        except Exception:
            return None, "ID de usuario inválido."

        try:
            # Buscar el usuario por el ObjectId
            usuario = db.usuarios.find_one({"_id": object_id})
            
            if usuario:
                # Limpiar el objeto para JSON serializable: convertir _id a string
                usuario["_id"] = str(usuario["_id"])
                
                # Asegurar que cualquier otro ID de tipo ObjectId (si existe) también se convierta
                if 'usuario_id' in usuario and isinstance(usuario['usuario_id'], ObjectId):
                    usuario["usuario_id"] = str(usuario["usuario_id"])
                    
                return usuario, None
            else:
                return None, "Usuario no encontrado."
        except Exception as e:
            # Capturar cualquier error de base de datos
            return None, str(e)