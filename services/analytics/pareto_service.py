from config.db import db
from datetime import datetime, timedelta


class ParetoService:

    @staticmethod
    def get_pareto(start_date=None, end_date=None, dias=90):
        """
        Calcula el análisis Pareto 80/20 de ingresos por platillo.

        Acepta un rango explícito (start_date/end_date, ambos datetime) o,
        si no se proveen, cae de vuelta al comportamiento legado de
        "últimos N días" (parámetro `dias`) para no romper consumidores
        que aún no fueron migrados al date range picker.
        """
        if start_date and end_date:
            fecha_inicio = start_date
            fecha_fin = end_date
        else:
            fecha_fin = datetime.now()
            fecha_inicio = fecha_fin - timedelta(days=dias)

        # Rango inclusivo de todo el día final (por si end_date llega sin hora, ej. 00:00:00)
        fecha_fin_query = fecha_fin
        if fecha_fin_query.hour == 0 and fecha_fin_query.minute == 0 and fecha_fin_query.second == 0:
            fecha_fin_query = fecha_fin_query.replace(hour=23, minute=59, second=59, microsecond=999999)

        pipeline = [
            {"$match": {"fecha_creacion": {"$gte": fecha_inicio, "$lte": fecha_fin_query}}},
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

        periodo_dias = max((fecha_fin - fecha_inicio).days, 1)
        rango = {
            "fecha_inicio": fecha_inicio.strftime("%d/%m/%Y"),
            "fecha_fin":    fecha_fin.strftime("%d/%m/%Y"),
            "periodo_dias": periodo_dias,
        }

        items = list(db.ventas.aggregate(pipeline))
        if not items:
            return {
                "platillos": [], "total_ingreso": 0, "corte_pareto": None,
                "total_platillos": 0, "n_pareto": 0, "pct_platillos_clave": 0,
                **rango,
            }

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
            **rango,
        }
