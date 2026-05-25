from config.db import db
from bson import ObjectId
from datetime import datetime, timedelta


class MeseroDiagnosticoService:

    @staticmethod
    def diagnostico_datos(mesero_id: str, dias: int = 90) -> dict:
        mesero_oid = ObjectId(mesero_id)
        hace_n_dias = datetime.now() - timedelta(days=dias)

        match = {
            "mesero_id":    mesero_oid,
            "estado":       {"$in": ["pagada", "cerrada"]},
            "fecha_cierre": {"$gte": hace_n_dias},
        }

        global_agg = list(db.comandas.aggregate([
            {"$match": match},
            {"$group": {
                "_id":               None,
                "total":             {"$sum": 1},
                "fecha_min":         {"$min": "$fecha_cierre"},
                "fecha_max":         {"$max": "$fecha_cierre"},
                "ticket_global_avg": {"$avg": "$total"},
                "ticket_global_std": {"$stdDevPop": "$total"},
            }}
        ]))

        if not global_agg:
            return {"error": "Sin datos en el periodo", "total_comandas": 0}

        g = global_agg[0]

        por_mesa = list(db.comandas.aggregate([
            {"$match": match},
            {"$group": {
                "_id":              "$mesa_numero",
                "n":                {"$sum": 1},
                "ticket_min":       {"$min": "$total"},
                "ticket_max":       {"$max": "$total"},
                "ticket_avg":       {"$avg": "$total"},
                "ticket_std":       {"$stdDevPop": "$total"},
                "propina_pct_avg":  {"$avg": "$porcentaje_propina"},
                "comensales_avg":   {"$avg": "$num_comensales"},
            }},
            {"$sort": {"_id": 1}},
        ]))

        metodos = list(db.comandas.aggregate([
            {"$match": match},
            {"$group": {"_id": "$metodo_pago", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]))

        return {
            "total_comandas":    int(g["total"]),
            "fecha_inicio":      g["fecha_min"].strftime("%d/%m/%Y") if g.get("fecha_min") else None,
            "fecha_fin":         g["fecha_max"].strftime("%d/%m/%Y") if g.get("fecha_max") else None,
            "ticket_global_avg": round(float(g["ticket_global_avg"]), 2),
            "ticket_global_std": round(float(g["ticket_global_std"]), 2),
            "por_mesa": [
                {
                    "mesa":           m["_id"],
                    "registros":      m["n"],
                    "ticket_min":     round(float(m["ticket_min"]), 2),
                    "ticket_max":     round(float(m["ticket_max"]), 2),
                    "ticket_avg":     round(float(m["ticket_avg"]), 2),
                    "ticket_std":     round(float(m.get("ticket_std") or 0), 2),
                    "propina_pct_avg": round(float(m.get("propina_pct_avg") or 0), 1),
                    "comensales_avg": round(float(m.get("comensales_avg") or 0), 1),
                }
                for m in por_mesa
            ],
            "metodos_pago": [{"metodo": m["_id"], "count": m["count"]} for m in metodos],
            "periodo_dias": dias,
        }
