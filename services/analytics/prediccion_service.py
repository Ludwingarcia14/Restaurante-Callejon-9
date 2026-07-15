from collections import defaultdict
from config.db import db
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import confusion_matrix as sk_confusion_matrix
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler


_DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

_GBR_PARAMS = dict(
    n_estimators=150, max_depth=3, learning_rate=0.08,
    subsample=0.8, random_state=42
)


def _make_model(n_samples):
    # Con log1p Ridge ya captura la curva semanal; GBR para datasets grandes.
    if n_samples < 90:
        return Ridge(alpha=1.0), "Ridge"
    return GradientBoostingRegressor(**_GBR_PARAMS), "Gradient Boosting"


def _featurize(fecha):
    """
    10 features — combinación de dummies directas + codificación cíclica.
    La codificación sin/cos permite que Ridge aprenda patrones semanales/mensuales
    sin necesidad de polinomios de alto orden.
    """
    wd = fecha.weekday()   # 0=lun … 6=dom
    m  = fecha.month       # 1-12
    return [
        wd,                                       # tendencia lineal semanal
        m,                                        # tendencia lineal mensual
        int(wd in (5, 6)),                        # fin de semana
        int(wd == 4),                             # viernes (pico propio)
        int(m in (12, 1, 2)),                     # temporada alta
        fecha.day,                                # quincenas
        np.sin(2 * np.pi * wd / 7),              # onda semanal — componente sin
        np.cos(2 * np.pi * wd / 7),              # onda semanal — componente cos
        np.sin(2 * np.pi * (m - 1) / 12),        # onda mensual — componente sin
        np.cos(2 * np.pi * (m - 1) / 12),        # onda mensual — componente cos
    ]


class PrediccionService:

    @staticmethod
    def predecir_demanda(dias_historial=90, dias_futuro=7):
        fecha_inicio = datetime.now() - timedelta(days=dias_historial)

        pipeline = [
            {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
            {"$group": {
                "_id": {
                    "year":  {"$year":  "$fecha_creacion"},
                    "month": {"$month": "$fecha_creacion"},
                    "day":   {"$dayOfMonth": "$fecha_creacion"},
                },
                "pedidos": {"$sum": 1},
                "ingreso":  {"$sum": "$total"},
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        ]

        docs = list(db.ventas.aggregate(pipeline))
        if len(docs) < 14:
            return {
                "predicciones": [],
                "historico": [],
                "metricas": {},
                "aviso": "Se necesitan al menos 14 días de historial para hacer predicciones.",
            }

        fechas, pedidos_hist = [], []
        for d in docs:
            f = datetime(d["_id"]["year"], d["_id"]["month"], d["_id"]["day"])
            fechas.append(f)
            pedidos_hist.append(int(d["pedidos"]))

        X = np.array([_featurize(f) for f in fechas])
        y = np.array(pedidos_hist, dtype=float)

        # Log-transform: convierte el proceso multiplicativo en aditivo.
        # log(base × dia_mult × mes_mult × ruido) = log(base) + log(dia_mult) + ...
        # Ridge puede ajustar esto exactamente con los features correctos.
        y_log = np.log1p(y)

        # ── Cross-validation temporal ──────────────────────────────────────
        n = len(X)
        # Usar los últimos 3 folds de TimeSeriesSplit: tienen los sets de entrenamiento
        # más grandes, lo que da R² más estables. Los primeros folds (train muy pequeño)
        # producen métricas ruidosas que sesgan el promedio hacia negativo.
        tscv = TimeSeriesSplit(n_splits=5)
        all_splits = list(tscv.split(X))
        # Tomar solo los últimos 3 (los más ricos en datos de entrenamiento)
        valid_splits = all_splits[-3:] if len(all_splits) >= 3 else all_splits
        if not valid_splits:
            cut = max(7, int(n * 0.75))
            valid_splits = [(np.arange(cut), np.arange(cut, n))]

        cv_r2s, cv_maes, cv_rmses = [], [], []
        for tr_idx, va_idx in valid_splits:
            modelo_cv, _ = _make_model(len(tr_idx))
            sc = StandardScaler()
            modelo_cv.fit(sc.fit_transform(X[tr_idx]), y_log[tr_idx])

            # Predecir en escala log, volver a escala original
            yp = np.maximum(0, np.expm1(modelo_cv.predict(sc.transform(X[va_idx]))))

            # R² en escala original (interpretable)
            ss_res = np.sum((y[va_idx] - yp) ** 2)
            ss_tot = np.sum((y[va_idx] - np.mean(y[va_idx])) ** 2)
            cv_r2s.append(float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0)
            cv_maes.append(float(np.mean(np.abs(yp - y[va_idx]))))
            cv_rmses.append(float(np.sqrt(np.mean((yp - y[va_idx]) ** 2))))

        mae  = round(float(np.mean(cv_maes)),  2)
        rmse = round(float(np.mean(cv_rmses)), 2)
        r2   = round(float(np.mean(cv_r2s)),   3)

        # ── Validación visual (tabla 7 días) ───────────────────────────────
        modelo_val, modelo_nombre = _make_model(n - 7)
        sc_val = StandardScaler()
        modelo_val.fit(sc_val.fit_transform(X[:-7]), y_log[:-7])
        y_val      = y[-7:]
        y_pred_val = np.maximum(0, np.expm1(modelo_val.predict(sc_val.transform(X[-7:]))))

        validacion = [
            {
                "fecha":      fechas[-7 + i].strftime("%Y-%m-%d"),
                "dia_semana": _DIAS_SEMANA[fechas[-7 + i].weekday()],
                "real":       int(y_val[i]),
                "pred":       round(float(y_pred_val[i])),
                "error":      round(abs(float(y_pred_val[i]) - float(y_val[i])), 1),
            }
            for i in range(7)
        ]

        # ── Matriz de confusión ────────────────────────────────────────────
        umbral     = float(np.mean(y[:-7]))
        y_val_bin  = (y_val      > umbral).astype(int)
        y_pred_bin = (y_pred_val > umbral).astype(int)
        try:
            cm = sk_confusion_matrix(y_val_bin, y_pred_bin, labels=[0, 1]).tolist()
        except Exception:
            cm = [[0, 0], [0, 0]]

        # ── Modelo final — todos los datos ─────────────────────────────────
        modelo_final, modelo_nombre = _make_model(n)
        scaler = StandardScaler()
        modelo_final.fit(scaler.fit_transform(X), y_log)

        # ── Predicciones futuras ───────────────────────────────────────────
        mean_ingreso = float(np.mean([d.get("ingreso", 0) for d in docs]))
        mean_pedidos = max(float(np.mean(pedidos_hist)), 1)
        avg_ticket   = mean_ingreso / mean_pedidos

        hoy   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        X_fut = np.array([_featurize(hoy + timedelta(days=i)) for i in range(1, dias_futuro + 1)])
        y_fut = np.maximum(0, np.expm1(modelo_final.predict(scaler.transform(X_fut))))

        predicciones = []
        for i, offset in enumerate(range(1, dias_futuro + 1)):
            fp       = hoy + timedelta(days=offset)
            pred_ped = round(float(y_fut[i]))
            predicciones.append({
                "fecha":         fp.strftime("%Y-%m-%d"),
                "dia_semana":    _DIAS_SEMANA[fp.weekday()],
                "pedidos_pred":  pred_ped,
                "ingreso_pred":  round(pred_ped * avg_ticket, 2),
                "es_fin_semana": fp.weekday() in (4, 5, 6),
            })

        resumen = defaultdict(list)
        for p in predicciones:
            resumen[p["dia_semana"]].append(p["pedidos_pred"])
        orden = {d: i for i, d in enumerate(_DIAS_SEMANA)}
        resumen_semana = sorted(
            [{"dia": dia, "pedidos_prom": round(sum(v) / len(v), 1)} for dia, v in resumen.items()],
            key=lambda x: orden.get(x["dia"], 7),
        )

        ingredientes = PrediccionService._estimar_ingredientes(hoy, dias_futuro, y_fut)

        historico = [
            {
                "fecha":      f.strftime("%Y-%m-%d"),
                "dia_semana": _DIAS_SEMANA[f.weekday()],
                "real":       int(p),
            }
            for f, p in zip(fechas[-30:], pedidos_hist[-30:])
        ]

        return {
            "predicciones":          predicciones,
            "historico":             historico,
            "resumen_semana":        resumen_semana,
            "ticket_promedio":       round(avg_ticket, 2),
            "validacion":            validacion,
            "matriz_confusion": {
                "cm":     cm,
                "umbral": round(umbral, 1),
            },
            "metricas": {
                "mae":            mae,
                "rmse":           rmse,
                "r2":             r2,
                "dias_historial": n,
                "n_splits":       len(valid_splits),
                "modelo":         modelo_nombre,
                "datos_limitados": n < 60,
            },
            "ingredientes_estimados": ingredientes,
            "periodo_dias":           dias_historial,
        }

    @staticmethod
    def _estimar_ingredientes(hoy, dias_futuro, y_fut):
        fecha_inicio = hoy - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id":            "$items.nombre",
                "cantidad_total": {"$sum": "$items.cantidad"},
            }},
            {"$sort": {"cantidad_total": -1}},
            {"$limit": 15},
        ]

        items = list(db.ventas.aggregate(pipeline))
        if not items:
            return []

        total_pedidos_hist = float(db.ventas.count_documents(
            {"fecha_creacion": {"$gte": fecha_inicio}}
        )) or 1
        pred_total = float(np.sum(y_fut))

        return [
            {
                "ingrediente":   str(item["_id"]),
                "unidades_pred": int(max(0, round(item["cantidad_total"] / total_pedidos_hist * pred_total))),
                "base_diaria":   round(item["cantidad_total"] / 30, 1),
            }
            for item in items
        ]
