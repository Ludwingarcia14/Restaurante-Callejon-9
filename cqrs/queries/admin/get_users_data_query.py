"""
Query para obtener la lista de usuarios (Admin/Asesor/Soporte) para DataTables.
"""
from config.db import db

class GetUsersDataQuery:
    """
    Recupera un conjunto paginado y filtrado de usuarios para la interfaz de lista.
    """
    @staticmethod
    def execute(draw, start, length, search_value):
        """
        Ejecuta la consulta con paginación, búsqueda y filtros de rol.

        Args:
            draw (int): Contador de petición de DataTables.
            start (int): Índice de inicio de la paginación.
            length (int): Tamaño de página.
            search_value (str): Valor de búsqueda global.

        Returns:
            tuple: (dict de DataTables, error)
        """
        # Roles que se deben mostrar en la lista de administradores
        roles_permitidos = ["1", "2", "3", "6"]
        base_query = {"usuario_rol": {"$in": roles_permitidos}}
        query = base_query
        
        try:
            if search_value:
                # Construir la consulta de búsqueda combinada con el filtro de roles
                search_query = {
                    "$or": [
                        {"usuario_nombre": {"$regex": search_value, "$options": "i"}},
                        {"usuario_apellidos": {"$regex": search_value, "$options": "i"}},
                        {"usuario_email": {"$regex": search_value, "$options": "i"}}
                    ]
                }
                # Asegurar que se cumplan ambas condiciones: rol permitido Y búsqueda
                query = {"$and": [base_query, search_query]}

            projection = {
                "_id": 1, # Necesario para las acciones de editar/eliminar
                "usuario_nombre": 1,
                "usuario_apellidos": 1,
                "usuario_email": 1,
                "usuario_telefono": 1,
                "usuario_rol": 1,
                "usuario_status": 1,
                "created_at": 1,
                "updated_at": 1
            }

            # Contar el total de registros y los registros filtrados
            total_records = db.usuarios.count_documents(base_query)
            total_filtered = db.usuarios.count_documents(query)
            
            # Aplicar paginación y proyección a la consulta
            cursor = db.usuarios.find(query, projection).skip(start).limit(length)
            
            data = []
            for u in cursor:
                u["_id"] = str(u["_id"])
                # Mapear el rol numérico a texto para la interfaz
                u["usuario_rol_text"] = (
                    "Super Administrador" if u["usuario_rol"] == "1" else
                    "Admininistrador" if u["usuario_rol"] == "2" else
                    "Asesor" if u["usuario_rol"] == "3" else 
                    "Soporte" if u["usuario_rol"] == "6" else "Otro"
                )
                data.append(u)

            # Devolver el formato esperado por DataTables
            return {
                "draw": draw,
                "recordsTotal": total_records,
                "recordsFiltered": total_filtered,
                "data": data
            }, None
        
        except Exception as e:
            # Captura cualquier error de base de datos o lógico
            return None, str(e)