from flask import jsonify, session, request
from datetime import datetime, time
from config.db import db
from bson import ObjectId
class HistorialController:

    @staticmethod
    def historial_mesero():
        """Obtiene el historial de comandas del mesero"""
        mesero_id = session.get("usuario_id")
        
        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        
        try:
            mesero_oid = ObjectId(mesero_id)
            
            # Obtener parámetros de fecha (opcional)
            fecha_inicio = request.args.get("fecha_inicio")
            fecha_fin = request.args.get("fecha_fin")
            
            filtro = {
                "mesero_id": mesero_oid,
                "estado": {"$in": ["pagada", "cerrada"]}  # 🔥 Ambos estados
            }
            
            if fecha_inicio and fecha_fin:
                filtro["fecha_cierre"] = {
                    "$gte": datetime.fromisoformat(fecha_inicio),
                    "$lte": datetime.fromisoformat(fecha_fin)
                }
            
            # Obtener comandas cerradas
            comandas = list(db.comandas.find(filtro).sort("fecha_cierre", -1).limit(100))
            
            # Formatear para el frontend
            historial = []
            for c in comandas:
                historial.append({
                    "id": str(c["_id"]),
                    "folio": c.get("folio"),
                    "mesa": c.get("mesa_numero"),
                    "total": float(c.get("total", 0)),
                    "propina": float(c.get("propina", 0)),
                    "total_final": float(c.get("total_final", c.get("total", 0))),
                    "metodo_pago": c.get("metodo_pago", "efectivo"),
                    "fecha_cierre": c.get("fecha_cierre").isoformat() if c.get("fecha_cierre") else None,
                    "num_comensales": c.get("num_comensales", 0),
                    "items": len(c.get("items", []))
                })
            
            return jsonify({
                "success": True,
                "historial": historial,
                "total_registros": len(historial)
            })
            
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500