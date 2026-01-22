from config.db import db
from datetime import datetime
import uuid
from typing import Dict, Any

class CreateEvaluacionCommand:
    def __init__(self, data: Dict[str, Any], financiera_id: str):
        self.data = data
        self.financiera_id = financiera_id

    def execute(self) -> str:
        """
        Calcula indicadores de riesgo y guarda una nueva evaluación de crédito.
        Retorna el ID de la evaluación creada.
        """
        cliente_id = str(self.data.get("cliente_id")).strip()
        monto_solicitado = float(self.data.get("monto_solicitado"))
        plazo_meses = int(self.data.get("plazo_meses"))
        tasa_interes = float(self.data.get("tasa_interes"))
        proposito_credito = str(self.data.get("proposito_credito")).strip()
        score_credito = float(self.data.get("score_credito", 0))
        ingresos_mensuales = float(self.data.get("ingresos_mensuales", 0))
        deudas_existentes = float(self.data.get("deudas_existentes", 0))

        # 1. Verificar que el cliente existe
        cliente = db.clientes.find_one({"cliente_id": cliente_id})
        if not cliente:
            raise ValueError("El cliente no existe.")

        # 2. Calcular indicadores de riesgo (Lógica de Negocio)
        tasa_mensual = tasa_interes / 100 / 12
        if tasa_mensual == 0:
            cuota_mensual = monto_solicitado / plazo_meses
        else:
            # Fórmula de cuota de préstamo
            cuota_mensual = monto_solicitado * (tasa_mensual * (1 + tasa_mensual)**plazo_meses) / ((1 + tasa_mensual)**plazo_meses - 1)
            
        deuda_total = deudas_existentes + cuota_mensual
        relacion_deuda_ingreso = (deuda_total / ingresos_mensuales * 100) if ingresos_mensuales > 0 else 0
            
        if score_credito >= 750 and relacion_deuda_ingreso <= 30:
            calificacion_riesgo = "Bajo"
        elif score_credito >= 650 and relacion_deuda_ingreso <= 50:
            calificacion_riesgo = "Medio"
        else:
            calificacion_riesgo = "Alto"
            
        monto_maximo = ingresos_mensuales * plazo_meses * 0.5 if ingresos_mensuales > 0 else monto_solicitado
        recomendacion = "Aprobado" if monto_solicitado <= monto_maximo and calificacion_riesgo != "Alto" else "Rechazado"

        # 3. Crear documento de evaluación
        evaluacion = {
            "evaluacion_id": str(uuid.uuid4()),
            "cliente_id": cliente_id,
            "cliente_nombre": cliente.get("cliente_nombre"),
            "cliente_email": cliente.get("cliente_email"),
            "evaluacion_monto_solicitado": monto_solicitado,
            "evaluacion_plazo_meses": plazo_meses,
            "evaluacion_tasa_interes": tasa_interes,
            "evaluacion_proposito": proposito_credito,
            "evaluacion_score_credito": score_credito,
            "evaluacion_ingresos_mensuales": ingresos_mensuales,
            "evaluacion_deudas_existentes": deudas_existentes,
            "evaluacion_cuota_mensual": round(cuota_mensual, 2),
            "evaluacion_relacion_deuda_ingreso": round(relacion_deuda_ingreso, 2),
            "evaluacion_calificacion_riesgo": calificacion_riesgo,
            "evaluacion_monto_maximo": round(monto_maximo, 2),
            "evaluacion_recomendacion": recomendacion,
            "evaluacion_status": "0", # Pendiente
            "evaluacion_financiera_id": self.financiera_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 4. Guardar en la base de datos
        db.evaluaciones_credito.insert_one(evaluacion)
        return evaluacion["evaluacion_id"]