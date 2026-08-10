from config.db import db
from datetime import datetime, timedelta
import numpy as np

_DIAS = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
_MATCH = {"estado": {"$in": ["pagada", "cerrada"]}}


def _hace(dias):
    return datetime.now() - timedelta(days=dias)


class AnalyticsChartsService:

    @staticmethod
    def tendencias(dias: int = 90) -> dict:
        pipeline = [
            {"$match": {**_MATCH, "fecha_cierre": {"$gte": _hace(dias)}}},
            {"$addFields": {
                "fecha_dia": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha_cierre"}}
            }},
            {"$group": {
                "_id": "$fecha_dia",
                "pedidos": {"$sum": 1},
                "ingresos": {"$sum": "$total"}
            }},
            {"$sort": {"_id": 1}}
        ]
        rows = list(db.comandas.aggregate(pipeline))
        return {
            "success": True,
            "labels":  [r["_id"] for r in rows],
            "pedidos": [r["pedidos"] for r in rows],
            "ingresos": [round(r["ingresos"], 2) for r in rows],
            "periodo_dias": dias,
            "total_pedidos": sum(r["pedidos"] for r in rows),
            "total_ingresos": round(sum(r["ingresos"] for r in rows), 2)
        }

    @staticmethod
    def histograma(dias: int = 90, n_bins: int = 10) -> dict:
        docs = list(db.comandas.find(
            {**_MATCH, "fecha_cierre": {"$gte": _hace(dias)}},
            {"total": 1, "_id": 0}
        ))
        if not docs:
            return {"success": True, "bins": [], "promedio": 0, "mediana": 0, "total": 0}

        totals = np.array(
            [d["total"] for d in docs if d.get("total") is not None and d["total"] > 0],
            dtype=float
        )
        if len(totals) == 0:
            return {"success": True, "bins": [], "promedio": 0, "mediana": 0, "total": 0}

        counts, edges = np.histogram(totals, bins=n_bins)
        bins = [
            {
                "label": f"${int(edges[i])}–${int(edges[i+1])}",
                "count": int(counts[i]),
                "min":   round(float(edges[i]), 2),
                "max":   round(float(edges[i+1]), 2)
            }
            for i in range(len(counts))
        ]
        pico_idx = int(np.argmax(counts))
        return {
            "success":    True,
            "bins":       bins,
            "promedio":   round(float(np.mean(totals)), 2),
            "mediana":    round(float(np.median(totals)), 2),
            "moda_bin":   bins[pico_idx]["label"],
            "total":      len(totals),
            "periodo_dias": dias
        }

    @staticmethod
    def heatmap(dias: int = 90) -> dict:
        pipeline = [
            {"$match": {**_MATCH, "fecha_cierre": {"$gte": _hace(dias)}}},
            {"$addFields": {
                "dia":  {"$dayOfWeek": "$fecha_cierre"},
                "hora": {"$hour":      "$fecha_cierre"}
            }},
            {"$group": {
                "_id": {"dia": "$dia", "hora": "$hora"},
                "comandas": {"$sum": 1}
            }}
        ]
        rows = list(db.comandas.aggregate(pipeline))

        matriz = {}
        for r in rows:
            di = (r["_id"]["dia"] - 1) % 7   # MongoDB: 1=Dom → index 0
            hora = r["_id"]["hora"]
            matriz[(di, hora)] = r["comandas"]

        horas = sorted({h for (_, h) in matriz}) or list(range(11, 23))

        series = []
        for di, nombre in enumerate(_DIAS):
            series.append({
                "name": nombre,
                "data": [{"x": f"{h}h", "y": matriz.get((di, h), 0)} for h in horas]
            })

        total = sum(r["comandas"] for r in rows)

        # peak info
        pico = max(matriz.items(), key=lambda kv: kv[1]) if matriz else ((0, 12), 0)
        pico_dia  = _DIAS[pico[0][0]]
        pico_hora = f"{pico[0][1]}h"

        return {
            "success": True,
            "series":    series,
            "total":     total,
            "pico_dia":  pico_dia,
            "pico_hora": pico_hora,
            "pico_val":  pico[1],
            "periodo_dias": dias
        }

    @staticmethod
    def area(dias: int = 90) -> dict:
        pipeline = [
            {"$match": {**_MATCH, "fecha_cierre": {"$gte": _hace(dias)}}},
            {"$addFields": {
                "semana": {"$week":  "$fecha_cierre"},
                "anio":   {"$year":  "$fecha_cierre"}
            }},
            {"$group": {
                "_id":      {"anio": "$anio", "semana": "$semana"},
                "pedidos":  {"$sum": 1},
                "ingresos": {"$sum": "$total"},
                "fecha_min": {"$min": "$fecha_cierre"}
            }},
            {"$sort": {"_id.anio": 1, "_id.semana": 1}}
        ]
        rows = list(db.comandas.aggregate(pipeline))

        labels, pedidos, ingresos, acumulados = [], [], [], []
        acum = 0.0
        for i, r in enumerate(rows):
            fecha = r.get("fecha_min")
            labels.append(fecha.strftime("%d %b") if fecha else f"Sem {i+1}")
            pedidos.append(r["pedidos"])
            ing = round(r["ingresos"], 2)
            ingresos.append(ing)
            acum += ing
            acumulados.append(round(acum, 2))

        sem_record = labels[int(np.argmax(ingresos))] if ingresos else "—"
        return {
            "success":        True,
            "labels":         labels,
            "pedidos":        pedidos,
            "ingresos":       ingresos,
            "acumulado":      acumulados,
            "total_ingresos": round(acum, 2),
            "total_pedidos":  sum(pedidos),
            "sem_record":     sem_record,
            "n_semanas":      len(rows),
            "periodo_dias":   dias
        }

    @staticmethod
    def boxplot(dias: int = 90) -> dict:
        pipeline = [
            {"$match": {**_MATCH, "fecha_cierre": {"$gte": _hace(dias)}}},
            {"$group": {
                "_id":     "$mesa_numero",
                "totales": {"$push": "$total"}
            }},
            {"$sort": {"_id": 1}}
        ]
        rows = list(db.comandas.aggregate(pipeline))

        mesas, all_totals = [], []
        for r in rows:
            if r["_id"] is None:
                continue
            arr = np.array(
                [t for t in r["totales"] if t is not None and t > 0],
                dtype=float
            )
            if len(arr) < 2:
                continue
            all_totals.extend(arr.tolist())
            q1, q2, q3 = np.percentile(arr, [25, 50, 75])
            mesas.append({
                "mesa":   f"Mesa {r['_id']}",
                "min":    round(float(arr.min()), 2),
                "q1":     round(float(q1), 2),
                "median": round(float(q2), 2),
                "q3":     round(float(q3), 2),
                "max":    round(float(arr.max()), 2),
                "n":      len(arr)
            })

        global_stats = {}
        if all_totals:
            ga = np.array(all_totals)
            g1, g2, g3 = np.percentile(ga, [25, 50, 75])
            global_stats = {
                "min":    round(float(ga.min()), 2),
                "q1":     round(float(g1), 2),
                "median": round(float(g2), 2),
                "q3":     round(float(g3), 2),
                "max":    round(float(ga.max()), 2)
            }

        return {
            "success":      True,
            "mesas":        mesas,
            "global":       global_stats,
            "periodo_dias": dias
        }
