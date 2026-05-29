"""
Módulo de Analytics usando MongoDB MapReduce
Procesa datos de ventas usando commands de MapReduce nativos de MongoDB
"""
from datetime import datetime, timedelta
from config.db import db


class SparkAnalytics:

    @staticmethod
    def _run_mapreduce(mapper, reducer, collection_name, query=None):
        """Ejecuta un comando MapReduce en MongoDB"""
        query = query or {}
        result = db[collection_name].map_reduce(
            mapper,
            reducer,
            out={"inline": 1},
            query=query
        )
        return list(result)

    @staticmethod
    def get_kpis(periodo=30):
        """MapReduce: Calcula KPIs generales del negocio"""
        try:
            now = datetime.now()
            offset_hours = 6
            hoy = (now - timedelta(hours=offset_hours)).replace(hour=0, minute=0, second=0, microsecond=0)
            semana = hoy - timedelta(days=7)
            mes = hoy - timedelta(days=periodo)

            mapper = """
            function() {
                emit(this.mesero_nombre || 'unknown', {
                    total: this.total || 0,
                    count: 1,
                    comensales: this.comensales || 0,
                    propina: this.propina || 0
                });
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { total: 0, count: 0, comensales: 0, propina: 0 };
                values.forEach(function(value) {
                    result.total += value.total;
                    result.count += value.count;
                    result.comensales += value.comensales;
                    result.propina += value.propina;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": mes}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            total_mes = 0
            count_mes = 0
            total_propinas = 0
            
            for doc in mr_result:
                total_mes += doc.get("value", {}).get("total", 0)
                count_mes += doc.get("value", {}).get("count", 0)
                total_propinas += doc.get("value", {}).get("propina", 0)

            ventas_hoy = list(db.ventas.aggregate([
                {"$match": {"fecha": {"$gte": hoy}}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
            ]))

            ventas_semana = list(db.ventas.aggregate([
                {"$match": {"fecha": {"$gte": semana}}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
            ]))

            ticket_promedio = total_mes / count_mes if count_mes > 0 else 0

            mesas_ocupadas = db.mesas.count_documents({"estado": "ocupada"})
            total_mesas = db.mesas.count_documents({})

            return {
                "ventas_hoy": float(ventas_hoy[0]["total"]) if ventas_hoy else 0,
                "transacciones_hoy": int(ventas_hoy[0]["count"]) if ventas_hoy else 0,
                "ventas_semana": float(ventas_semana[0]["total"]) if ventas_semana else 0,
                "ventas_mes": float(total_mes),
                "transacciones_mes": count_mes,
                "ticket_promedio": round(ticket_promedio, 2),
                "propinas_mes": round(float(total_propinas), 2),
                "mesas_ocupadas": mesas_ocupadas,
                "total_mesas": total_mesas,
                "ocupacion_pct": round((mesas_ocupadas / total_mesas * 100) if total_mesas > 0 else 0, 1)
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_top_platillos(periodo=30):
        """MapReduce: TOP 10 platillos más vendidos"""
        try:
            fecha_inicio = datetime.now() - timedelta(days=periodo)
            
            mapper = """
            function() {
                if (this.platillos && this.platillos.length > 0) {
                    this.platillos.forEach(function(p) {
                        emit(p.nombre, {
                            cantidad: p.cantidad || 0,
                            subtotal: p.subtotal || 0,
                            precio: p.precio_unitario || 0
                        });
                    });
                }
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { cantidad: 0, subtotal: 0, precio: 0 };
                values.forEach(function(value) {
                    result.cantidad += value.cantidad;
                    result.subtotal += value.subtotal;
                    result.precio += value.precio;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": fecha_inicio}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            results = []
            for doc in mr_result:
                results.append({
                    "platillo": doc["_id"],
                    "total_ingreso": round(doc.get("value", {}).get("subtotal", 0), 2),
                    "total_cantidad": doc.get("value", {}).get("cantidad", 0),
                    "precio_unitario_prom": round(doc.get("value", {}).get("precio", 0), 2),
                    "num_ventas": 1
                })
            
            results.sort(key=lambda x: x["total_ingreso"], reverse=True)
            results = results[:10]
            
            return {"data": results, "periodo_dias": periodo}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_ventas_por_dia(periodo=30):
        """MapReduce: Tendencia de ventas diarias"""
        try:
            fecha_inicio = datetime.now() - timedelta(days=periodo)
            
            mapper = """
            function() {
                var fecha = this.fecha;
                var key = fecha.getFullYear() + '-' + 
                          (fecha.getMonth() + 1).toString().padStart(2, '0') + '-' + 
                          fecha.getDate().toString().padStart(2, '0');
                emit(key, {
                    total: this.total || 0,
                    transacciones: 1,
                    comensales: this.comensales || 0
                });
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { total: 0, transacciones: 0, comensales: 0 };
                values.forEach(function(value) {
                    result.total += value.total;
                    result.transacciones += value.transacciones;
                    result.comensales += value.comensales;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": fecha_inicio}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            results = []
            for doc in mr_result:
                results.append({
                    "fecha": doc["_id"],
                    "total": round(doc.get("value", {}).get("total", 0), 2),
                    "transacciones": doc.get("value", {}).get("transacciones", 0),
                    "comensales": doc.get("value", {}).get("comensales", 0)
                })
            
            results.sort(key=lambda x: x["fecha"])
            
            return {"data": results}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_ventas_por_metodo_pago(periodo=30):
        """MapReduce: Distribución por método de pago"""
        try:
            fecha_inicio = datetime.now() - timedelta(days=periodo)
            
            mapper = """
            function() {
                emit(this.metodo_pago || 'desconocido', {
                    total: this.total || 0,
                    count: 1
                });
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { total: 0, count: 0 };
                values.forEach(function(value) {
                    result.total += value.total;
                    result.count += value.count;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": fecha_inicio}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            results = []
            for doc in mr_result:
                results.append({
                    "metodo": doc["_id"],
                    "total": round(doc.get("value", {}).get("total", 0), 2),
                    "count": doc.get("value", {}).get("count", 0)
                })
            
            results.sort(key=lambda x: x["total"], reverse=True)
            
            return {"data": results}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_horas_pico(periodo=30):
        """MapReduce: Distribución de ventas por hora"""
        try:
            fecha_inicio = datetime.now() - timedelta(days=periodo)
            
            mapper = """
            function() {
                var hora = this.fecha.getHours();
                emit(hora, {
                    total: this.total || 0,
                    count: 1
                });
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { total: 0, count: 0 };
                values.forEach(function(value) {
                    result.total += value.total;
                    result.count += value.count;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": fecha_inicio}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            results = []
            for doc in mr_result:
                results.append({
                    "hora": doc["_id"],
                    "total": round(doc.get("value", {}).get("total", 0), 2),
                    "count": doc.get("value", {}).get("count", 0)
                })
            
            results.sort(key=lambda x: x["hora"])
            
            return {"data": results}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_rendimiento_meseros(periodo=30):
        """MapReduce: Rendimiento por mesero"""
        try:
            fecha_inicio = datetime.now() - timedelta(days=periodo)
            
            mapper = """
            function() {
                emit(this.mesero_nombre || 'desconocido', {
                    total: this.total || 0,
                    count: 1,
                    comensales: this.comensales || 0,
                    propina: this.propina || 0
                });
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { total: 0, count: 0, comensales: 0, propina: 0 };
                values.forEach(function(value) {
                    result.total += value.total;
                    result.count += value.count;
                    result.comensales += value.comensales;
                    result.propina += value.propina;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": fecha_inicio}, "mesero_nombre": {"$exists": True, "$ne": ""}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            results = []
            for doc in mr_result:
                val = doc.get("value", {})
                ticket = val.get("total", 0) / val.get("count", 1) if val.get("count", 1) > 0 else 0
                results.append({
                    "mesero": doc["_id"],
                    "total_ventas": round(val.get("total", 0), 2),
                    "num_ventas": val.get("count", 0),
                    "propinas": round(val.get("propina", 0), 2),
                    "comensales_atendidos": val.get("comensales", 0),
                    "ticket_promedio": round(ticket, 2)
                })
            
            results.sort(key=lambda x: x["total_ventas"], reverse=True)
            results = results[:10]
            
            return {"data": results}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_ventas_por_mesa(periodo=30):
        """MapReduce: Ventas por mesa"""
        try:
            fecha_inicio = datetime.now() - timedelta(days=periodo)
            
            mapper = """
            function() {
                emit(this.mesa_numero, {
                    total: this.total || 0,
                    count: 1,
                    comensales: this.comensales || 0
                });
            }
            """
            
            reducer = """
            function(key, values) {
                var result = { total: 0, count: 0, comensales: 0 };
                values.forEach(function(value) {
                    result.total += value.total;
                    result.count += value.count;
                    result.comensales += value.comensales;
                });
                return result;
            }
            """
            
            query = {"fecha": {"$gte": fecha_inicio}}
            mr_result = db.ventas.map_reduce(mapper, reducer, out={"inline": 1}, query=query)
            
            results = []
            for doc in mr_result:
                val = doc.get("value", {})
                ticket = val.get("total", 0) / val.get("count", 1) if val.get("count", 1) > 0 else 0
                results.append({
                    "mesa": doc["_id"],
                    "total_ventas": round(val.get("total", 0), 2),
                    "num_visitas": val.get("count", 0),
                    "comensales_total": val.get("comensales", 0),
                    "ticket_promedio": round(ticket, 2)
                })
            
            results.sort(key=lambda x: x["total_ventas"], reverse=True)
            results = results[:15]
            
            return {"data": results}

        except Exception as e:
            return {"error": str(e)}