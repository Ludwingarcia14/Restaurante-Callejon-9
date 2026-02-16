"""
Modelo de Reportes - Sistema Completo de Reportes del Restaurante
Reports: Financial, Inventory, Operational with Export Capabilities
"""
from config.db import db
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from collections import defaultdict

class ReportsModel:
    """Modelo principal para todos los reportes del sistema"""
    
    # Colecciones
    ventas = db.ventas
    pedidos = db.pedidos
    platillos = db.platillos
    insumos = db.insumos
    movimientos = db.movimientos_inventario
    usuarios = db.usuarios
    clientes = db.clientes
    mesas = db.mesas
    ordenes = db.ordenes
    
    # ==========================================
    # REPORTES FINANCIEROS
    # ==========================================
    
    @staticmethod
    def ventas_por_periodo(fecha_inicio, fecha_fin, granularidad='dia'):
        """
        Obtiene ventas por período (día, semana, mes)
        
        Args:
            fecha_inicio: datetime - Fecha de inicio
            fecha_fin: datetime - Fecha de fin
            granularidad: 'dia', 'semana', 'mes'
            
        Returns:
            list: Ventas agrupadas por período
        """
        match_stage = {
            "$match": {
                "fecha": {
                    "$gte": fecha_inicio,
                    "$lte": fecha_fin
                },
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
            {
                "$group": {
                    "_id": group_id,
                    "total_ventas": {"$sum": "$total"},
                    "num_pedidos": {"$sum": 1},
                    "total_propinas": {"$sum": {"$ifNull": ["$propina", 0]}},
                    "promedio_por_pedido": {"$avg": "$total"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    @staticmethod
    def utilidad_bruta(fecha_inicio, fecha_fin):
        """
        Calcula la utilidad bruta por período
        Utilidad = Ventas - Costo de Insumos
        """
        # Obtener ventas
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
        """
        Calcula el margen de ganancia por cada platillo
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "estado": {"$ne": "cancelado"}
            }},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.platillo_id",
                    "nombre": {"$first": "$items.nombre"},
                    "ventas_totales": {"$sum": {"$multiply": ["$items.cantidad", "$items.precio"]}},
                    "cantidad_vendida": {"$sum": "$items.cantidad"},
                    "costo_total": {"$sum": {"$multiply": ["$items.cantidad", "$items.costo"]}}
                }
            },
            {
                "$project": {
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
                }
            },
            {"$sort": {"ventas_totales": -1}}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    @staticmethod
    def ingresos_vs_gastos(fecha_inicio, fecha_fin):
        """
        Compara ingresos por ventas vs gastos operativos
        """
        # Ingresos por ventas
        ingresos_pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "estado": {"$ne": "cancelado"}
            }},
            {"$group": {
                "_id": None,
                "total_ingresos": {"$sum": "$total"}
            }}
        ]
        
        # Gastos de inventario (salidas)
        gastos_pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "tipo": "salida"
            }},
            {"$group": {
                "_id": None,
                "total_gastos": {"$sum": "$costo_total"}
            }}
        ]
        
        ingresos = list(ReportsModel.pedidos.aggregate(ingresos_pipeline))
        gastos = list(ReportsModel.movimientos.aggregate(gastos_pipeline))
        
        total_ingresos = ingresos[0]["total_ingresos"] if ingresos else 0
        total_gastos = gastos[0]["total_gastos"] if gastos else 0
        
        return {
            "ingresos": total_ingresos,
            "gastos": total_gastos,
            "diferencia": total_ingresos - total_gastos,
            "ratio": round(total_ingresos / total_gastos, 2) if total_gastos > 0 else 0
        }
    
    @staticmethod
    def flujo_caja(fecha_inicio, fecha_fin):
        """
        Flujo de caja diario (entradas - salidas)
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha"}},
                "entradas": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$tipo", ["entrada", "venta"]]},
                            "$monto",
                            0
                        ]
                    }
                },
                "salidas": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$tipo", ["salida", "gasto", "merma"]]},
                            "$monto",
                            0
                        ]
                    }
                }
            }},
            {
                "$project": {
                    "fecha": "$_id",
                    "entradas": 1,
                    "salidas": 1,
                    "flujo_neto": {"$subtract": ["$entradas", "$salidas"]}
                }
            },
            {"$sort": {"fecha": 1}}
        ]
        
        return list(ReportsModel.movimientos.aggregate(pipeline))
    
    # ==========================================
    # REPORTES DE INVENTARIO
    # ==========================================
    
    @staticmethod
    def consumo_por_periodo(fecha_inicio, fecha_fin):
        """
        Consumo de insumos por período
        """
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
        """
        Merma acumulada por insumo
        """
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
        """
        Rotación de inventario por categoría
        Rotación = Costo de Insumos Vendidos / Inventario Promedio
        """
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
    def insumos_mas_costosos(fecha_inicio, fecha_fin, limite=10):
        """
        Insumos con mayor costo acumulado
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "tipo": {"$in": ["salida", "entrada", "merma"]}
            }},
            {"$group": {
                "_id": "$insumo_id",
                "nombre": {"$first": "$insumo_nombre"},
                "categoria": {"$first": "$categoria"},
                "costo_total": {"$sum": "$costo_total"},
                "cantidad_total": {"$sum": "$cantidad"}
            }},
            {"$sort": {"costo_total": -1}},
            {"$limit": limite}
        ]
        
        return list(ReportsModel.movimientos.aggregate(pipeline))
    
    @staticmethod
    def stock_actual():
        """
        Stock actual de todos los insumos
        """
        return list(ReportsModel.insumos.aggregate([
            {"$match": {"activo": True}},
            {"$sort": {"categoria": 1, "nombre": 1}}
        ]))
    
    # ==========================================
    # REPORTES OPERATIVOS
    # ==========================================
    
    @staticmethod
    def rendimiento_empleado(fecha_inicio, fecha_fin):
        """
        Rendimiento por empleado (ventas, pedidos, propinas)
        """
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
    def tiempo_promedio_servicio(fecha_inicio, fecha_fin):
        """
        Tiempo promedio de servicio por período
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
            }},
            {"$project": {
                "fecha": 1,
                "tiempo_total": {"$subtract": ["$hora_servicio", "$hora_pedido"]},
                "hora_pedido": 1,
                "hora_servicio": 1
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha"}},
                "tiempo_promedio_minutos": {"$avg": {"$divide": ["$tiempo_total", 60000]}},
                "pedidos_totales": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    @staticmethod
    def platillos_mas_vendidos(fecha_inicio, fecha_fin, limite=10):
        """
        Platillos más vendidos
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "estado": {"$ne": "cancelado"}
            }},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.platillo_id",
                    "nombre": {"$first": "$items.nombre"},
                    "categoria": {"$first": "$items.categoria"},
                    "cantidad_vendida": {"$sum": "$items.cantidad"},
                    "ventas_totales": {"$sum": {"$multiply": ["$items.cantidad", "$items.precio"]}}
                }
            },
            {"$sort": {"cantidad_vendida": -1}},
            {"$limit": limite}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    @staticmethod
    def platillos_menos_rentables(fecha_inicio, fecha_fin, limite=10):
        """
        Platillos menos rentables (bajo margen)
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "estado": {"$ne": "cancelado"}
            }},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.platillo_id",
                    "nombre": {"$first": "$items.nombre"},
                    "categoria": {"$first": "$items.categoria"},
                    "ventas_totales": {"$sum": {"$multiply": ["$items.cantidad", "$items.precio"]}},
                    "costo_total": {"$sum": {"$multiply": ["$items.cantidad", "$items.costo"]}},
                    "cantidad_vendida": {"$sum": "$items.cantidad"}
                }
            },
            {
                "$project": {
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
                }
            },
            {"$sort": {"margen": 1}},
            {"$limit": limite}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    # ==========================================
    # REPORTES DE Métodos de Pago
    # ==========================================
    
    @staticmethod
    def distribucion_metodos_pago(fecha_inicio, fecha_fin):
        """
        Distribución de ventas por método de pago
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "estado": {"$ne": "cancelado"}
            }},
            {"$unwind": "$pagos"},
            {
                "$group": {
                    "_id": "$pagos.metodo",
                    "total": {"$sum": "$pagos.monto"},
                    "transacciones": {"$sum": 1}
                }
            },
            {"$sort": {"total": -1}}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    # ==========================================
    # REPORTES DE Tendencias
    # ==========================================
    
    @staticmethod
    def tendencia_ingresos(fecha_inicio, fecha_fin):
        """
        Tendencia de ingresos a lo largo del tiempo
        """
        pipeline = [
            {"$match": {
                "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin},
                "estado": {"$ne": "cancelado"}
            }},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha"}},
                    "total_ingresos": {"$sum": "$total"},
                    "num_pedidos": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        return list(ReportsModel.pedidos.aggregate(pipeline))
    
    # ==========================================
    # RESUMEN EJECUTIVO
    # ==========================================
    
    @staticmethod
    def resumen_ejecutivo(fecha_inicio, fecha_fin):
        """
        Resumen ejecutivo con todas las métricas principales
        """
        return {
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "financiero": ReportsModel.utilidad_bruta(fecha_inicio, fecha_fin),
            "ventas": ReportsModel.ventas_por_periodo(fecha_inicio, fecha_fin),
            "top_platillos": ReportsModel.platillos_mas_vendidos(fecha_inicio, fecha_fin, 5),
            "top_empleados": ReportsModel.rendimiento_empleado(fecha_inicio, fecha_fin, )[:3],
            "metodos_pago": ReportsModel.distribucion_metodos_pago(fecha_inicio, fecha_fin),
            "mermas": ReportsModel.merma_acumulada(fecha_inicio, fecha_fin)
        }
