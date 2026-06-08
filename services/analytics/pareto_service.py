from config.db import db
from datetime import datetime, timedelta


class ParetoService:

    @staticmethod
    def get_pareto(dias=90):
        fecha_inicio = datetime.now() - timedelta(days=dias)

        pipeline = [
            {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
            {"$unwind": "$items"},
            {"$match": {"items.nombre": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$items.nombre",
                "ingreso":   {"$sum": {"$multiply": ["$items.precio", "$items.cantidad"]}},
                "cantidad":  {"$sum": "$items.cantidad"},
                "num_ventas": {"$sum": 1},
            }},
            {"$sort": {"ingreso": -1}},
        ]

        items = list(db.ventas.aggregate(pipeline))
        if not items:
            return {"platillos": [], "total_ingreso": 0, "corte_pareto": None}

        total = sum(float(i["ingreso"]) for i in items)
        acumulado = 0.0
        corte_pareto = None  # primer platillo donde acumulado supera 80 %
        resultado = []

        for idx, item in enumerate(items):
            ingreso = float(item["ingreso"])
            pct_individual = round(ingreso / total * 100, 2) if total else 0
            acumulado += pct_individual
            es_pareto = acumulado <= 80.01  # dentro del 80 %

            resultado.append({
                "platillo":      str(item["_id"]),
                "ingreso":       round(ingreso, 2),
                "cantidad":      int(item["cantidad"]),
                "num_ventas":    int(item["num_ventas"]),
                "pct_ingreso":   pct_individual,
                "pct_acumulado": round(acumulado, 2),
                "es_pareto":     es_pareto,
                "rank":          idx + 1,
            })

            if corte_pareto is None and acumulado >= 80:
                corte_pareto = idx + 1

        n_pareto = corte_pareto or len(resultado)
        pct_platillos_clave = round(n_pareto / len(resultado) * 100, 1) if resultado else 0

        return {
            "platillos":          resultado,
            "total_ingreso":      round(total, 2),
            "total_platillos":    len(resultado),
            "n_pareto":           n_pareto,
            "pct_platillos_clave": pct_platillos_clave,
            "periodo_dias":       dias,
        }
