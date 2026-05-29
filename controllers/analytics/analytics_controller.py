from flask import jsonify, render_template, session
from config.db import db
from datetime import datetime, timedelta
from controllers.auth.AuthController import login_required, rol_required


class AnalyticsController:

    # VISTA PRINCIPAL

    @staticmethod
    @login_required
    @rol_required(['1'])
    def index():
        """Renderiza el dashboard de analytics"""
        usuario = {
            "nombre": session.get("usuario_nombre", "Admin"),
            "rol": session.get("usuario_rol"),
            "id": session.get("usuario_id")
        }
        return render_template("admin/analytics/analytics.html", usuario=usuario)

    # KPIs GENERALES

    @staticmethod
    def get_kpis():
        """MapReduce: KPIs generales del negocio"""
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            semana = hoy - timedelta(days=7)
            mes = hoy - timedelta(days=30)

            # Ventas de hoy
            ventas_hoy = list(db.ventas.aggregate([
                {"$match": {"fecha_creacion": {"$gte": hoy}}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
            ]))

            # Ventas de la semana
            ventas_semana = list(db.ventas.aggregate([
                {"$match": {"fecha_creacion": {"$gte": semana}}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
            ]))

            # Ventas del mes
            ventas_mes = list(db.ventas.aggregate([
                {"$match": {"fecha_creacion": {"$gte": mes}}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
            ]))

            total_mes = float(ventas_mes[0]["total"]) if ventas_mes else 0
            count_mes = int(ventas_mes[0]["count"]) if ventas_mes else 0
            ticket_promedio = total_mes / count_mes if count_mes > 0 else 0

            mesas_ocupadas = db.mesas.count_documents({"estado": "ocupada"})
            total_mesas = db.mesas.count_documents({})

            # Propinas del mes
            propinas_mes = list(db.ventas.aggregate([
                {"$match": {"fecha_creacion": {"$gte": mes}}},
                {"$group": {"_id": None, "total_propinas": {"$sum": "$propina"}}}
            ]))
            total_propinas = float(propinas_mes[0]["total_propinas"]) if propinas_mes else 0

            return jsonify({
                "ventas_hoy": float(ventas_hoy[0]["total"]) if ventas_hoy else 0,
                "transacciones_hoy": int(ventas_hoy[0]["count"]) if ventas_hoy else 0,
                "ventas_semana": float(ventas_semana[0]["total"]) if ventas_semana else 0,
                "ventas_mes": total_mes,
                "transacciones_mes": count_mes,
                "ticket_promedio": round(ticket_promedio, 2),
                "propinas_mes": round(total_propinas, 2),
                "mesas_ocupadas": mesas_ocupadas,
                "total_mesas": total_mesas,
                "ocupacion_pct": round((mesas_ocupadas / total_mesas * 100) if total_mesas > 0 else 0, 1)
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # TOP PLATILLOS

    @staticmethod
    def get_top_platillos():
        """
        MapReduce: TOP 10 platillos más vendidos por ingreso y cantidad.
        MAP → $unwind descompone cada elemento del array platillos.
        REDUCE → $group agrupa por nombre y suma subtotal + cantidad.
        """
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            fecha_inicio = datetime.now() - timedelta(days=30)

            pipeline = [
                {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
                # MAP: un documento por cada item vendido
                {"$unwind": "$items"},
                {"$match": {"items.nombre": {"$exists": True, "$ne": None}}},
                # REDUCE: agrupar por nombre del item
                {"$group": {
                    "_id": "$items.nombre",
                    "total_ingreso": {"$sum": {"$multiply": ["$items.precio", "$items.cantidad"]}},
                    "total_cantidad": {"$sum": "$items.cantidad"},
                    "precio_unitario_prom": {"$avg": "$items.precio"},
                    "num_ventas": {"$sum": 1}
                }},
                {"$sort": {"total_ingreso": -1}},
                {"$limit": 10},
                {"$project": {
                    "platillo": "$_id",
                    "total_ingreso": {"$round": ["$total_ingreso", 2]},
                    "total_cantidad": 1,
                    "precio_unitario_prom": {"$round": ["$precio_unitario_prom", 2]},
                    "num_ventas": 1,
                    "_id": 0
                }}
            ]

            resultado = list(db.ventas.aggregate(pipeline))
            return jsonify({"data": resultado, "periodo_dias": 30})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # VENTAS POR DÍA 

    @staticmethod
    def get_ventas_por_dia():
        """MapReduce: Tendencia de ventas diarias usando campo 'fecha'"""
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            fecha_inicio = datetime.now() - timedelta(days=30)

            pipeline = [
                {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$fecha_creacion"},
                        "month": {"$month": "$fecha_creacion"},
                        "day": {"$dayOfMonth": "$fecha_creacion"}
                    },
                    "total": {"$sum": "$total"},
                    "transacciones": {"$sum": 1},
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
                {"$project": {
                    "fecha": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {
                                "$dateFromParts": {
                                    "year": "$_id.year",
                                    "month": "$_id.month",
                                    "day": "$_id.day"
                                }
                            }
                        }
                    },
                    "total": {"$round": ["$total", 2]},
                    "transacciones": 1,
                    "_id": 0
                }}
            ]

            resultado = list(db.ventas.aggregate(pipeline))
            return jsonify({"data": resultado})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # VENTAS POR MÉTODO DE PAGO

    @staticmethod
    def get_ventas_por_metodo_pago():
        """MapReduce: Distribución por método de pago"""
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            fecha_inicio = datetime.now() - timedelta(days=30)

            pipeline = [
                {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
                {"$group": {
                    "_id": "$metodo_pago",
                    "total": {"$sum": "$total"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"total": -1}},
                {"$project": {
                    "metodo": "$_id",
                    "total": {"$round": ["$total", 2]},
                    "count": 1,
                    "_id": 0
                }}
            ]

            resultado = list(db.ventas.aggregate(pipeline))
            return jsonify({"data": resultado})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ==============================
    # HORAS PICO
    # ==============================

    @staticmethod
    def get_horas_pico():
        """MapReduce: Distribución de ventas por hora del día usando campo 'fecha'"""
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            fecha_inicio = datetime.now() - timedelta(days=30)

            pipeline = [
                {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
                {"$group": {
                    "_id": {"$hour": "$fecha_creacion"},
                    "total": {"$sum": "$total"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}},
                {"$project": {
                    "hora": "$_id",
                    "total": {"$round": ["$total", 2]},
                    "count": 1,
                    "_id": 0
                }}
            ]

            resultado = list(db.ventas.aggregate(pipeline))
            return jsonify({"data": resultado})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # RENDIMIENTO POR MESERO

    @staticmethod
    def get_rendimiento_meseros():
        """MapReduce: Ventas, ticket promedio y propinas por mesero"""
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            fecha_inicio = datetime.now() - timedelta(days=30)

            pipeline = [
                {"$match": {
                    "fecha_creacion": {"$gte": fecha_inicio},
                    "mesero_nombre": {"$exists": True, "$ne": ""}
                }},
                {"$group": {
                    "_id": "$mesero_nombre",
                    "total_ventas": {"$sum": "$total"},
                    "num_ventas": {"$sum": 1},
                    "propinas": {"$sum": "$propina"},
                    "comensales_atendidos": {"$sum": 0}
                }},
                {"$sort": {"total_ventas": -1}},
                {"$limit": 10},
                {"$project": {
                    "mesero": "$_id",
                    "total_ventas": {"$round": ["$total_ventas", 2]},
                    "num_ventas": 1,
                    "propinas": {"$round": ["$propinas", 2]},
                    "comensales_atendidos": 1,
                    "ticket_promedio": {
                        "$round": [{"$divide": ["$total_ventas", "$num_ventas"]}, 2]
                    },
                    "_id": 0
                }}
            ]

            resultado = list(db.ventas.aggregate(pipeline))
            return jsonify({"data": resultado})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # PLATILLOS POR MESA (promedio de consumo)

    @staticmethod
    def get_ventas_por_mesa():
        """MapReduce: Consumo promedio por número de mesa"""
        try:
            if session.get("usuario_rol") != "1":
                return jsonify({"error": "No autorizado"}), 403

            fecha_inicio = datetime.now() - timedelta(days=30)

            pipeline = [
                {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
                {"$group": {
                    "_id": "$mesa_numero",
                    "total_ventas": {"$sum": "$total"},
                    "num_visitas": {"$sum": 1},
                    "comensales_total": {"$sum": 0},
                    "ticket_promedio": {"$avg": "$total"}
                }},
                {"$sort": {"total_ventas": -1}},
                {"$limit": 15},
                {"$project": {
                    "mesa": "$_id",
                    "total_ventas": {"$round": ["$total_ventas", 2]},
                    "num_visitas": 1,
                    "comensales_total": 1,
                    "ticket_promedio": {"$round": ["$ticket_promedio", 2]},
                    "_id": 0
                }}
            ]

            resultado = list(db.ventas.aggregate(pipeline))
            return jsonify({"data": resultado})

        except Exception as e:
            return jsonify({"error": str(e)}), 500
