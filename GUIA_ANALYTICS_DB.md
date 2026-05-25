# Guía: Llamadas de Base de Datos al Sistema de Analytics

Este documento muestra los bloques de código donde se realizan las llamadas a MongoDB para el sistema de Analytics del restaurante.

---

## 1. Controlador de Analytics

**Archivo:** `controllers/analytics/analytics_controller.py`

Este archivo contiene todas las consultas de agregación para métricas avanzadas.

### 1.1 KPIs Generales

```python
@staticmethod
def get_kpis():
    """MapReduce: KPIs generales del negocio"""
    try:
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        semana = hoy - timedelta(days=7)
        mes = hoy - timedelta(days=30)

        # Ventas de hoy
        ventas_hoy = list(db.ventas.aggregate([
            {"$match": {"fecha": {"$gte": hoy}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
        ]))

        # Ventas de la semana
        ventas_semana = list(db.ventas.aggregate([
            {"$match": {"fecha": {"$gte": semana}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
        ]))

        # Ventas del mes
        ventas_mes = list(db.ventas.aggregate([
            {"$match": {"fecha": {"$gte": mes}}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
        ]))

        total_mes = float(ventas_mes[0]["total"]) if ventas_mes else 0
        count_mes = int(ventas_mes[0]["count"]) if ventas_mes else 0
        ticket_promedio = total_mes / count_mes if count_mes > 0 else 0

        # Mesas
        mesas_ocupadas = db.mesas.count_documents({"estado": "ocupada"})
        total_mesas = db.mesas.count_documents({})

        # Propinas del mes
        propinas_mes = list(db.ventas.aggregate([
            {"$match": {"fecha": {"$gte": mes}}},
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
```

---

### 1.2 Top Platillos MapReduce

```python
@staticmethod
def get_top_platillos():
    """
    MapReduce: TOP 10 platillos más vendidos por ingreso y cantidad.
    MAP → $unwind descompone cada elemento del array platillos.
    REDUCE → $group agrupa por nombre y suma subtotal + cantidad.
    """
    try:
        fecha_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha": {"$gte": fecha_inicio}}},
            # MAP: un documento por cada platillo vendido
            {"$unwind": "$platillos"},
            {"$match": {"platillos.nombre": {"$exists": True, "$ne": None}}},
            # REDUCE: agrupar por nombre del platillo
            {"$group": {
                "_id": "$platillos.nombre",
                "total_ingreso": {"$sum": "$platillos.subtotal"},
                "total_cantidad": {"$sum": "$platillos.cantidad"},
                "precio_unitario_prom": {"$avg": "$platillos.precio_unitario"},
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
```

---

### 1.3 Ventas por Día (Últimos 30 días)

```python
@staticmethod
def get_ventas_por_dia():
    """MapReduce: Tendencia de ventas diarias"""
    try:
        fecha_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha": {"$gte": fecha_inicio}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$fecha"},
                    "month": {"$month": "$fecha"},
                    "day": {"$dayOfMonth": "$fecha"}
                },
                "total": {"$sum": "$total"},
                "transacciones": {"$sum": 1},
                "comensales": {"$sum": "$comensales"}
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
                "comensales": 1,
                "_id": 0
            }}
        ]

        resultado = list(db.ventas.aggregate(pipeline))
        return jsonify({"data": resultado})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

### 1.4 Ventas por Método de Pago

```python
@staticmethod
def get_ventas_por_metodo_pago():
    """MapReduce: Distribución por método de pago"""
    try:
        fecha_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha": {"$gte": fecha_inicio}}},
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
```

---

### 1.5 Horas Pico

```python
@staticmethod
def get_horas_pico():
    """MapReduce: Distribución de ventas por hora del día"""
    try:
        fecha_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha": {"$gte": fecha_inicio}}},
            {"$group": {
                "_id": {"$hour": "$fecha"},
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
```

---

### 1.6 Rendimiento por Mesero

```python
@staticmethod
def get_rendimiento_meseros():
    """MapReduce: Ventas, ticket promedio y propinas por mesero"""
    try:
        fecha_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio},
                "mesero_nombre": {"$exists": True, "$ne": ""}
            }},
            {"$group": {
                "_id": "$mesero_nombre",
                "total_ventas": {"$sum": "$total"},
                "num_ventas": {"$sum": 1},
                "propinas": {"$sum": "$propina"},
                "comensales_atendidos": {"$sum": "$comensales"}
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
```

---

### 1.7 Ventas por Mesa

```python
@staticmethod
def get_ventas_por_mesa():
    """MapReduce: Consumo promedio por número de mesa"""
    try:
        fecha_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha": {"$gte": fecha_inicio}}},
            {"$group": {
                "_id": "$mesa_numero",
                "total_ventas": {"$sum": "$total"},
                "num_visitas": {"$sum": 1},
                "comensales_total": {"$sum": "$comensales"},
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
```

---

## 2. Modelo de Reportes

**Archivo:** `models/reports_model.py`

Contiene consultas más avanzadas para reportes financieros, de inventario y operativos.

### 2.1 Reportes Financieros

```python
@staticmethod
def ventas_por_periodo(fecha_inicio, fecha_fin, granularidad='dia'):
    """Obtiene ventas por período (día, semana, mes)"""
    match_stage = {
        "$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "estado": {"$ne": "cancelado"}
        }
    }
    
    if granularidad == 'dia':
        group_id = {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha"}}
    elif granularidad == 'semana':
        group_id = {"$dateToString": {"format": "%Y-W%V", "date": "$fecha"}}
    else:  # mes
        group_id = {"$dateToString": {"format": "%Y-%m", "date": "$fecha"}}
    
    pipeline = [
        match_stage,
        {"$group": {
            "_id": group_id,
            "total_ventas": {"$sum": "$total"},
            "num_pedidos": {"$sum": 1},
            "total_propinas": {"$sum": {"$ifNull": ["$propina", 0]}},
            "promedio_por_pedido": {"$avg": "$total"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    return list(ReportsModel.pedidos.aggregate(pipeline))


@staticmethod
def utilidad_bruta(fecha_inicio, fecha_fin):
    """Calcula la utilidad bruta por período"""
    ventas_pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "estado": {"$ne": "cancelado"}
        }},
        {"$group": {
            "_id": None,
            "total_ventas": {"$sum": "$total"},
            "costo_insumos": {"$sum": "$costo_total"}
        }}
    ]
    
    ventas_result = list(ReportsModel.pedidos.aggregate(ventas_pipeline))
    
    if not ventas_result:
        return {"total_ventas": 0, "costo_insumos": 0, "utilidad_bruta": 0, "margen_bruto": 0}
    
    total_ventas = ventas_result[0]["total_ventas"]
    costo_insumos = ventas_result[0]["costo_insumos"] or 0
    utilidad_bruta = total_ventas - costo_insumos
    margen_bruto = (utilidad_bruta / total_ventas * 100) if total_ventas > 0 else 0
    
    return {
        "total_ventas": total_ventas,
        "costo_insumos": costo_insumos,
        "utilidad_bruta": utilidad_bruta,
        "margen_bruto": round(margen_bruto, 2)
    }


@staticmethod
def margen_por_producto(fecha_inicio, fecha_fin):
    """Calcula el margen de ganancia por cada platillo"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "estado": {"$ne": "cancelado"}
        }},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.platillo_id",
            "nombre": {"$first": "$items.nombre"},
            "ventas_totales": {"$sum": {"$multiply": ["$items.cantidad", "$items.precio"]}},
            "cantidad_vendida": {"$sum": "$items.cantidad"},
            "costo_total": {"$sum": {"$multiply": ["$items.cantidad", "$items.costo"]}}
        }},
        {"$project": {
            "nombre": 1,
            "ventas_totales": 1,
            "cantidad_vendida": 1,
            "costo_total": 1,
            "utilidad": {"$subtract": ["$ventas_totales", "$costo_total"]},
            "margen": {
                "$multiply": [
                    {"$divide": [
                        {"$subtract": ["$ventas_totales", "$costo_total"]},
                        "$ventas_totales"
                    ]},
                    100
                ]
            }
        }},
        {"$sort": {"ventas_totales": -1}}
    ]
    
    return list(ReportsModel.pedidos.aggregate(pipeline))
```

---

### 2.2 Reportes de Inventario

```python
@staticmethod
def consumo_por_periodo(fecha_inicio, fecha_fin):
    """Consumo de insumos por período"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "tipo": "salida"
        }},
        {"$group": {
            "_id": "$insumo_id",
            "nombre": {"$first": "$insumo_nombre"},
            "categoria": {"$first": "$categoria"},
            "cantidad_total": {"$sum": "$cantidad"},
            "costo_total": {"$sum": "$costo_total"},
            "movimientos": {"$sum": 1}
        }},
        {"$sort": {"costo_total": -1}}
    ]
    
    return list(ReportsModel.movimientos.aggregate(pipeline))


@staticmethod
def merma_acumulada(fecha_inicio, fecha_fin):
    """Merma acumulada por insumo"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "tipo": "merma"
        }},
        {"$group": {
            "_id": "$insumo_id",
            "nombre": {"$first": "$insumo_nombre"},
            "categoria": {"$first": "$categoria"},
            "cantidad_perdida": {"$sum": "$cantidad"},
            "costo_perdido": {"$sum": "$costo_total"},
            "num_movimientos": {"$sum": 1}
        }},
        {"$sort": {"costo_perdido": -1}}
    ]
    
    return list(ReportsModel.movimientos.aggregate(pipeline))


@staticmethod
def rotacion_inventario(fecha_inicio, fecha_fin):
    """Rotación de inventario por categoría"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "tipo": {"$in": ["salida", "venta"]}
        }},
        {"$group": {
            "_id": "$categoria",
            "costo_total_consumido": {"$sum": "$costo_total"},
            "cantidad_total": {"$sum": "$cantidad"}
        }},
        {"$sort": {"costo_total_consumido": -1}}
    ]
    
    return list(ReportsModel.movimientos.aggregate(pipeline))


@staticmethod
def stock_actual():
    """Stock actual de todos los insumos"""
    return list(ReportsModel.insumos.aggregate([
        {"$match": {"activo": True}},
        {"$sort": {"categoria": 1, "nombre": 1}}
    ]))
```

---

### 2.3 Reportes Operativos

```python
@staticmethod
def rendimiento_empleado(fecha_inicio, fecha_fin):
    """Rendimiento por empleado (ventas, pedidos, propinas)"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "estado": {"$ne": "cancelado"}
        }},
        {"$group": {
            "_id": "$mesero_id",
            "nombre_mesero": {"$first": "$mesero_nombre"},
            "total_ventas": {"$sum": "$total"},
            "num_pedidos": {"$sum": 1},
            "total_propinas": {"$sum": {"$ifNull": ["$propina", 0]}},
            "promedio_venta": {"$avg": "$total"}
        }},
        {"$sort": {"total_ventas": -1}}
    ]
    
    return list(ReportsModel.pedidos.aggregate(pipeline))


@staticmethod
def platillos_mas_vendidos(fecha_inicio, fecha_fin, limite=10):
    """Platillos más vendidos"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "estado": {"$ne": "cancelado"}
        }},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.platillo_id",
            "nombre": {"$first": "$items.nombre"},
            "categoria": {"$first": "$items.categoria"},
            "cantidad_vendida": {"$sum": "$items.cantidad"},
            "ventas_totales": {"$sum": {"$multiply": ["$items.cantidad", "$items.precio"]}}
        }},
        {"$sort": {"cantidad_vendida": -1}},
        {"$limit": limite}
    ]
    
    return list(ReportsModel.pedidos.aggregate(pipeline))


@staticmethod
def platillos_menos_rentables(fecha_inicio, fecha_fin, limite=10):
    """Platillos menos rentables (bajo margen)"""
    pipeline = [
        {"$match": {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
            "estado": {"$ne": "cancelado"}
        }},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.platillo_id",
            "nombre": {"$first": "$items.nombre"},
            "categoria": {"$first": "$items.categoria"},
            "ventas_totales": {"$sum": {"$multiply": ["$items.cantidad", "$items.precio"]}},
            "costo_total": {"$sum": {"$multiply": ["$items.cantidad", "$items.costo"]}},
            "cantidad_vendida": {"$sum": "$items.cantidad"}
        }},
        {"$project": {
            "nombre": 1,
            "categoria": 1,
            "ventas_totales": 1,
            "costo_total": 1,
            "cantidad_vendida": 1,
            "utilidad": {"$subtract": ["$ventas_totales", "$costo_total"]},
            "margen": {
                "$multiply": [
                    {"$divide": [
                        {"$subtract": ["$ventas_totales", "$costo_total"]},
                        "$ventas_totales"
                    ]},
                    100
                ]
            }
        }},
        {"$sort": {"margen": 1}},
        {"$limit": limite}
    ]
    
    return list(ReportsModel.pedidos.aggregate(pipeline))
```

---

## 3. Analytics con Spark (MapReduce)

**Archivo:** `analytics/dashboard_mapreduce.py`

Este archivo usa Apache Spark para análisis distribuido.

```python
import streamlit as st
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum, avg, count
import pandas as pd

# CARGA DE DATOS DESDE MONGODB
@st.cache_resource
def load_data():
    spark, df, _ = get_spark_session()
    return spark, df

spark, df = load_data()

# FILTROS
productos = [row["producto"] for row in df.select("producto").distinct().collect()]
producto_seleccionado = st.sidebar.multiselect(
    "Selecciona producto",
    productos,
    default=productos
)

df_filtrado = df.filter(df["producto"].isin(producto_seleccionado))

# MAPREDUCE (AGREGACIONES CON SPARK)
resumen = df_filtrado.groupBy("producto").agg(
    sum("ingreso").alias("ingreso_total"),
    sum("cantidad").alias("cantidad_total"),
    avg("precio").alias("precio_promedio"),
    count("*").alias("numero_ventas")
)

resumen_pd = resumen.toPandas()
st.dataframe(resumen_pd)
```

---

## 4. Rutas de Analytics

**Archivo:** `routes.py`

```python
from controllers.analytics.analytics_controller import AnalyticsController

# Dashboard de Analytics
@routes_bp.route("/analytics")
@login_required
@rol_required(['1'])
def analytics_index():
    """Vista principal del dashboard de analytics"""
    return AnalyticsController.index()

# APIs de Analytics
@routes_bp.route("/api/analytics/kpis")
@login_required
@rol_required(['1'])
def api_analytics_kpis():
    return AnalyticsController.get_kpis()

@routes_bp.route("/api/analytics/top-platillos")
@login_required
@rol_required(['1'])
def api_analytics_top_platillos():
    return AnalyticsController.get_top_platillos()

@routes_bp.route("/api/analytics/ventas-por-dia")
@login_required
@rol_required(['1'])
def api_analytics_ventas_dia():
    return AnalyticsController.get_ventas_por_dia()

@routes_bp.route("/api/analytics/ventas-metodo-pago")
@login_required
@rol_required(['1'])
def api_analytics_metodo_pago():
    return AnalyticsController.get_ventas_por_metodo_pago()

@routes_bp.route("/api/analytics/horas-pico")
@login_required
@rol_required(['1'])
def api_analytics_horas_pico():
    return AnalyticsController.get_horas_pico()

@routes_bp.route("/api/analytics/rendimiento-meseros")
@login_required
@rol_required(['1'])
def api_analytics_meseros():
    return AnalyticsController.get_rendimiento_meseros()

@routes_bp.route("/api/analytics/ventas-mesa")
@login_required
@rol_required(['1'])
def api_analytics_mesa():
    return AnalyticsController.get_ventas_por_mesa()
```

---

## Resumen de Colecciones Utilizadas en Analytics

| Colección | Uso Principal |
|-----------|----------------|
| `ventas` | Transacciones, ingresos, propinas |
| `pedidos` | Detalles de pedidos, items |
| `mesas` | Estado de ocupación |
| `insumos` | Stock de inventario |
| `movimientos_inventario` | Entradas, salidas, mermas |
| `usuarios` | Rendimiento de empleados |

---

## Patrones de Agregación MongoDB Utilizados

```python
# Contar documentos
db.ventas.count_documents({filtro})

# Agregación básica con $group
db.ventas.aggregate([
    {"$match": {"fecha": {"$gte": fecha_inicio}}},
    {"$group": {"_id": None, "total": {"$sum": "$total"}}}
])

# MapReduce con $unwind (descomponer arrays)
db.ventas.aggregate([
    {"$unwind": "$platillos"},
    {"$group": {"_id": "$platillos.nombre", "total": {"$sum": "$platillos.subtotal"}}}
])

# Agrupar por fecha
db.ventas.aggregate([
    {"$group": {
        "_id": {"$year": "$fecha"},
        "total": {"$sum": "$total"}
    }}
])

# Multiple aggregations con $project
db.ventas.aggregate([
    {"$group": {...}},
    {"$project": {"campo": "$_id", "total": 1, "_id": 0}}
])
```
