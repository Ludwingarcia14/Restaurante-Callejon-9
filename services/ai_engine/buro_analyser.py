# app/services/buro_analyser.py

class BuroAnalyser:
    
    # MOPs considerados de alto riesgo, moderado y bueno
    MOP_ALTO_RIESGO = ["5", "6", "7", "9"]
    MOP_MODERADO = ["3", "4"]
    MOP_BUENO = ["1", "2"]
    
    @staticmethod
    def analizar_mop_buro(solicitud_activa):
        """
        Analiza el MOP (Mes de Observación del Pago) de los créditos activos 
        en el Buró de Crédito del cliente y genera un resumen estructurado.
        Evalúa consistencia de riesgos por otorgante y genera resumen global.
        """
        # 1. Acceder a los datos
        try:
            detail_data = solicitud_activa["documentos"]["buro_credito_fisica"]["analisis_buro"]["STRUCTURED_RAW"]["detail_data"]
        except KeyError:
            return {
                "resumen_mop_titulo": "No disponible",
                "resumen_mop_descripcion": "No hay datos detallados del Buró de Crédito.",
                "mop_alto_riesgo_detectado": False,
                "cuentas_mop_riesgo": [],
                "detalle_creditos_mop": []
            }

        detalle_creditos_mop = []
        mop_alto_riesgo_detectado = False
        cuentas_mop_riesgo = []
        resumen_otorgantes = []

        # 2. Iterar y analizar cada crédito por otorgante
        for credito in detail_data:
            otorgante = credito.get("Otorgante", "Otorgante Desconocido")
            mop_historico = [m for m in credito.get("MOP_Historico", []) if m not in ["0", "U", None, ""]]

            # Contar ocurrencias de MOP por tipo
            cuenta_alto = sum(1 for m in mop_historico if m in BuroAnalyser.MOP_ALTO_RIESGO)
            cuenta_moderado = sum(1 for m in mop_historico if m in BuroAnalyser.MOP_MODERADO)
            cuenta_bueno = sum(1 for m in mop_historico if m in BuroAnalyser.MOP_BUENO)

            # Evaluación por otorgante
            if cuenta_alto >= 3:
                estado_otorgante = "ALTO RIESGO"
                mop_alto_riesgo_detectado = True
                if otorgante not in cuentas_mop_riesgo:
                    cuentas_mop_riesgo.append(otorgante)
            elif cuenta_moderado >= 3:
                estado_otorgante = "RIESGO MODERADO"
            else:
                estado_otorgante = "BUEN COMPORTAMIENTO"

            detalle_creditos_mop.append({
                "otorgante": otorgante,
                "mop_reciente": mop_historico[-1] if mop_historico else "0",
                "cuenta_alto": cuenta_alto,
                "cuenta_moderado": cuenta_moderado,
                "cuenta_bueno": cuenta_bueno,
                "estado_otorgante": estado_otorgante
            })

            resumen_otorgantes.append(estado_otorgante)

            if "ALTO RIESGO" in resumen_otorgantes:
                titulo = "ALTO RIESGO"
                estado = "danger" # Variable de control
                descripcion = "Se detectaron atrasos graves..."
            elif "RIESGO MODERADO" in resumen_otorgantes:
                titulo = "RIESGO MODERADO"
                estado = "warning"
                descripcion = "Se detectaron atrasos menores..."
            else:
                titulo = "BUEN COMPORTAMIENTO"
                estado = "success"
                descripcion = "Todos los créditos presentan buen historial..."

        return {
            "resumen_mop_titulo": titulo,
            "resumen_mop_descripcion": descripcion,
            "mop_alto_riesgo_detectado": mop_alto_riesgo_detectado,
            "cuentas_mop_riesgo": cuentas_mop_riesgo,
            "detalle_creditos_mop": detalle_creditos_mop,
            "estado_resumen": estado
        }
