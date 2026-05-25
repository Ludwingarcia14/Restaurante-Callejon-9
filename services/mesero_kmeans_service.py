from config.db import db
from bson import ObjectId
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import numpy as np

from services.mesero_randomforest_service import MeseroRandomForestService


_CLUSTER_META = [
    {
        "label": "Mesas VIP",
        "color": "#f59e0b",
        "bg": "#fef3c7",
        "icon": "bi-star-fill",
        "recomendacion": "Son tus mesas más rentables. Asigna atención prioritaria y busca fidelizar a estos clientes con un servicio excepcional.",
    },
    {
        "label": "Mesas Regulares",
        "color": "#3b82f6",
        "bg": "#dbeafe",
        "icon": "bi-circle-fill",
        "recomendacion": "Buen potencial de crecimiento. Mantén consistencia en el servicio y considera pequeños incentivos para subir su ticket.",
    },
    {
        "label": "Mesas Ocasionales",
        "color": "#94a3b8",
        "bg": "#f1f5f9",
        "icon": "bi-circle",
        "recomendacion": "Baja frecuencia de uso. Evalúa promociones o menú especial para atraerlos con más regularidad.",
    },
]


class MeseroKMeansService:

    @staticmethod
    def segmentar_mesas(mesero_id: str, dias: int = 90) -> dict:
        mesero_oid = ObjectId(mesero_id)
        hace_n_dias = datetime.now() - timedelta(days=dias)

        pipeline = [
            {"$match": {
                "mesero_id": mesero_oid,
                "estado": {"$in": ["pagada", "cerrada"]},
                "fecha_cierre": {"$gte": hace_n_dias}
            }},
            {"$group": {
                "_id": "$mesa_numero",
                "num_visitas":      {"$sum": 1},
                "ticket_promedio":  {"$avg": "$total"},
                "ticket_std":       {"$stdDevPop": "$total"},
                "propina_promedio": {"$avg": "$propina"},
                "ingreso_total":    {"$sum": "$total"}
            }},
            {"$match": {"num_visitas": {"$gte": 1}}},
            {"$sort": {"ingreso_total": -1}}
        ]
        mesas_raw = list(db.comandas.aggregate(pipeline))

        if len(mesas_raw) < 3:
            return {
                "puntos": [], "resumen": [],
                "aviso": "Se necesitan al menos 3 mesas con historial para ejecutar K-Means."
            }

        nombres = [f"Mesa {m['_id']}" for m in mesas_raw]

        X_kmeans = np.array([
            [float(m["num_visitas"]), float(m["ticket_promedio"])]
            for m in mesas_raw
        ])
        X_arbol = np.array([
            [
                float(m["num_visitas"]),
                float(m["ticket_promedio"]),
                float(m.get("ticket_std") or 0),
            ]
            for m in mesas_raw
        ])

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_kmeans)

        k = min(3, len(mesas_raw))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)

        sil_score = None
        if k >= 2 and len(mesas_raw) > k:
            sil_score = round(float(silhouette_score(X_scaled, km.labels_)), 4)

        centroids_orig = scaler.inverse_transform(km.cluster_centers_)
        orden = np.argsort(centroids_orig[:, 0] + centroids_orig[:, 1])[::-1]
        remap = {old: new for new, old in enumerate(orden)}
        labels_remap = np.array([remap[l] for l in km.labels_])

        puntos = []
        for i, m in enumerate(mesas_raw):
            cl = int(labels_remap[i])
            meta = _CLUSTER_META[cl] if cl < len(_CLUSTER_META) else _CLUSTER_META[-1]
            puntos.append({
                "mesa":             nombres[i],
                "mesa_numero":      m["_id"],
                "x":                round(float(m["num_visitas"]), 2),
                "y":                round(float(m["ticket_promedio"]), 2),
                "ticket_std":       round(float(m.get("ticket_std") or 0), 2),
                "ingreso_total":    round(float(m["ingreso_total"]), 2),
                "propina_promedio": round(float(m["propina_promedio"]), 2),
                "cluster":          cl,
                "label":            meta["label"],
                "color":            meta["color"],
            })

        resumen = []
        for cl_idx, meta in enumerate(_CLUSTER_META[:k]):
            grupo = [p for p in puntos if p["cluster"] == cl_idx]
            if not grupo:
                continue
            resumen.append({
                "cluster":       cl_idx,
                "label":         meta["label"],
                "color":         meta["color"],
                "bg":            meta["bg"],
                "icon":          meta["icon"],
                "recomendacion": meta["recomendacion"],
                "num_mesas":     len(grupo),
                "ticket_prom":   round(sum(p["y"] for p in grupo) / len(grupo), 2),
                "visitas_prom":  round(sum(p["x"] for p in grupo) / len(grupo), 1),
                "mesas":         sorted([p["mesa"] for p in grupo]),
            })

        elbow = []
        for ki in range(1, min(6, len(mesas_raw))):
            ki_km = KMeans(n_clusters=ki, random_state=42, n_init=10)
            ki_km.fit(X_scaled)
            elbow.append({"k": ki, "inertia": round(float(ki_km.inertia_), 4)})

        arbol = MeseroRandomForestService.entrenar(X_arbol, labels_remap, k)

        return {
            "puntos":       puntos,
            "resumen":      resumen,
            "periodo_dias": dias,
            "evaluacion": {
                "silhouette_score": sil_score,
                "inertia":          round(float(km.inertia_), 4),
                "n_mesas":          len(mesas_raw),
                "n_clusters":       k,
                "elbow":            elbow,
            },
            "arbol": arbol,
        }
