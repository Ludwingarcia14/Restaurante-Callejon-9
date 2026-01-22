from config.db import db
from typing import Dict, Any, Optional, List
from bson.objectid import ObjectId
from datetime import datetime

class GetPrestamosQueryHandler:
    """Manejador de consultas para obtener listas de préstamos."""
    
    def handle(self, financiera_id: Optional[str], start: int, length: int, search_value: str) -> Dict[str, Any]:
        """Ejecuta la consulta principal de préstamos para DataTables."""
        
        # Filtro base: No eliminados Y que pertenezcan a la financiera del usuario
        query = {"deleted_at": None}
        
        # Asegurarse de que solo se consultan préstamos de la financiera asignada
        if financiera_id:
            # Asume que 'financiera_id' en la colección 'prestamos' es un string
            query["financiera_id"] = financiera_id 
        
        if search_value:
            query["$or"] = [
                {"datbasicos_clave": {"$regex": search_value, "$options": "i"}},
                {"prestamo_motivo": {"$regex": search_value, "$options": "i"}},
                {"prestamo_estado": {"$regex": search_value, "$options": "i"}}
            ]

        # Conteo total y filtrado
        total_records = db.prestamos.count_documents({"deleted_at": None, "financiera_id": financiera_id})
        total_filtered = db.prestamos.count_documents(query)
        
        cursor = db.prestamos.find(query).skip(start).limit(length).sort("created_at", -1)
        data = []
        
        # Optimizamos buscando todos los clientes en una sola pasada
        cliente_ids = [p.get("cliente_id") for p in cursor if p.get("cliente_id")]
        
        # Volvemos a consultar para obtener la lista completa y resolver el nombre del cliente
        cursor.rewind() 
        
        # Mapear nombres de clientes
        cliente_map = {
            c["_id"]: f"{c.get('cliente_nombre', '')} {c.get('cliente_apellidos', '')}".strip() 
            for c in db.clientes.find({"_id": {"$in": cliente_ids}}, {"cliente_nombre": 1, "cliente_apellidos": 1})
        }

        for p in cursor:
            # Resolver nombre del cliente
            nombre_cliente = cliente_map.get(p.get("cliente_id"), "Desconocido")

            # Formateo de fechas
            fecha_solicitud = p.get("prestamo_fecha_solicitud")
            if isinstance(fecha_solicitud, datetime):
                fecha_solicitud = fecha_solicitud.strftime("%Y-%m-%d")

            data.append({
                "_id": str(p["_id"]),
                "clave": p.get("datbasicos_clave", "S/N"),
                "cliente": nombre_cliente,
                "monto": f"${p.get('prestamo_monto', 0):,.2f}",
                "plazo": f"{p.get('prestamo_plazo', 0)} meses",
                "interes": f"{p.get('prestamo_tasa_interes', 0)}%",
                "estado": p.get("prestamo_estado", "Pendiente"),
                "fecha": fecha_solicitud
            })

        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }