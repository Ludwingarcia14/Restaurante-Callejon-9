"""
API Controller para Dashboard de Administración
Proporciona endpoints para obtener datos en tiempo real
"""
from flask import jsonify, session
from config.db import db
from datetime import datetime, timedelta
from bson import ObjectId

class DashboardAPIController:
    
    @staticmethod
    def get_stats():
        """Obtiene estadísticas generales del dashboard"""
        try:
            if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
                return jsonify({"error": "No autorizado"}), 403
            
            hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            total_empleados = db.usuarios.count_documents({"usuario_rol": {"$in": ["1", "2", "3", "4"]}})
            empleados_activos = db.usuarios.count_documents({
                "usuario_rol": {"$in": ["1", "2", "3", "4"]},
                "usuario_status": 1
            })
            
            total_mesas = db.mesas.count_documents({"activa": True})
            mesas_ocupadas = db.mesas.count_documents({"estado": "ocupada", "activa": True})
            
            comandas_activas = db.comandas.count_documents({
                "estado": {"$in": ["nueva", "en_cocina", "preparando"]}
            })
            
            comandas_listas = db.comandas.count_documents({"estado": "lista"})
            
            ventas_hoy = list(db.ventas.aggregate([
                {
                    "$match": {
                        "fecha": {"$gte": hoy_inicio}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$total"},
                        "cantidad": {"$sum": 1}
                    }
                }
            ]))
            
            ventas_dia = float(ventas_hoy[0]["total"]) if ventas_hoy else 0
            num_ventas = ventas_hoy[0]["cantidad"] if ventas_hoy else 0
            
            total_platillos = db.platillos.count_documents({"disponible": True})
            
            stats = {
                "total_empleados": total_empleados,
                "empleados_activos": empleados_activos,
                "total_admin": db.usuarios.count_documents({"usuario_rol": "1"}),
                "total_meseros": db.usuarios.count_documents({"usuario_rol": "2"}),
                "total_cocina": db.usuarios.count_documents({"usuario_rol": "3"}),
                "total_inventario": db.usuarios.count_documents({"usuario_rol": "4"}),
                "mesas_ocupadas": mesas_ocupadas,
                "mesas_disponibles": total_mesas - mesas_ocupadas,
                "comandas_activas": comandas_activas,
                "comandas_listas": comandas_listas,
                "ventas_dia": ventas_dia,
                "num_ventas": num_ventas,
                "total_platillos": total_platillos,
                "en_cocina": db.comandas.count_documents({"estado": "en_cocina"})
            }
            
            return jsonify(stats)
            
        except Exception as e:
            print(f"Error en get_stats: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    def get_actividad_reciente():
        """Obtiene las últimas actividades del sistema"""
        try:
            if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
                return jsonify({"error": "No autorizado"}), 403
            
            actividades = list(db.actividad_reciente.find().sort("timestamp", -1).limit(10))
            
            for act in actividades:
                act["_id"] = str(act["_id"])
                if "usuario_id" in act:
                    act["usuario_id"] = str(act["usuario_id"])
                if "timestamp" in act and isinstance(act["timestamp"], datetime):
                    act["timestamp"] = act["timestamp"].isoformat()
            
            return jsonify(actividades)
            
        except Exception as e:
            print(f"Error en get_actividad_reciente: {e}")
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    def get_personal_activo():
        """Obtiene lista de personal actualmente conectado"""
        try:
            if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
                return jsonify({"error": "No autorizado"}), 403
            
            personal = list(db.usuarios.find({
                "usuario_rol": {"$in": ["1", "2", "3", "4"]},
                "usuario_status": 1
            }).sort("usuario_nombre", 1))
            
            resultado = []
            for p in personal:
                resultado.append({
                    "nombre": f"{p.get('usuario_nombre', '')} {p.get('usuario_apellidos', '')}".strip(),
                    "rol": p.get("usuario_rol", ""),
                    "email": p.get("usuario_email", ""),
                    "status": "online",
                    "ultimaActividad": "Hace 1 min"
                })
            
            return jsonify(resultado)
            
        except Exception as e:
            print(f"Error en get_personal_activo: {e}")
            return jsonify({"error": str(e)}), 500