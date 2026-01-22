from config.db import db
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict
from bson.objectid import ObjectId

class GetProyeccionQueries:
    @staticmethod
    def get_liquidaciones_report(fecha_inicio_str: str, fecha_fin_str: str) -> Dict[str, Any]:
        """
        Obtiene datos de liquidaciones dentro de un rango de fechas, calcula KPIs y formatea para gráficos.
        """
        # 1. Conversión de fechas
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

        # 2. Construir consulta MongoDB (prestamos liquidados en el rango de vencimiento)
        query = {
            "prestamo_estado": "Pagado",
            "prestamo_fecha_vencimiento": {"$gte": fecha_inicio, "$lte": fecha_fin}
        }
        cursor = db.prestamos.find(query).sort("prestamo_fecha_vencimiento", 1)
        lista_prestamos = list(cursor)

        if not lista_prestamos:
            return {
                "stats": {"total_liquidado": 0, "prestamos_count": 0, "monto_promedio": 0},
                "tabla_liquidaciones": [],
                "chart_data": {"labels": [], "data": []}
            }

        # 3. Buscar nombres de clientes asociados
        cliente_ids = [p.get("cliente_id") for p in lista_prestamos if p.get("cliente_id")]
        cliente_ids_validos = [cid for cid in cliente_ids if ObjectId.is_valid(cid)]

        clientes_cursor = db.clientes.find({"_id": {"$in": [ObjectId(cid) for cid in cliente_ids_validos]}})
        cliente_map = {
            str(c["_id"]): f"{c.get('cliente_nombre', '')} {c.get('cliente_apellidos', '')}".strip()
            for c in clientes_cursor
        }
        
        # 4. Preparar datos para tabla y gráfico
        total_liquidado = 0
        tabla_liquidaciones = []
        liquidaciones_por_dia = defaultdict(float)

        for item in lista_prestamos:
            monto = float(item.get("prestamo_monto", 0))
            total_liquidado += monto

            fecha_venc = item.get("prestamo_fecha_vencimiento")
            if isinstance(fecha_venc, str):
                fecha_venc = datetime.fromisoformat(fecha_venc.replace("Z", ""))
            
            cliente_id = str(item.get("cliente_id"))
            cliente_nombre = cliente_map.get(ObjectId(cliente_id), "Cliente desconocido")

            # Datos para tabla
            tabla_liquidaciones.append({
                "cliente_nombre": cliente_nombre,
                "credito_id": str(item.get("_id")),
                "monto_pagado": monto,
                "fecha_liquidacion": fecha_venc.strftime('%d/%m/%Y')
            })

            # Datos para gráfico (agrupados por día)
            fecha_str = fecha_venc.strftime('%Y-%m-%d')
            liquidaciones_por_dia[fecha_str] += monto

        # 5. KPIs
        count = len(tabla_liquidaciones)
        monto_promedio = total_liquidado / count if count > 0 else 0

        stats = {
            "total_liquidado": round(total_liquidado, 2),
            "prestamos_count": count,
            "monto_promedio": round(monto_promedio, 2)
        }

        # 6. Formato gráfico
        labels_ordenados = sorted(liquidaciones_por_dia.keys())
        chart_data = {
            "labels": [datetime.strptime(f, '%Y-%m-%d').strftime('%d/%m') for f in labels_ordenados],
            "data": [liquidaciones_por_dia[f] for f in labels_ordenados]
        }
        
        # 7. Retornar resultado
        return {
            "stats": stats,
            "tabla_liquidaciones": tabla_liquidaciones,
            "chart_data": chart_data
        }

    @staticmethod
    def get_mora_data(financiera_id: str) -> List[Dict[str, Any]]:
        """Obtiene datos de mora filtrados por financiera_id."""
        cursor = db.mora.find({"financiera_id": financiera_id}).sort("fecha_mora", 1)
        data = []
        for item in cursor:
            item["_id"] = str(item["_id"])
            data.append(item)
        return data

    @staticmethod
    def get_pagos_data(financiera_id: str) -> List[Dict[str, Any]]:
        """Obtiene datos de pagos filtrados por financiera_id."""
        cursor = db.pagos.find({"financiera_id": financiera_id}).sort("fecha_pago", 1)
        data = []
        for item in cursor:
            item["_id"] = str(item["_id"])
            data.append(item)
        return data

    @staticmethod
    def get_prestamos_data(financiera_id: str) -> List[Dict[str, Any]]:
        """Obtiene datos de préstamos filtrados por financiera_id."""
        cursor = db.prestamos.find({"financiera_id": financiera_id}).sort("fecha_prestamo", 1)
        data = []
        for item in cursor:
            item["_id"] = str(item["_id"])
            data.append(item)
        return data