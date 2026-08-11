"""
Modelo de Ventas - Comandas, Ventas, Pagos
"""
from config.db import db
from datetime import datetime, timedelta
from bson.objectid import ObjectId

class Venta:
    collection = db["ventas"]
    
    # Estados de venta
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_COMPLETADA = "completada"
    ESTADO_CANCELADA = "cancelada"
    
    # Métodos de pago
    METODO_EFECTIVO = "efectivo"
    METODO_TARJETA = "tarjeta"
    METODO_TRANSFERENCIA = "transferencia"
    METODO_MIXTO = "mixto"
    
    @classmethod
    def find_all(cls, filtro=None):
        """Obtiene todas las ventas con filtros opcionales"""
        query = filtro or {}
        return list(cls.collection.find(query).sort("fecha_creacion", -1))
    
    @classmethod
    def find_by_id(cls, id):
        """Obtiene una venta por ID"""
        return cls.collection.find_one({"_id": ObjectId(id)})
    
    @classmethod
    def find_by_mesa(cls, mesa_id):
        """Obtiene ventas por mesa"""
        return list(cls.collection.find({"mesa_id": mesa_id}).sort("fecha_creacion", -1))
    
    @classmethod
    def find_by_mesero(cls, mesero_id):
        """Obtiene ventas por mesero"""
        return list(cls.collection.find({"mesero_id": mesero_id}).sort("fecha_creacion", -1))
    
    @classmethod
    def find_by_fecha(cls, fecha_inicio, fecha_fin):
        """Obtiene ventas por rango de fechas"""
        query = {
            "fecha_creacion": {
                "$gte": fecha_inicio,
                "$lte": fecha_fin
            }
        }
        return list(cls.collection.find(query).sort("fecha_creacion", -1))
    
    @classmethod
    def find_by_estado(cls, estado):
        """Obtiene ventas por estado"""
        return list(cls.collection.find({"estado": estado}).sort("fecha_creacion", -1))
    
    @classmethod
    def find_hoy(cls):
        """Obtiene las ventas de hoy"""
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        manana = hoy + timedelta(days=1)
        return cls.find_by_fecha(hoy, manana)
    
    @classmethod
    def create(cls, data):
        """Crea una nueva venta"""
        venta = {
            "mesa_id": data.get("mesa_id"),
            "mesa_nombre": data.get("mesa_nombre", ""),
            "mesero_id": data.get("mesero_id"),
            "mesero_nombre": data.get("mesero_nombre", ""),
            "cliente_nombre": data.get("cliente_nombre", ""),
            "items": data.get("items", []),
            "subtotal": float(data.get("subtotal", 0)),
            "impuesto": float(data.get("impuesto", 0)),
            "descuento": float(data.get("descuento", 0)),
            "propina": float(data.get("propina", 0)),
            "total": float(data.get("total", 0)),
            "metodo_pago": data.get("metodo_pago", cls.METODO_EFECTIVO),
            "estado": cls.ESTADO_PENDIENTE,
            "notas": data.get("notas", ""),
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        result = cls.collection.insert_one(venta)
        return str(result.inserted_id)
    
    @classmethod
    def update(cls, id, data):
        """Actualiza una venta"""
        update_data = {
            "fecha_actualizacion": datetime.utcnow()
        }
        
        # Solo actualizar campos que se proporcionan
        campos = ["mesa_id", "mesa_nombre", "mesero_id", "mesero_nombre", 
                  "cliente_nombre", "items", "subtotal", "impuesto", 
                  "descuento", "propina", "total", "metodo_pago", 
                  "estado", "notas"]
        
        for campo in campos:
            if campo in data:
                update_data[campo] = data[campo]
        
        result = cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    def delete(cls, id):
        """Elimina una venta"""
        result = cls.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    @classmethod
    def completar(cls, id, metodo_pago=None):
        """Completa una venta"""
        update_data = {
            "estado": cls.ESTADO_COMPLETADA,
            "fecha_completada": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        if metodo_pago:
            update_data["metodo_pago"] = metodo_pago
        
        result = cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    def cancelar(cls, id, motivo=None):
        """Cancela una venta"""
        update_data = {
            "estado": cls.ESTADO_CANCELADA,
            "motivo_cancelacion": motivo or "Sin motivo",
            "fecha_cancelada": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        
        result = cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    def agregar_item(cls, id, item):
        """Agrega un item a una venta"""
        venta = cls.find_by_id(id)
        if venta:
            items = venta.get("items", [])
            items.append(item)
            
            # Recalcular totales
            subtotal = sum(item.get("precio", 0) * item.get("cantidad", 1) for item in items)
            impuesto = subtotal * 0.16  # 16% de impuesto
            total = subtotal + impuesto
            
            result = cls.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "items": items,
                    "subtotal": subtotal,
                    "impuesto": impuesto,
                    "total": total,
                    "fecha_actualizacion": datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        return False
    
    @classmethod
    def get_estadisticas_hoy(cls):
        """Obtiene estadísticas del día"""
        ventas_hoy = cls.find_hoy()
        
        total_ventas = sum(v.get("total", 0) for v in ventas_hoy)
        num_transacciones = len(ventas_hoy)
        ticket_promedio = total_ventas / num_transacciones if num_transacciones > 0 else 0
        cuentas_pendientes = len([v for v in ventas_hoy if v.get("estado") == cls.ESTADO_PENDIENTE])
        
        return {
            "total_ventas": total_ventas,
            "num_transacciones": num_transacciones,
            "ticket_promedio": ticket_promedio,
            "cuentas_pendientes": cuentas_pendientes
        }
    
    @classmethod
    def get_ventas_por_metodo(cls, fecha_inicio, fecha_fin):
        """Obtiene ventas agrupadas por método de pago"""
        ventas = cls.find_by_fecha(fecha_inicio, fecha_fin)
        
        por_metodo = {}
        for venta in ventas:
            metodo = venta.get("metodo_pago", cls.METODO_EFECTIVO)
            if metodo not in por_metodo:
                por_metodo[metodo] = {"count": 0, "total": 0}
            por_metodo[metodo]["count"] += 1
            por_metodo[metodo]["total"] += venta.get("total", 0)

        return por_metodo

    @classmethod
    def ensure_indexes(cls):
        """Índices para consultas por rango de fechas (analítica, cortes, Pareto, etc.)"""
        cls.collection.create_index("fecha_creacion")
        cls.collection.create_index([("mesa_id", 1), ("fecha_creacion", -1)])
        cls.collection.create_index([("mesero_id", 1), ("fecha_creacion", -1)])


class Cuenta:
    collection = db["cuentas"]
    
    @classmethod
    def find_abiertas(cls):
        """Obtiene cuentas abiertas"""
        return list(cls.collection.find({"estado": "abierta"}).sort("fecha_creacion", -1))
    
    @classmethod
    def find_by_id(cls, id):
        """Obtiene una cuenta por ID"""
        return cls.collection.find_one({"_id": ObjectId(id)})
    
    @classmethod
    def create(cls, data):
        """Crea una nueva cuenta"""
        cuenta = {
            "mesa_id": data.get("mesa_id"),
            "mesa_nombre": data.get("mesa_nombre"),
            "mesero_id": data.get("mesero_id"),
            "mesero_nombre": data.get("mesero_nombre"),
            "cliente_nombre": data.get("cliente_nombre", ""),
            "num_personas": data.get("num_personas", 1),
            "estado": "abierta",
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        result = cls.collection.insert_one(cuenta)
        return str(result.inserted_id)
    
    @classmethod
    def cerrar(cls, id, datos_pago):
        """Cierra una cuenta"""
        update_data = {
            "estado": "cerrada",
            "metodo_pago": datos_pago.get("metodo_pago"),
            "total": datos_pago.get("total", 0),
            "propina": datos_pago.get("propina", 0),
            "fecha_cierre": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        
        result = cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0


class CorteCaja:
    collection = db["cortes_caja"]
    
    @classmethod
    def find_all(cls):
        """Obtiene todos los cortes de caja"""
        return list(cls.collection.find().sort("fecha_creacion", -1))
    
    @classmethod
    def find_by_id(cls, id):
        """Obtiene un corte por ID"""
        return cls.collection.find_one({"_id": ObjectId(id)})
    
    @classmethod
    def create(cls, data):
        """Crea un nuevo corte de caja"""
        corte = {
            "usuario_id": data.get("usuario_id"),
            "usuario_nombre": data.get("usuario_nombre"),
            "fecha_inicio": data.get("fecha_inicio"),
            "fecha_fin": data.get("fecha_fin"),
            "ventas": data.get("ventas", []),
            "total_ventas": data.get("total_ventas", 0),
            "total_efectivo": data.get("total_efectivo", 0),
            "total_tarjeta": data.get("total_tarjeta", 0),
            "total_transferencia": data.get("total_transferencia", 0),
            "total_propinas": data.get("total_propinas", 0),
            "num_transacciones": data.get("num_transacciones", 0),
            "notas": data.get("notas", ""),
            "fecha_creacion": datetime.utcnow()
        }
        result = cls.collection.insert_one(corte)
        return str(result.inserted_id)
    
    @classmethod
    def find_by_fecha(cls, fecha):
        """Obtiene un corte por fecha"""
        return cls.collection.find_one({
            "fecha_creacion": {
                "$gte": fecha.replace(hour=0, minute=0, second=0),
                "$lt": (fecha + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            }
        })
