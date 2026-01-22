from config.db import db
from typing import Dict, Any, Tuple, List, Optional
from bson.objectid import ObjectId
from datetime import datetime
import logging
from collections import defaultdict

# Aunque los métodos de catálogos pueden estar en un archivo separado, 
# se mantienen aquí para que toda la lógica de configuración (incluyendo catálogos y auditoría) 
# quede agrupada bajo la gestión de la Financiera.

class GetConfigQueries:
    
    # ------------------------------------------------------------
    # 1. MÉTODOS BASE DE CONFIGURACIÓN
    # ------------------------------------------------------------
    
    @staticmethod
    def _get_default_config(financiera_id: str) -> Dict[str, Any]:
        """Obtiene la configuración actual o crea una por defecto si no existe."""
        
        config = db.configuracion.find_one({"financiera_id": financiera_id})
        
        if not config:
            # Si no existe, crea una configuración por defecto
            default_config = {
                "financiera_id": financiera_id,
                "tasa_interes_anual": 18.0,
                "tasa_mora_mensual": 5.0,
                "plazo_minimo_meses": 6,
                "plazo_maximo_meses": 60,
                "monto_minimo": 5000.00,
                "monto_maximo": 500000.00,
                "dia_corte_mensual": 15,
                "dias_gracia": 5,
                "comision_apertura_porcentaje": 2.0,
                "iva_porcentaje": 16.0,
                "score_minimo_aprobacion": 650,
                "permite_renovacion": True,
                "permite_pago_anticipado": True,
                "penalizacion_pago_anticipado": 0.0,
                "email_notificaciones": "",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.configuracion.insert_one(default_config)
            config = default_config
            
        # Serializar ObjectId si existe
        if "_id" in config:
            config["_id"] = str(config["_id"])
            
        return config

    @staticmethod
    def get_general_config(financiera_id: str) -> Dict[str, Any]:
        """Consulta principal. Obtiene la configuración actual para el formulario general."""
        return GetConfigQueries._get_default_config(financiera_id)
        
    @staticmethod
    def get_dashboard_config_and_stats(financiera_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Obtiene la configuración general y estadísticas rápidas para el dashboard de configuración.
        """
        
        config = GetConfigQueries._get_default_config(financiera_id)
        
        # Estadísticas rápidas (asumiendo que las colecciones tienen 'financiera_id')
        total_clientes = db.clientes.count_documents({"financiera_id": financiera_id})
        total_evaluaciones = db.evaluaciones_credito.count_documents({"evaluacion_financiera_id": financiera_id})
        total_pagos = db.pagos.count_documents({"pago_financiera_id": financiera_id})
        
        # Conteo de catálogos activos
        metodos_pago = db.catalogos.count_documents({"tipo": "metodo_pago", "activo": True})
        estados_credito = db.catalogos.count_documents({"tipo": "estado_credito", "activo": True})
            
        stats = {
            "total_clientes": total_clientes,
            "total_evaluaciones": total_evaluaciones,
            "total_pagos": total_pagos,
            "metodos_pago_count": metodos_pago,
            "estados_credito_count": estados_credito
        }
        
        return config, stats

    # ------------------------------------------------------------
    # 2. MÉTODOS DE CATÁLOGOS (DataTables)
    # ------------------------------------------------------------

    @staticmethod
    def get_catalogos_for_datatable(start: int, length: int, search_value: str, tipo_filtro: str) -> Dict[str, Any]:
        """Obtiene datos de catálogos con paginación y filtros para DataTables."""
        
        query = {}
        
        if tipo_filtro:
            query["tipo"] = tipo_filtro
            
        if search_value:
            query["$or"] = [
                {"nombre": {"$regex": search_value, "$options": "i"}},
                {"descripcion": {"$regex": search_value, "$options": "i"}},
                {"tipo": {"$regex": search_value, "$options": "i"}}
            ]

        total_records = db.catalogos.count_documents({})
        total_filtered = db.catalogos.count_documents(query)

        cursor = db.catalogos.find(query).skip(start).limit(length).sort("orden", 1)
        data = []
        for item in cursor:
            item["_id"] = str(item["_id"])
            data.append(item)

        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }

    @staticmethod
    def view_catalogo_by_id(catalogo_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los detalles de un catálogo específico por su ID de MongoDB (_id)."""
        try:
            object_id = ObjectId(catalogo_id)
        except:
            return None

        catalogo = db.catalogos.find_one({"_id": object_id})

        if catalogo:
            catalogo["_id"] = str(catalogo["_id"])
            return catalogo
        return None

    # ------------------------------------------------------------
    # 3. MÉTODOS DE AUDITORÍA (DataTables)
    # ------------------------------------------------------------

    @staticmethod
    def get_auditoria_for_datatable(start: int, length: int, search_value: str) -> Dict[str, Any]:
        """Obtiene datos de auditoría con paginación y filtros para DataTables."""
        
        query = {}
        
        if search_value:
            query["$or"] = [
                {"usuario_nombre": {"$regex": search_value, "$options": "i"}},
                {"accion": {"$regex": search_value, "$options": "i"}},
                {"modulo": {"$regex": search_value, "$options": "i"}}
            ]

        total_records = db.auditoria.count_documents({})
        total_filtered = db.auditoria.count_documents(query)

        cursor = db.auditoria.find(query).skip(start).limit(length).sort("fecha", -1)
        data = []
        for item in cursor:
            item["_id"] = str(item["_id"])
            data.append(item)

        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }

    @staticmethod
    def view_auditoria_by_id(auditoria_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles de un registro de auditoría por ID."""
        try:
            object_id = ObjectId(auditoria_id)
        except:
            return None

        auditoria = db.auditoria.find_one({"_id": object_id})

        if auditoria:
            auditoria["_id"] = str(auditoria["_id"])
            return auditoria
        return None