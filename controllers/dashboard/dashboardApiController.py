"""
API Controller para Dashboard de Administración
Endpoints del dashboard admin
"""

from flask import jsonify, session, request
from config.db import db
from datetime import datetime
from utils.pagination import get_pagination_params, paginate_response


class DashboardAPIController:

    # ==============================
    # KPIs GENERALES
    # ==============================

    @staticmethod
    def get_stats():

        if session.get("usuario_rol") != "1":
            return jsonify({"error": "No autorizado"}), 403

        hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        total_empleados = db.usuarios.count_documents({"usuario_rol": {"$in": ["1","2","3","4"]}})

        empleados_activos = db.usuarios.count_documents({
            "usuario_rol": {"$in": ["1","2","3","4"]},
            "usuario_status": 1
        })

        ventas = list(db.ventas.aggregate([
            {"$match": {"fecha": {"$gte": hoy_inicio}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}}}
        ]))

        ventas_dia = float(ventas[0]["total"]) if ventas else 0

        return jsonify({
            "total_empleados": total_empleados,
            "empleados_activos": empleados_activos,
            "total_admin": db.usuarios.count_documents({"usuario_rol": "1"}),
            "total_meseros": db.usuarios.count_documents({"usuario_rol": "2"}),
            "total_cocina": db.usuarios.count_documents({"usuario_rol": "3"}),
            "total_inventario": db.usuarios.count_documents({"usuario_rol": "4"}),
            "mesas_ocupadas": db.mesas.count_documents({"estado": "ocupada"}),
            "comandas_activas": db.comandas.count_documents({"estado": {"$in": ["nueva","en_cocina","preparando"]}}),
            "ventas_dia": ventas_dia,
            "en_cocina": db.comandas.count_documents({"estado": "en_cocina"})
        })


    # ==============================
    # PERSONAL ACTIVO (ONLINE) - CONEXION REAL
    # ==============================

    @staticmethod
    def get_personal_activo():

        if session.get("usuario_rol") != "1":
            return jsonify({"error": "No autorizado"}), 403

        from datetime import datetime
        
        # Ahora filtramos por fecha_conexion (timestamp real de conexión)
        # Un usuario está conectado si tiene fecha_conexion diferente de None
        personal = list(db.usuarios.find({
            "usuario_rol": {"$in": ["1","2","3","4"]},
            "fecha_conexion": {"$ne": None}
        }).sort("usuario_nombre", 1))

        resultado = []

        for p in personal:
            fecha_conexion = p.get("fecha_conexion")
            tiempo_conectado = ""
            
            if fecha_conexion:
                if isinstance(fecha_conexion, str):
                    try:
                        fecha_conexion = datetime.fromisoformat(fecha_conexion.replace('Z', '+00:00'))
                    except:
                        fecha_conexion = None
                
                if fecha_conexion:
                    # Calcular tiempo conectado
                    ahora = datetime.utcnow()
                    delta = ahora - fecha_conexion
                    
                    if delta.days > 0:
                        tiempo_conectado = f"{delta.days}d {delta.seconds // 3600}h"
                    elif delta.seconds >= 3600:
                        tiempo_conectado = f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
                    elif delta.seconds >= 60:
                        tiempo_conectado = f"{delta.seconds // 60}m"
                    else:
                        tiempo_conectado = f"{delta.seconds}s"
            
            resultado.append({
                "nombre": f"{p.get('usuario_nombre','')} {p.get('usuario_apellidos','')}".strip(),
                "rol": p.get("usuario_rol",""),
                "email": p.get("usuario_email",""),
                "tiempo_conectado": tiempo_conectado,
                "fecha_conexion": fecha_conexion.isoformat() if fecha_conexion and hasattr(fecha_conexion, 'isoformat') else str(fecha_conexion) if fecha_conexion else None
            })

        return jsonify(resultado)


    # ==============================
    # TODOS LOS EMPLEADOS
    # ==============================

    @staticmethod
    def get_todos_empleados():

        if session.get("usuario_rol") != "1":
            return jsonify({"error": "No autorizado"}), 403

        limit, page, skip = get_pagination_params(default_limit=50, max_limit=200)
        query = {"usuario_rol": {"$in": ["1", "2", "3", "4"]}}

        total = db.usuarios.count_documents(query)
        empleados = list(db.usuarios.find(
            query,
            {"usuario_clave": 0}
        ).sort("usuario_nombre", 1).skip(skip).limit(limit))

        resultado = [
            {
                "id": str(e["_id"]),
                "nombre": f"{e.get('usuario_nombre','')} {e.get('usuario_apellidos','')}".strip(),
                "email": e.get("usuario_email", ""),
                "rol": e.get("usuario_rol", ""),
                "status": e.get("usuario_status", 0),
            }
            for e in empleados
        ]

        return jsonify({
            "success": True,
            **paginate_response(resultado, total, page, limit),
        })


    # ==============================
    # ACTIVIDAD RECIENTE (SAFE)
    # ==============================

    @staticmethod
    def get_actividad_reciente():

        if session.get("usuario_rol") != "1":
            return jsonify([])

        try:
            actividades = list(db.actividad_reciente.find().sort("timestamp",-1).limit(10))

            for a in actividades:
                a["_id"] = str(a["_id"])
                if isinstance(a.get("timestamp"), datetime):
                    a["timestamp"] = a["timestamp"].isoformat()

            return jsonify(actividades)

        except:
            return jsonify([])

    # ==============================
    # DETALLE DE EMPLEADO
    # ==============================

    @staticmethod
    def get_empleado_detalle(empleado_id):

        if session.get("usuario_rol") != "1":
            return jsonify({"success": False, "error": "No autorizado"}), 403

        try:
            from bson import ObjectId
            empleado = db.usuarios.find_one({
                "_id": ObjectId(empleado_id),
                "usuario_rol": {"$in": ["1","2","3","4"]}
            }, {"usuario_clave": 0})

            if not empleado:
                return jsonify({"success": False, "error": "Empleado no encontrado"}), 404

            rol_nombres = {"1": "Administrador", "2": "Mesero", "3": "Cocina", "4": "Inventario"}

            return jsonify({
                "success": True,
                "empleado": {
                    "id": str(empleado["_id"]),
                    "usuario_nombre": empleado.get("usuario_nombre", ""),
                    "usuario_apellidos": empleado.get("usuario_apellidos", ""),
                    "usuario_email": empleado.get("usuario_email", ""),
                    "usuario_telefono": empleado.get("usuario_telefono", ""),
                    "rol": empleado.get("usuario_rol", ""),
                    "rol_nombre": rol_nombres.get(empleado.get("usuario_rol", ""), "Usuario"),
                    "usuario_status": empleado.get("usuario_status", 0)
                }
            })

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==============================
    # ELIMINAR EMPLEADO
    # ==============================

    @staticmethod
    def eliminar_empleado(empleado_id):

        if session.get("usuario_rol") != "1":
            return jsonify({"success": False, "error": "No autorizado"}), 403

        try:
            from bson import ObjectId

            # No permitir eliminar admins
            empleado = db.usuarios.find_one({"_id": ObjectId(empleado_id)})

            if not empleado:
                return jsonify({"success": False, "error": "Empleado no encontrado"}), 404

            if empleado.get("usuario_rol") == "1":
                return jsonify({"success": False, "error": "No se puede eliminar administradores"}), 400

            result = db.usuarios.delete_one({"_id": ObjectId(empleado_id)})

            if result.deleted_count > 0:
                return jsonify({"success": True, "message": "Empleado eliminado correctamente"})
            else:
                return jsonify({"success": False, "error": "No se pudo eliminar"}), 500

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==============================
    # ACTUALIZAR EMPLEADO
    # ==============================

    @staticmethod
    def actualizar_empleado(empleado_id):

        if session.get("usuario_rol") != "1":
            return jsonify({"success": False, "error": "No autorizado"}), 403

        try:
            from bson import ObjectId
            from flask import request

            data = request.get_json()

            empleado = db.usuarios.find_one({"_id": ObjectId(empleado_id)})

            if not empleado:
                return jsonify({"success": False, "error": "Empleado no encontrado"}), 404

            # Preparar datos para actualizar
            update_data = {}

            if 'nombre' in data:
                update_data['usuario_nombre'] = data['nombre']
            if 'apellidos' in data:
                update_data['usuario_apellidos'] = data['apellidos']
            if 'email' in data:
                update_data['usuario_email'] = data['email']
            if 'telefono' in data:
                update_data['usuario_telefono'] = data['telefono']
            if 'rol' in data:
                update_data['usuario_rol'] = data['rol']
            if 'status' in data:
                update_data['usuario_status'] = int(data['status'])

            # Si se proporciona una nueva contraseña
            if 'password' in data and data['password']:
                from services.security.password_service import PasswordService
                update_data['usuario_clave'] = PasswordService.hash_password(data['password'])

            if update_data:
                db.usuarios.update_one(
                    {"_id": ObjectId(empleado_id)},
                    {"$set": update_data}
                )

            return jsonify({"success": True, "message": "Empleado actualizado correctamente"})

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==============================
    # DESCONECTAR USUARIO (Manual)
    # ==============================

    @staticmethod
    def desconectar_usuario(empleado_id):
        """Permite a un admin desconectar manualmente a un usuario"""
        if session.get("usuario_rol") != "1":
            return jsonify({"success": False, "error": "No autorizado"}), 403

        try:
            from bson import ObjectId
            from datetime import datetime

            # Buscar y desconectar al usuario
            result = db.usuarios.update_one(
                {"_id": ObjectId(empleado_id)},
                {"$set": {
                    "usuario_tokensession": None,
                    "usuario_status": 0,
                    "fecha_conexion": None,
                    "updated_at": datetime.utcnow()
                }}
            )

            if result.modified_count > 0:
                return jsonify({
                    "success": True, 
                    "message": "Usuario desconectado correctamente"
                })
            else:
                return jsonify({
                    "success": False, 
                    "error": "No se pudo desconectar al usuario"
                }), 500

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
