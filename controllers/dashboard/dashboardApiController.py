"""
API Controller para Dashboard de Administración
Endpoints del dashboard admin
"""

from flask import jsonify, session
from config.db import db
from datetime import datetime


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
    # PERSONAL ACTIVO (ONLINE)
    # ==============================

    @staticmethod
    def get_personal_activo():

        if session.get("usuario_rol") != "1":
            return jsonify({"error": "No autorizado"}), 403

        personal = list(db.usuarios.find({
            "usuario_rol": {"$in": ["1","2","3","4"]},
            "usuario_status": 1
        }).sort("usuario_nombre", 1))

        resultado = []

        for p in personal:
            resultado.append({
                "nombre": f"{p.get('usuario_nombre','')} {p.get('usuario_apellidos','')}".strip(),
                "rol": p.get("usuario_rol",""),
                "email": p.get("usuario_email",""),
                "ultimaActividad": "Hace 1 min"
            })

        return jsonify(resultado)


    # ==============================
    # TODOS LOS EMPLEADOS
    # ==============================

    @staticmethod
    def get_todos_empleados():

        if session.get("usuario_rol") != "1":
            return jsonify({"error": "No autorizado"}), 403

        empleados = list(db.usuarios.find(
            {"usuario_rol": {"$in": ["1","2","3","4"]}},
            {"usuario_clave": 0}
        ).sort("usuario_nombre", 1))

        resultado = []

        for e in empleados:
            resultado.append({
                "id": str(e["_id"]),
                "nombre": f"{e.get('usuario_nombre','')} {e.get('usuario_apellidos','')}".strip(),
                "email": e.get("usuario_email",""),
                "rol": e.get("usuario_rol",""),
                "status": e.get("usuario_status",0)
            })

        return jsonify({
            "success": True,
            "data": resultado
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
