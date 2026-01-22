from utils.parsers import limpiar_moneda, parsear_rango_moneda

class MatchEngine:
    def __init__(self):
        self.pesos = {"perfil": 20, "monto": 25, "ingresos": 30, "buro": 15, "region": 10}

    def evaluar_compatibilidad(self, cliente_data, financiera):
        score = 0
        razones = []
        
        tipo_cte = cliente_data.get('tipo_persona', '').lower()
        perfil_fin = financiera.get('financiera_perfilsolicitante', '').lower()
        if ('fisica' in tipo_cte and 'fisica' not in perfil_fin) and ('moral' in tipo_cte and 'moral' not in perfil_fin):
            return {"score": 0, "nivel": "rechazado", "razon": "Tipo de persona no admitido"}
        score += self.pesos['perfil']

        monto = cliente_data.get('monto_solicitado', 0)
        min_f, max_f = parsear_rango_moneda(financiera.get('financiera_montoFinanciacion'))
        if min_f <= monto <= max_f: score += self.pesos['monto']
        elif monto < min_f: razones.append(f"Monto bajo (Mín: ${min_f:,.0f})")
        else: return {"score": 0, "nivel": "rechazado", "razon": "Monto excede límite"}

        ingresos = cliente_data.get('ingresos_promedio', 0)
        req_dep = limpiar_moneda(financiera.get('financiera_DepositosMinimos'))
        req_sal = limpiar_moneda(financiera.get('financiera_SaldosPromediosM'))
        requisito = max(req_dep, req_sal)
        if ingresos >= requisito: score += self.pesos['ingresos']
        elif ingresos >= (requisito * 0.7): 
            score += self.pesos['ingresos'] * 0.5
            razones.append("Ingresos ajustados")
        else: razones.append("Ingresos insuficientes")

        score_buro = cliente_data.get('score_buro', 0)
        min_buro = float(financiera.get('financiera_scoreminimoburo', 0) or 0)
        if score_buro >= min_buro: score += self.pesos['buro']

        nivel = "bajo"
        if score >= 85: nivel = "perfecto"
        elif 50 <= score < 85: nivel = "potencial"

        return {
            "id": str(financiera["_id"]),
            "nombre": financiera["financiera_nombre"],
            "score": score,
            "nivel": nivel,
            "aliado_email": financiera.get("financiera_correo"),
            "detalles": razones
        }