from config.db import db
from typing import Dict, Any

class GetDashboardQueries:
    @staticmethod
    def get_finance_kpis(financiera_id: str) -> Dict[str, Any]:
        """Calcula el total cobrado, saldo pendiente y pagos en mora para el dashboard."""
        
        # 1. Total de pagos recibidos
        pagos = db.pagos.find({"pago_financiera_id": financiera_id})
        total_cobrado = sum(p.get("pago_monto", 0) for p in pagos)
        
        # 2. Créditos por cobrar (evaluaciones aprobadas)
        evaluaciones = db.evaluaciones_credito.find({
            "evaluacion_financiera_id": financiera_id,
            "evaluacion_recomendacion": "Aprobado"
        })
        total_por_cobrar = sum(e.get("evaluacion_monto_solicitado", 0) for e in evaluaciones)
        
        saldo_pendiente = total_por_cobrar - total_cobrado
        
        # 3. Pagos en mora
        pagos_mora = db.pagos.count_documents({
            "pago_financiera_id": financiera_id,
            "pago_tiene_mora": True
        })
        
        # 4. Estadísticas para el dashboard
        stats = {
            "total_cobrado": round(total_cobrado, 2),
            "saldo_pendiente": round(saldo_pendiente, 2),
            "pagos_mora": pagos_mora,
            "total_pagos": db.pagos.count_documents({"pago_financiera_id": financiera_id})
        }
        return stats