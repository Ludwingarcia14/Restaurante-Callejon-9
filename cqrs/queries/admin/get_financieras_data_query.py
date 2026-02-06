"""
Query para obtener el listado de financieras para DataTables.
"""
from config.db import db

class GetFinancierasDataQuery:
    """
    Recupera un conjunto paginado y filtrado de financieras.
    """
    @staticmethod
    def execute(draw, start, length, search_value):
        """
        Ejecuta la consulta con paginación, búsqueda y proyección.

        Returns:
            tuple: (dict de DataTables, error)
        """
        try:
            query = {}
            if search_value:
                query = {
                    "$or": [
                        {"financiera_nombre": {"$regex": search_value, "$options": "i"}},
                        {"financiera_correo": {"$regex": search_value, "$options": "i"}},
                        {"financiera_NContrato": {"$regex": search_value, "$options": "i"}},
                        {"financiera_ProductoOfrecido": {"$regex": search_value, "$options": "i"}}
                    ]
                }

            projection = {
                "_id": 1,
                "financiera_nombre": 1,
                "financiera_correo": 1,
                "financiera_NContrato": 1,
                "financiera_ProductoOfrecido": 1
            }

            total_records = db.financieras.count_documents({})
            total_filtered = db.financieras.count_documents(query)

            cursor = db.financieras.find(query, projection).skip(start).limit(length)
            data = []
            for f in cursor:
                f["_id"] = str(f["_id"]) # Convertir ObjectId a string
                data.append(f)

            return {
                "draw": draw,
                "recordsTotal": total_records,
                "recordsFiltered": total_filtered,
                "data": data
            }, None
        
        except Exception as e:
            return None, str(e)