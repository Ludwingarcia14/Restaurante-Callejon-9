from config.db import db
from bson.objectid import ObjectId
from typing import Dict, Any, Optional

class GetCatalogoQueries:
    @staticmethod
    def get_catalogos_for_datatable(start: int, length: int, search_value: str, tipo_filtro: str) -> Dict[str, Any]:
        """
        Obtiene datos de catálogos con paginación y filtros para la interfaz DataTables.
        """
        
        query = {}
        
        if tipo_filtro:
            query["tipo"] = tipo_filtro
            
        if search_value:
            query["$or"] = [
                {"nombre": {"$regex": search_value, "$options": "i"}},
                {"descripcion": {"$regex": search_value, "$options": "i"}},
                {"tipo": {"$regex": search_value, "$options": "i"}}
            ]

        total_records = db.catalogos.count_documents({})
        total_filtered = db.catalogos.count_documents(query)

        cursor = db.catalogos.find(query).skip(start).limit(length).sort("orden", 1)
        data = []
        for item in cursor:
            # Serializar ObjectId a string
            item["_id"] = str(item["_id"])
            data.append(item)

        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }

    @staticmethod
    def view_catalogo_by_id(catalogo_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de un catálogo específico por su ID de MongoDB (_id).
        """
        try:
            object_id = ObjectId(catalogo_id)
        except:
            return None

        catalogo = db.catalogos.find_one({"_id": object_id})

        if catalogo:
            # Serializar ObjectId a string
            catalogo["_id"] = str(catalogo["_id"])
            return catalogo
        return None