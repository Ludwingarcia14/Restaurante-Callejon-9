from config.db import db
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler


_DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class PrediccionService:

    @staticmethod
    def predecir_demanda(dias_historial=90, dias_futuro=7):
        fecha_inicio = datetime.now() - timedelta(days=dias_historial)

        # ── EXTRACCIÓN ─────────────────────────────────────────────────────
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
                "comensales": {"$sum": 0},
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

        # ── TRANSFORMACIÓN ─────────────────────────────────────────────────
        fechas, pedidos_hist = [], []
        for d in docs:
            f = datetime(d["_id"]["year"], d["_id"]["month"], d["_id"]["day"])
            fechas.append(f)
            pedidos_hist.append(int(d["pedidos"]))

        def featurize(fecha):
            return [
                fecha.weekday(),                    # 0=lun … 6=dom
                fecha.month,                        # 1-12
                int(fecha.weekday() in (4, 5, 6)),  # fin de semana
                int(fecha.month in (12, 1, 2)),     # temporada alta (dic-feb)
                fecha.day,                          # día del mes
            ]

        X = np.array([featurize(f) for f in fechas])
        y = np.array(pedidos_hist, dtype=float)

        # Dejar últimos 7 días como validación
        X_train, y_train = X[:-7], y[:-7]
        X_val,   y_val   = X[-7:], y[-7:]

        scaler  = StandardScaler()
        X_tr_s  = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)

        modelo = GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            subsample=0.8, random_state=42
        )
        modelo.fit(X_tr_s, y_train)

        y_pred_val = np.maximum(0, modelo.predict(X_val_s))
        mae  = float(np.mean(np.abs(y_pred_val - y_val)))
        rmse = float(np.sqrt(np.mean((y_pred_val - y_val) ** 2)))
        ss_res = np.sum((y_val - y_pred_val) ** 2)
        ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # ── CARGA / PREDICCIÓN ─────────────────────────────────────────────
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        X_fut = np.array([featurize(hoy + timedelta(days=i)) for i in range(1, dias_futuro + 1)])
        X_fut_s = scaler.transform(X_fut)
        y_fut   = np.maximum(0, modelo.predict(X_fut_s))

        predicciones = []
        for i, dias_adelante in enumerate(range(1, dias_futuro + 1)):
            fecha_pred = hoy + timedelta(days=dias_adelante)
            pred_pedidos = round(float(y_fut[i]))
            ticket_prom  = float(np.mean(y) / max(np.mean(pedidos_hist), 1)) if pedidos_hist else 0
            predicciones.append({
                "fecha":          fecha_pred.strftime("%Y-%m-%d"),
                "dia_semana":     _DIAS_SEMANA[fecha_pred.weekday()],
                "pedidos_pred":   pred_pedidos,
                "ingreso_pred":   round(pred_pedidos * float(np.mean([d.get("ingreso", 0) for d in docs])) / max(float(np.mean(pedidos_hist)), 1), 2),
                "es_fin_semana":  fecha_pred.weekday() in (4, 5, 6),
            })

        # Ingredientes estimados (top items × predicción de volumen)
        ingredientes = PrediccionService._estimar_ingredientes(hoy, dias_futuro, y_fut)

        historico = [
            {
                "fecha":     f.strftime("%Y-%m-%d"),
                "dia_semana": _DIAS_SEMANA[f.weekday()],
                "real":      int(p),
            }
            for f, p in zip(fechas[-30:], pedidos_hist[-30:])
        ]

        return {
            "predicciones": predicciones,
            "historico":    historico,
            "metricas": {
                "mae":          round(mae, 2),
                "rmse":         round(rmse, 2),
                "r2":           round(r2, 3),
                "dias_historial": len(docs),
            },
            "ingredientes_estimados": ingredientes,
            "periodo_dias":   dias_historial,
        }

    @staticmethod
    def _estimar_ingredientes(hoy, dias_futuro, y_fut):
        fecha_inicio = hoy - timedelta(days=30)

        pipeline = [
            {"$match": {"fecha_creacion": {"$gte": fecha_inicio}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.nombre",
                "cantidad_total": {"$sum": "$items.cantidad"},
                "num_ventas":     {"$sum": 1},
            }},
            {"$sort": {"cantidad_total": -1}},
            {"$limit": 15},
        ]

        items = list(db.ventas.aggregate(pipeline))
        if not items:
            return []

        total_pedidos_hist = float(db.ventas.count_documents({"fecha_creacion": {"$gte": fecha_inicio}})) or 1
        pred_total = float(np.sum(y_fut))

        resultado = []
        for item in items:
            cant_hist  = float(item["cantidad_total"])
            cant_pred  = round(cant_hist / total_pedidos_hist * pred_total)
            resultado.append({
                "ingrediente":   str(item["_id"]),
                "unidades_pred": int(max(0, cant_pred)),
                "base_diaria":   round(cant_hist / 30, 1),
            })

        return resultado
