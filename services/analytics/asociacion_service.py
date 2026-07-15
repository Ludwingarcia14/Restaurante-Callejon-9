from config.db import db
from datetime import datetime, timedelta
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


class AsociacionService:

    @staticmethod
    def get_reglas(min_support=0.04, min_confidence=0.25, dias=90, top_n=20):
        fecha_inicio = datetime.now() - timedelta(days=dias)

        # Extraer transacciones: una lista de items por comanda
        ventas = list(db.ventas.find(
            {"fecha_creacion": {"$gte": fecha_inicio}, "items": {"$exists": True, "$ne": []}},
            {"items.nombre": 1, "_id": 0}
        ))

        transacciones = []
        for v in ventas:
            items = v.get("items", [])
            nombres = list({str(i.get("nombre", "")).strip() for i in items if i.get("nombre")})
            if len(nombres) >= 2:
                transacciones.append(nombres)

        if len(transacciones) < 10:
            return {
                "reglas": [],
                "n_transacciones": len(transacciones),
                "aviso": "Se necesitan al menos 10 comandas con 2+ platillos para encontrar asociaciones.",
            }

        te = TransactionEncoder()
        te_array = te.fit(transacciones).transform(transacciones)
        df = pd.DataFrame(te_array, columns=te.columns_)

        try:
            frecuentes = apriori(df, min_support=min_support, use_colnames=True, max_len=3)
        except Exception:
            return {"reglas": [], "n_transacciones": len(transacciones), "aviso": "No se encontraron itemsets frecuentes con los parámetros dados."}

        if frecuentes.empty:
            return {"reglas": [], "n_transacciones": len(transacciones), "aviso": "No se encontraron itemsets frecuentes. Intenta reducir el soporte mínimo."}

        try:
            reglas = association_rules(frecuentes, metric="confidence", min_threshold=min_confidence, num_itemsets=len(frecuentes))
        except Exception:
            return {"reglas": [], "n_transacciones": len(transacciones), "aviso": "No se pudieron calcular reglas con los parámetros dados."}

        if reglas.empty:
            return {"reglas": [], "n_transacciones": len(transacciones), "aviso": "No se encontraron reglas con esa confianza mínima."}

        reglas = reglas.sort_values("lift", ascending=False).head(top_n)

        resultado = []
        for _, r in reglas.iterrows():
            antecedentes = list(r["antecedents"])
            consecuentes = list(r["consequents"])
            resultado.append({
                "si_piden":   antecedentes,
                "tambien_piden": consecuentes,
                "soporte":    round(float(r["support"]) * 100, 1),
                "confianza":  round(float(r["confidence"]) * 100, 1),
                "lift":       round(float(r["lift"]), 2),
                "descripcion": f"Quien pide {' + '.join(antecedentes)} también pide {' + '.join(consecuentes)} en el {round(float(r['confidence'])*100,0):.0f}% de los casos.",
            })

        return {
            "reglas":          resultado,
            "n_transacciones": len(transacciones),
            "n_items_unicos":  len(te.columns_),
            "min_soporte":     round(min_support * 100, 1),
            "min_confianza":   round(min_confidence * 100, 1),
            "periodo_dias":    dias,
        }
