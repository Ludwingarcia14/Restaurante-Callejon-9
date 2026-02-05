"""
Query para obtener la lista de roles disponibles para la creación de usuarios.
(Usado en create_admin y crear_cliente)
"""
from config.db import db
from bson.objectid import ObjectId

class GetRolesForCreationQuery:
    """
    Recupera los roles de la colección 'roles'.
    """
    @staticmethod
    def execute():
        """
        Ejecuta la consulta de roles.

        Returns:
            tuple: (lista de roles, error)
        """
        try:
            roles_cursor = db.roles.find()
            roles = []
            for r in roles_cursor:
                roles.append({
                    # Convertir el ID de rol a string si no lo es
                    "Rol_id": str(r.get("Rol_id", "")), 
                    "Rol_nombre": r.get("Rol_nombre", "Sin nombre")
                })
            return roles, None
        except Exception as e:
            return None, str(e)