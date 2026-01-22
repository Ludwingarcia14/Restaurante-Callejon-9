# cqrs/queries/get_prestamos_query.py
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class GetPrestamosQueryHandler:
    def handle(self, financiera_id, start, length, search_value):
        # -----------------------------------------------------------------
        # PASO 3 (Movido desde el controlador): Consultar Préstamos
        # -----------------------------------------------------------------
        
        # Filtro base: No eliminados Y que pertenezcan a la financiera
        # Nota: financiera_id puede llegar como None, String u ObjectId, asegúrate de manejarlo consistente.
        query = {
            "deleted_at": None,
            "financiera_id": financiera_id 
        }

        # Filtros de búsqueda del DataTables
        if search_value:
            query["$or"] = [
                {"datbasicos_clave": {"$regex": search_value, "$options": "i"}},
                {"prestamo_motivo": {"$regex": search_value, "$options": "i"}},
                {"prestamo_estado": {"$regex": search_value, "$options": "i"}}
            ]

        # Conteos para la paginación
        total_records = db.prestamos.count_documents({
            "deleted_at": None, 
            "financiera_id": financiera_id
        })
        
        total_filtered = db.prestamos.count_documents(query)
        
        # Consulta final con paginación
        cursor = db.prestamos.find(query).skip(start).limit(length).sort("created_at", -1)

        data = []
        for p in cursor:
            # Resolver nombre del cliente
            nombre_cliente = "Desconocido"
            if "cliente_id" in p:
                try:
                    c = db.clientes.find_one({"_id": p["cliente_id"]})
                    if c:
                        nombre_cliente = f"{c.get('cliente_nombre', '')} {c.get('cliente_apellidos', '')}"
                except:
                    pass

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

        # Retornamos un diccionario simple con los datos listos
        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }