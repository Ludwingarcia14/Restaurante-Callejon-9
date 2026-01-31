"""
Modelo de Inventario - Sistema de Movimientos
Roles: 1=Admin, 4=Inventario
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId
from enum import Enum

# ==========================================
# ENUMS PARA TIPOS DE MOVIMIENTO
# ==========================================

class TipoMovimiento(str, Enum):
    """Tipos de movimientos de inventario"""
    ENTRADA = "entrada"           # Compras, devoluciones de clientes
    SALIDA = "salida"             # Uso en cocina, ventas
    AJUSTE = "ajuste"             # Correcciones de inventario
    MERMA = "merma"               # Pérdidas, caducidad, daños
    TRANSFERENCIA = "transferencia"  # Entre almacenes (futuro)

class UnidadMedida(str, Enum):
    """Unidades de medida para insumos"""
    KG = "kg"           # Kilogramos
    GR = "gr"           # Gramos
    LT = "lt"           # Litros
    ML = "ml"           # Mililitros
    PZA = "pza"         # Piezas
    CAJA = "caja"       # Cajas
    PAQUETE = "paquete" # Paquetes

class CategoriaInsumo(str, Enum):
    """Categorías de insumos"""
    CARNES = "carnes"
    VERDURAS = "verduras"
    LACTEOS = "lacteos"
    GRANOS = "granos"
    BEBIDAS = "bebidas"
    CONDIMENTOS = "condimentos"
    DESECHABLES = "desechables"
    LIMPIEZA = "limpieza"
    OTROS = "otros"


# ==========================================
# MODELO: INSUMO
# ==========================================

class Insumo:
    """
    Modelo de Insumo - Representa un producto en el almacén
    """
    collection = db["insumos"]
    
    @classmethod
    def crear_insumo(cls, data):
        """
        Crea un nuevo insumo en el sistema
        
        Args:
            data (dict): Datos del insumo
                - nombre: str
                - categoria: str (enum CategoriaInsumo)
                - unidad_medida: str (enum UnidadMedida)
                - stock_minimo: float
                - costo_unitario: float (opcional)
                - proveedor_id: ObjectId (opcional)
        
        Returns:
            ObjectId: ID del insumo creado
        """
        insumo = {
            "nombre": data["nombre"],
            "categoria": data["categoria"],
            "unidad_medida": data["unidad_medida"],
            "stock_actual": data.get("stock_inicial", 0),
            "stock_minimo": data["stock_minimo"],
            "costo_unitario": data.get("costo_unitario", 0),
            "proveedor_id": ObjectId(data["proveedor_id"]) if data.get("proveedor_id") else None,
            "activo": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = cls.collection.insert_one(insumo)
        return result.inserted_id
    
    @classmethod
    def obtener_todos(cls, filtros=None):
        """Obtiene todos los insumos con filtros opcionales"""
        query = filtros or {}
        return list(cls.collection.find(query).sort("nombre", 1))
    
    @classmethod
    def obtener_por_id(cls, insumo_id):
        """Obtiene un insumo por su ID"""
        return cls.collection.find_one({"_id": ObjectId(insumo_id)})
    
    @classmethod
    def obtener_stock_critico(cls):
        """Obtiene insumos con stock por debajo del mínimo"""
        pipeline = [
            {
                "$match": {
                    "activo": True,
                    "$expr": {
                        "$lte": ["$stock_actual", "$stock_minimo"]
                    }
                }
            },
            {"$sort": {"nombre": 1}}
        ]
        return list(cls.collection.aggregate(pipeline))
    
    @classmethod
    def actualizar_stock(cls, insumo_id, nuevo_stock):
        """
        Actualiza el stock actual de un insumo
        ⚠️ SOLO para uso interno del sistema de movimientos
        """
        return cls.collection.update_one(
            {"_id": ObjectId(insumo_id)},
            {
                "$set": {
                    "stock_actual": nuevo_stock,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    @classmethod
    def actualizar_costo(cls, insumo_id, nuevo_costo):
        """Actualiza el costo unitario de un insumo"""
        return cls.collection.update_one(
            {"_id": ObjectId(insumo_id)},
            {
                "$set": {
                    "costo_unitario": nuevo_costo,
                    "updated_at": datetime.utcnow()
                }
            }
        )


# ==========================================
# MODELO: MOVIMIENTO DE INVENTARIO
# ==========================================

class MovimientoInventario:
    """
    Modelo de Movimiento - Representa cada operación sobre el inventario
    Sistema de auditoría completo
    """
    collection = db["movimientos_inventario"]
    
    @classmethod
    def registrar_movimiento(cls, data):
        """
        Registra un movimiento de inventario y actualiza el stock
        
        Args:
            data (dict):
                - tipo: str (enum TipoMovimiento)
                - insumo_id: ObjectId
                - cantidad: float
                - usuario_id: ObjectId (quien registra)
                - costo_unitario: float (opcional)
                - proveedor_id: ObjectId (opcional, para entradas)
                - motivo: str (opcional)
                - referencia: str (opcional, ej: número de factura)
        
        Returns:
            dict: {"success": bool, "movimiento_id": ObjectId, "stock_nuevo": float}
        """
        try:
            # 1. Obtener insumo actual
            insumo = Insumo.obtener_por_id(data["insumo_id"])
            if not insumo:
                return {"success": False, "error": "Insumo no encontrado"}
            
            stock_anterior = insumo["stock_actual"]
            cantidad = float(data["cantidad"])
            
            # 2. Calcular nuevo stock según tipo de movimiento
            if data["tipo"] in [TipoMovimiento.ENTRADA, TipoMovimiento.AJUSTE]:
                # Si es ajuste, la cantidad puede ser negativa
                if data["tipo"] == TipoMovimiento.AJUSTE:
                    stock_nuevo = stock_anterior + cantidad
                else:
                    stock_nuevo = stock_anterior + abs(cantidad)
            elif data["tipo"] in [TipoMovimiento.SALIDA, TipoMovimiento.MERMA]:
                stock_nuevo = stock_anterior - abs(cantidad)
            else:
                return {"success": False, "error": "Tipo de movimiento inválido"}
            
            # 3. Validar que no quede stock negativo
            if stock_nuevo < 0:
                return {"success": False, "error": "Stock insuficiente"}
            
            # 4. Crear el documento del movimiento
            movimiento = {
                "tipo": data["tipo"],
                "insumo_id": ObjectId(data["insumo_id"]),
                "insumo_nombre": insumo["nombre"],  # Desnormalización para reportes
                "cantidad": cantidad,
                "unidad_medida": insumo["unidad_medida"],
                "stock_anterior": stock_anterior,
                "stock_nuevo": stock_nuevo,
                "costo_unitario": data.get("costo_unitario", insumo.get("costo_unitario", 0)),
                "costo_total": abs(cantidad) * data.get("costo_unitario", insumo.get("costo_unitario", 0)),
                "usuario_id": ObjectId(data["usuario_id"]),
                "proveedor_id": ObjectId(data["proveedor_id"]) if data.get("proveedor_id") else None,
                "motivo": data.get("motivo", ""),
                "referencia": data.get("referencia", ""),
                "fecha": datetime.utcnow()
            }
            
            # 5. Insertar movimiento
            result = cls.collection.insert_one(movimiento)
            
            # 6. Actualizar stock del insumo
            Insumo.actualizar_stock(data["insumo_id"], stock_nuevo)
            
            # 7. Si es entrada, actualizar costo si viene en data
            if data["tipo"] == TipoMovimiento.ENTRADA and data.get("costo_unitario"):
                Insumo.actualizar_costo(data["insumo_id"], data["costo_unitario"])
            
            return {
                "success": True,
                "movimiento_id": result.inserted_id,
                "stock_nuevo": stock_nuevo,
                "stock_anterior": stock_anterior
            }
            
        except Exception as e:
            print(f"Error en registrar_movimiento: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def obtener_historial(cls, filtros=None, limit=100):
        """
        Obtiene el historial de movimientos con filtros
        
        Args:
            filtros (dict): 
                - insumo_id: ObjectId
                - tipo: str
                - fecha_desde: datetime
                - fecha_hasta: datetime
            limit (int): Límite de resultados
        """
        query = filtros or {}
        
        # Filtro de rango de fechas
        if filtros and ("fecha_desde" in filtros or "fecha_hasta" in filtros):
            fecha_query = {}
            if "fecha_desde" in filtros:
                fecha_query["$gte"] = filtros.pop("fecha_desde")
            if "fecha_hasta" in filtros:
                fecha_query["$lte"] = filtros.pop("fecha_hasta")
            query["fecha"] = fecha_query
        
        return list(cls.collection.find(query).sort("fecha", -1).limit(limit))
    
    @classmethod
    def obtener_movimientos_por_insumo(cls, insumo_id, limit=50):
        """Obtiene los movimientos de un insumo específico"""
        return cls.obtener_historial(
            {"insumo_id": ObjectId(insumo_id)},
            limit=limit
        )
    
    @classmethod
    def calcular_consumo_periodo(cls, insumo_id, fecha_desde, fecha_hasta):
        """
        Calcula el consumo total de un insumo en un periodo
        Útil para analítica y proyecciones
        """
        pipeline = [
            {
                "$match": {
                    "insumo_id": ObjectId(insumo_id),
                    "tipo": TipoMovimiento.SALIDA,
                    "fecha": {
                        "$gte": fecha_desde,
                        "$lte": fecha_hasta
                    }
                }
            },
            {
                "$group": {
                    "_id": "$insumo_id",
                    "total_consumido": {"$sum": "$cantidad"},
                    "costo_total": {"$sum": "$costo_total"},
                    "numero_movimientos": {"$sum": 1}
                }
            }
        ]
        
        result = list(cls.collection.aggregate(pipeline))
        return result[0] if result else None


# ==========================================
# MODELO: PROVEEDOR
# ==========================================

class Proveedor:
    """Modelo de Proveedor"""
    collection = db["proveedores"]
    
    @classmethod
    def crear_proveedor(cls, data):
        """Crea un nuevo proveedor"""
        proveedor = {
            "nombre": data["nombre"],
            "razon_social": data.get("razon_social", data["nombre"]),
            "rfc": data.get("rfc", ""),
            "telefono": data.get("telefono", ""),
            "email": data.get("email", ""),
            "direccion": data.get("direccion", ""),
            "contacto_nombre": data.get("contacto_nombre", ""),
            "contacto_telefono": data.get("contacto_telefono", ""),
            "activo": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = cls.collection.insert_one(proveedor)
        return result.inserted_id
    
    @classmethod
    def obtener_todos(cls, solo_activos=True):
        """Obtiene todos los proveedores"""
        query = {"activo": True} if solo_activos else {}
        return list(cls.collection.find(query).sort("nombre", 1))
    
    @classmethod
    def obtener_por_id(cls, proveedor_id):
        """Obtiene un proveedor por ID"""
        return cls.collection.find_one({"_id": ObjectId(proveedor_id)})
    
    @classmethod
    def actualizar(cls, proveedor_id, data):
        """Actualiza un proveedor"""
        data["updated_at"] = datetime.utcnow()
        return cls.collection.update_one(
            {"_id": ObjectId(proveedor_id)},
            {"$set": data}
        )
    
    @classmethod
    def desactivar(cls, proveedor_id):
        """Desactiva un proveedor (soft delete)"""
        return cls.collection.update_one(
            {"_id": ObjectId(proveedor_id)},
            {"$set": {"activo": False, "updated_at": datetime.utcnow()}}
        )


# ==========================================
# MODELO: ALERTA DE STOCK
# ==========================================

class AlertaStock:
    """Modelo de Alertas de Stock Crítico"""
    collection = db["alertas_stock"]
    
    @classmethod
    def generar_alertas_automaticas(cls):
        """
        Genera alertas para todos los insumos con stock crítico
        Se puede ejecutar en un cron job o cada vez que se registra un movimiento
        """
        insumos_criticos = Insumo.obtener_stock_critico()
        alertas_nuevas = []
        
        for insumo in insumos_criticos:
            # Verificar si ya existe una alerta activa para este insumo
            alerta_existente = cls.collection.find_one({
                "insumo_id": insumo["_id"],
                "resuelta": False
            })
            
            if not alerta_existente:
                alerta = {
                    "insumo_id": insumo["_id"],
                    "insumo_nombre": insumo["nombre"],
                    "stock_actual": insumo["stock_actual"],
                    "stock_minimo": insumo["stock_minimo"],
                    "diferencia": insumo["stock_minimo"] - insumo["stock_actual"],
                    "nivel_criticidad": cls._calcular_criticidad(insumo),
                    "resuelta": False,
                    "fecha_generacion": datetime.utcnow(),
                    "fecha_resolucion": None
                }
                
                result = cls.collection.insert_one(alerta)
                alertas_nuevas.append(result.inserted_id)
        
        return alertas_nuevas
    
    @classmethod
    def _calcular_criticidad(cls, insumo):
        """Calcula el nivel de criticidad: alta, media, baja"""
        stock_actual = insumo["stock_actual"]
        stock_minimo = insumo["stock_minimo"]
        
        if stock_actual == 0:
            return "alta"
        elif stock_actual <= stock_minimo * 0.5:
            return "alta"
        elif stock_actual <= stock_minimo * 0.8:
            return "media"
        else:
            return "baja"
    
    @classmethod
    def obtener_alertas_activas(cls):
        """Obtiene todas las alertas no resueltas"""
        return list(cls.collection.find({"resuelta": False}).sort("nivel_criticidad", -1))
    
    @classmethod
    def resolver_alerta(cls, alerta_id, usuario_id):
        """Marca una alerta como resuelta"""
        return cls.collection.update_one(
            {"_id": ObjectId(alerta_id)},
            {
                "$set": {
                    "resuelta": True,
                    "fecha_resolucion": datetime.utcnow(),
                    "resuelto_por": ObjectId(usuario_id)
                }
            }
        )