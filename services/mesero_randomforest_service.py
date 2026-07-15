from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import export_text
import numpy as np


_FEATURE_LABELS = ["Frecuencia", "Ticket Promedio", "Variabilidad"]

_CLUSTER_LABELS = ["Mesas VIP", "Mesas Regulares", "Mesas Ocasionales"]


class MeseroRandomForestService:

    @staticmethod
    def entrenar(X_raw: np.ndarray, labels: np.ndarray, k: int) -> dict:
        nombres_clase = [_CLUSTER_LABELS[i] for i in range(k)]

        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=3,
            random_state=42,
            oob_score=True,
        )
        rf.fit(X_raw, labels)

        imp_mean = rf.feature_importances_
        imp_std  = np.std([t.feature_importances_ for t in rf.estimators_], axis=0)

        importancias = sorted(
            [
                {
                    "feature":     _FEATURE_LABELS[i],
                    "importancia": round(float(imp_mean[i]), 4),
                    "std":         round(float(imp_std[i]),  4),
                }
                for i in range(len(_FEATURE_LABELS))
            ],
            key=lambda x: x["importancia"],
            reverse=True,
        )

        diffs = [
            float(np.sum((t.feature_importances_ - imp_mean) ** 2))
            for t in rf.estimators_
        ]
        arbol_rep = rf.estimators_[int(np.argmin(diffs))]
        reglas = export_text(arbol_rep, feature_names=_FEATURE_LABELS)

        return {
            "reglas":              reglas,
            "feature_importances": importancias,
            "clases":              nombres_clase,
            "n_estimators":        rf.n_estimators,
            "oob_score":           round(float(rf.oob_score_), 4),
        }
