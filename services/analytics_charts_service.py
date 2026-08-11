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
    def histograma(dias: int = 90) -> dict:
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

        # Bins alineados a las zonas de estrategia comercial (no equiespaciados
        # sobre min–max como antes): cortes de $100 hasta $1,000 y un bin final
        # abierto "≥ $1,000" (umbral de la promoción 1 invitado gratis).
        # El corte en 401 (no 400) hace que un ticket de exactamente $400 caiga
        # en la zona "incrementar" ($200–$400) y $401 en "alcanzar meta".
        edges = [0, 100, 200, 300, 401, 500, 600, 700, 800, 900, 1000,
                 max(1000.01, float(totals.max()))]
        counts, edges = np.histogram(totals, bins=edges)

        def _zona(lo):
            if lo >= 1000: return "mantener"      # ≥ $1,000 → promoción
            if lo >= 401:  return "meta"          # $401–$999 → acercar a $1,000
            if lo >= 200:  return "incrementar"   # $200–$400 → combos
            return "base"                         # < $200, fuera de estrategia

        bins = []
        for i in range(len(counts)):
            lo, hi = float(edges[i]), float(edges[i + 1])
            label = "≥ $1,000" if lo >= 1000 else f"${int(lo)}–${int(hi) - 1 if hi in (401,) else int(hi)}"
            bins.append({
                "label": label,
                "count": int(counts[i]),
                "min":   round(lo, 2),
                "max":   round(hi, 2),
                "zona":  _zona(lo)
            })
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

        horas = list(range(24))  # las 24 horas siempre presentes, en orden cronológico

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
    def area(dias: int = 90, fecha_inicio=None, fecha_fin_exclusiva=None) -> dict:
        """
        Ingresos semanales (área + acumulado).

        Por defecto usa "últimos N días" (comportamiento original, sin cambios).
        Si se proveen fecha_inicio/fecha_fin_exclusiva (datetime), filtra por ese
        rango explícito en su lugar — pensado para el selector de semanas del
        frontend, que ya calcula límites sin solape (fin exclusivo) antes de
        llamar aquí. La agregación/agrupación por semana no se modifica.
        """
        if fecha_inicio is not None and fecha_fin_exclusiva is not None:
            filtro_fecha = {"$gte": fecha_inicio, "$lt": fecha_fin_exclusiva}
        else:
            filtro_fecha = {"$gte": _hace(dias)}

        pipeline = [
            {"$match": {**_MATCH, "fecha_cierre": filtro_fecha}},
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
        if fecha_inicio is not None and fecha_fin_exclusiva is not None:
            periodo_dias = max((fecha_fin_exclusiva - fecha_inicio).days, 1)
        else:
            periodo_dias = dias
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
            "periodo_dias":   periodo_dias
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
