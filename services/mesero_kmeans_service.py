from config.db import db
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, silhouette_samples
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

    # Nombres legibles de las 4 variables del espacio de características
    FEATURE_LABELS = ["Frecuencia", "Ticket Prom.", "Variabilidad", "Propina Prom."]

    @staticmethod
    def segmentar_mesas(mesero_id: str, dias: int = 90) -> dict:
        hace_n_dias = datetime.now() - timedelta(days=dias)

        pipeline = [
            {"$match": {
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

        # 4 variables → más información para K-Means y PCA
        X = np.array([
            [
                float(m["num_visitas"]),
                float(m["ticket_promedio"]),
                float(m.get("ticket_std") or 0),
                float(m.get("propina_promedio") or 0),
            ]
            for m in mesas_raw
        ])

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # ── K-Means (aprendizaje no supervisado) ───────────────────────
        k = min(3, len(mesas_raw))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)

        # ── Silhouette global + por cluster ────────────────────────────
        sil_score = None
        sil_por_cluster = [None] * k
        if k >= 2 and len(mesas_raw) > k:
            sil_score = round(float(silhouette_score(X_scaled, km.labels_)), 4)
            sil_muestras = silhouette_samples(X_scaled, km.labels_)
            sil_por_cluster_orig = {}
            for ci in range(k):
                mascara = km.labels_ == ci
                if mascara.sum() > 0:
                    sil_por_cluster_orig[ci] = round(float(sil_muestras[mascara].mean()), 4)

        # ── Remap etiquetas: VIP=0, Regular=1, Ocasional=2 ────────────
        centroids_orig = scaler.inverse_transform(km.cluster_centers_)
        # Ordenar por frecuencia + ticket (mayor primero → VIP)
        orden = np.argsort(centroids_orig[:, 0] + centroids_orig[:, 1])[::-1]
        remap = {int(old): int(new) for new, old in enumerate(orden)}
        labels_remap = np.array([remap[int(l)] for l in km.labels_])

        # Reasignar silhouette por cluster al nuevo orden
        if k >= 2 and len(mesas_raw) > k:
            for old_ci, new_ci in remap.items():
                sil_por_cluster[new_ci] = sil_por_cluster_orig.get(old_ci)

        # ── PCA: reducción a 2 componentes para visualización ─────────
        n_comp = min(2, X_scaled.shape[1], X_scaled.shape[0])
        pca = PCA(n_components=n_comp, random_state=42)
        X_pca = pca.fit_transform(X_scaled)

        var_explicada = [round(float(v) * 100, 2) for v in pca.explained_variance_ratio_]
        var_acumulada = round(sum(pca.explained_variance_ratio_) * 100, 2)

        # Cargas (loadings): contribución de cada variable original a cada PC
        feature_labels = MeseroKMeansService.FEATURE_LABELS
        loadings = []
        for pc_idx, componente in enumerate(pca.components_):
            for feat_idx, peso in enumerate(componente):
                loadings.append({
                    "pc":      f"PC{pc_idx + 1}",
                    "feature": feature_labels[feat_idx],
                    "peso":    round(float(peso), 4),
                })

        # ── Construir puntos ───────────────────────────────────────────
        puntos = []
        for i, m in enumerate(mesas_raw):
            cl = int(labels_remap[i])
            meta = _CLUSTER_META[cl] if cl < len(_CLUSTER_META) else _CLUSTER_META[-1]
            puntos.append({
                "mesa":             nombres[i],
                "mesa_numero":      m["_id"],
                "x":                round(float(m["num_visitas"]), 2),
                "y":                round(float(m["ticket_promedio"]), 2),
                "pca_x":            round(float(X_pca[i, 0]), 4),
                "pca_y":            round(float(X_pca[i, 1]), 4) if n_comp >= 2 else 0.0,
                "ticket_std":       round(float(m.get("ticket_std") or 0), 2),
                "ingreso_total":    round(float(m["ingreso_total"]), 2),
                "propina_promedio": round(float(m.get("propina_promedio") or 0), 2),
                "cluster":          cl,
                "label":            meta["label"],
                "color":            meta["color"],
            })

        # ── Resumen por cluster ────────────────────────────────────────
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
                "silhouette":    sil_por_cluster[cl_idx],
                "mesas":         sorted([p["mesa"] for p in grupo]),
            })

        # ── WCSS — método del codo ─────────────────────────────────────
        wcss_elbow = []
        for ki in range(1, min(6, len(mesas_raw))):
            ki_km = KMeans(n_clusters=ki, random_state=42, n_init=10)
            ki_km.fit(X_scaled)
            wcss_elbow.append({"k": ki, "wcss": round(float(ki_km.inertia_), 4)})

        # ── Random Forest explicativo ──────────────────────────────────
        arbol = MeseroRandomForestService.entrenar(X[:, :3], labels_remap, k)

        return {
            "puntos":       puntos,
            "resumen":      resumen,
            "periodo_dias": dias,
            "evaluacion": {
                "silhouette_score":       sil_score,
                "silhouette_por_cluster": sil_por_cluster,
                "inertia":                round(float(km.inertia_), 4),
                "n_mesas":                len(mesas_raw),
                "n_clusters":             k,
                "wcss_elbow":             wcss_elbow,
                "pca": {
                    "varianza_explicada": var_explicada,
                    "varianza_acumulada": var_acumulada,
                    "n_components":       n_comp,
                    "loadings":           loadings,
                    "feature_labels":     feature_labels,
                },
            },
            "arbol": arbol,
        }
