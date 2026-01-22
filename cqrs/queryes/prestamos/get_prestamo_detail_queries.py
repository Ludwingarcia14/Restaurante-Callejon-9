from config.db import db
from bson.objectid import ObjectId
from typing import Optional, Dict
from datetime import datetime

class GetPrestamoDetailQueries:
    @staticmethod
    def get_prestamo_detail(id_prestamo: str) -> Optional[Dict]:
        """Obtiene un préstamo y resuelve el nombre del cliente."""
        try:
            prestamo = db.prestamos.find_one({"_id": ObjectId(id_prestamo)})
        except Exception:
            return None
        
        if prestamo and "cliente_id" in prestamo:
            # Buscar nombre cliente
            cliente = db.clientes.find_one({"_id": prestamo["cliente_id"]})
            prestamo["cliente_nombre"] = f"{cliente.get('cliente_nombre', '')} {cliente.get('cliente_apellidos', '')}" if cliente else "Desconocido"
            
            # Formatear fechas
            if isinstance(prestamo.get("prestamo_fecha_solicitud"), datetime):
                prestamo["prestamo_fecha_solicitud"] = prestamo["prestamo_fecha_solicitud"].strftime("%Y-%m-%d")
            if isinstance(prestamo.get("prestamo_fecha_vencimiento"), datetime):
                prestamo["prestamo_fecha_vencimiento"] = prestamo["prestamo_fecha_vencimiento"].strftime("%Y-%m-%d")
                
        return prestamo