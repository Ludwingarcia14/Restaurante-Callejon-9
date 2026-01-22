# services/scoring_service.py
import math

class FinancialScoringService:
    
    @staticmethod
    def calcular_score(analisis_ia):
        """
        Calcula un puntaje crediticio interno basado en el análisis de la IA.
        Retorna un diccionario con el score, capacidad de pago y nivel de riesgo.
        """
        # 1. Extraer datos (Asumiendo que la IA devuelve estos campos)
        ingresos_mensuales = analisis_ia.get('promedio_depositos', 0)
        egresos_mensuales = analisis_ia.get('promedio_retiros', 0)
        saldo_promedio = analisis_ia.get('saldo_promedio', 0)
        num_sobregiros = analisis_ia.get('num_sobregiros', 0) # Cheques devueltos o saldos negativos

        score = 0
        
        # --- REGLA 1: Flujo de Efectivo (40 Puntos) ---
        # Si le queda dinero al final del mes
        cash_flow = ingresos_mensuales - egresos_mensuales
        if cash_flow > (ingresos_mensuales * 0.20): # Le sobra el 20%
            score += 40
        elif cash_flow > 0:
            score += 20
            
        # --- REGLA 2: Solvencia / Saldo Promedio (30 Puntos) ---
        # Un saldo promedio alto indica estabilidad
        if saldo_promedio > 20000: 
            score += 30
        elif saldo_promedio > 5000:
            score += 15

        # --- REGLA 3: Comportamiento Negativo (Penalización) ---
        # Si tiene sobregiros o saldos negativos frecuentes
        if num_sobregiros > 0:
            score -= (num_sobregiros * 10)

        # --- REGLA 4: Escala de Ingresos (30 Puntos) ---
        # Mayor ingreso = Mayor capacidad teórica
        if ingresos_mensuales > 50000:
            score += 30
        elif ingresos_mensuales > 15000:
            score += 15

        # Normalizar Score (0 a 100)
        score = max(0, min(100, score))

        # Determinar Nivel y Capacidad Máxima de Pago Mensual (aprox 30% del flujo libre)
        capacidad_pago = max(0, cash_flow * 0.30)
        
        nivel = "Bajo"
        color = "red"
        mensaje = "Se requiere aval o garantía adicional."
        
        if score >= 80:
            nivel = "Excelente"
            color = "green"
            mensaje = "Alta probabilidad de aprobación rápida."
        elif score >= 50:
            nivel = "Bueno"
            color = "orange"
            mensaje = "Aprobable con revisión manual estándar."

        return {
            "score": score,
            "nivel": nivel,
            "color": color,
            "mensaje": mensaje,
            "capacidad_pago_mensual": round(capacidad_pago, 2),
            "cash_flow": round(cash_flow, 2)
        }