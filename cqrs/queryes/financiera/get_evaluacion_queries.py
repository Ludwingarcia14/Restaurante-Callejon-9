from config.db import db
from typing import Dict, Any, List
from bson.objectid import ObjectId

class GetEvaluacionQueries:
    @staticmethod
    def get_clients_for_new_evaluation(financiera_id: str) -> List[Dict[str, str]]:
        """
        Obtiene la lista de clientes asociados a esta financiera para el formulario de nueva evaluación.
        """
        
        # Asume que los clientes tienen un campo 'cliente_idFinanciera' para este filtro
        clientes_cursor = db.clientes.find(
            {"cliente_idFinanciera": financiera_id},
            {"cliente_id": 1, "cliente_nombre": 1, "cliente_apellidos": 1}
        )
        clientes = []
        for c in clientes_cursor:
            # Asegura que el ID de cliente sea un string para el formulario (select option)
            clientes.append({
                "cliente_id": str(c.get("cliente_id")),
                "nombre_completo": f"{c.get('cliente_nombre', '')} {c.get('cliente_apellidos', '')}".strip()
            })
        return clientes

    @staticmethod
    def get_evaluaciones_for_datatable(financiera_id: str, start: int, length: int, search_value: str) -> Dict[str, Any]:
        """
        Retorna los datos de evaluaciones para la interfaz DataTables, incluyendo paginación y búsqueda.
        """
        
        # Filtro base: solo evaluaciones de esta financiera
        query = {"evaluacion_financiera_id": financiera_id}
        
        if search_value:
            # Añade el filtro de búsqueda por cliente/email/ID
            query["$or"] = [
                {"cliente_nombre": {"$regex": search_value, "$options": "i"}},
                {"cliente_email": {"$regex": search_value, "$options": "i"}},
                {"evaluacion_id": {"$regex": search_value, "$options": "i"}}
            ]

        # Conteo total y filtrado
        total_records = db.evaluaciones_credito.count_documents({"evaluacion_financiera_id": financiera_id})
        total_filtered = db.evaluaciones_credito.count_documents(query)

        projection = {
            "evaluacion_id": 1,
            "cliente_nombre": 1,
            "cliente_email": 1,
            "evaluacion_monto_solicitado": 1,
            "evaluacion_plazo_meses": 1,
            "evaluacion_calificacion_riesgo": 1,
            "evaluacion_recomendacion": 1,
            "evaluacion_status": 1,
            "created_at": 1
        }

        # Consulta con paginación y ordenamiento
        cursor = db.evaluaciones_credito.find(query, projection).skip(start).limit(length).sort("created_at", -1)
        data = []
        for e in cursor:
            if "_id" in e:
                # El ID de MongoDB es necesario para acciones de edición/detalle
                e["_id"] = str(e["_id"])
            data.append(e)

        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }