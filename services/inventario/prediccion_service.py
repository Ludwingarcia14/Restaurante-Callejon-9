"""
Predicción de inventario: pronóstico de consumo (regresión) y recomendación de
reorden (clasificación), con sus métricas de evaluación.

Las métricas (RMSE, matriz de confusión) se implementan a mano para dejar
explícita su definición y poder testearlas; scikit-learn se usa solo para
entrenar los modelos (ver funciones del pipeline).
"""
import math

_FEATURES = ["stock_actual", "stock_minimo", "costo_unitario", "n_movs"]


# ==========================================
# PREPARACIÓN DE DATOS
# ==========================================

def preparar_dataset(insumos, movimientos, dias_ventana=30, umbral_dias=7):
    """Construye una fila por insumo con features, consumo total y etiqueta de reorden.

    label_reorden = 1 si los días de cobertura (stock / consumo diario) < umbral_dias.
    """
    consumo = {}
    for mov in movimientos:
        if mov.get("tipo") != "salida":
            continue
        iid = mov.get("insumo_id")
        agg = consumo.setdefault(iid, {"total": 0.0, "n": 0})
        agg["total"] += float(mov.get("cantidad") or 0)
        agg["n"] += 1

    filas = []
    for ins in insumos:
        iid = ins.get("_id")
        agg = consumo.get(iid, {"total": 0.0, "n": 0})
        total = agg["total"]
        stock = float(ins.get("stock_actual") or 0)
        minimo = float(ins.get("stock_minimo") or 0)
        tasa = total / dias_ventana if dias_ventana else 0.0
        cobertura = stock / tasa if tasa > 0 else float("inf")
        filas.append({
            "insumo_id": iid,
            "nombre": ins.get("nombre", ""),
            "stock_actual": stock,
            "stock_minimo": minimo,
            "costo_unitario": float(ins.get("costo_unitario") or 0),
            "n_movs": agg["n"],
            "total_consumido": round(total, 2),
            "tasa_diaria": round(tasa, 3),
            "dias_cobertura": None if cobertura == float("inf") else round(cobertura, 1),
            # Punto de reorden: stock en o por debajo de 1.5x el mínimo (nivel bajo/crítico)
            "label_reorden": 1 if stock <= minimo * 1.5 else 0,
        })
    return filas


def entrenar_y_evaluar(dataset, test_size=0.3, random_state=42):
    """Entrena regresión (consumo) y clasificación (reorden) y devuelve métricas.

    Métricas calculadas sobre el conjunto de prueba (honesto). Las predicciones
    de la tabla se generan para todos los insumos (modelo entrenado en train).
    """
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression, LogisticRegression

    n = len(dataset)
    if n < 4:
        return {"ok": False, "motivo": "Datos insuficientes para entrenar (se requieren al menos 4 insumos)."}

    X = [[f[k] for k in _FEATURES] for f in dataset]
    y_consumo = [f["total_consumido"] for f in dataset]
    y_reorden = [f["label_reorden"] for f in dataset]
    idx = list(range(n))

    tr, te = train_test_split(idx, test_size=test_size, random_state=random_state)
    Xtr = [X[i] for i in tr]; Xte = [X[i] for i in te]

    # --- Regresión: consumo ---
    reg = LinearRegression().fit(Xtr, [y_consumo[i] for i in tr])
    pred_te = reg.predict(Xte)
    y_te = [y_consumo[i] for i in te]
    media_tr = sum(y_consumo[i] for i in tr) / len(tr)
    resultado = {
        "ok": True,
        "n_total": n, "n_train": len(tr), "n_test": len(te),
        "rmse": round(rmse(y_te, list(pred_te)), 2),
        "rmse_baseline": round(rmse(y_te, [media_tr] * len(te)), 2),
    }

    # --- Clasificación: reorden (requiere ambas clases en train) ---
    ytr_clf = [y_reorden[i] for i in tr]
    if len(set(ytr_clf)) == 2:
        clf = LogisticRegression(max_iter=1000).fit(Xtr, ytr_clf)
        pred_clf = [int(v) for v in clf.predict(Xte)]
        resultado["clasificacion"] = metricas_clasificacion([y_reorden[i] for i in te], pred_clf)
        pred_reorden_all = [int(v) for v in clf.predict(X)]
    else:
        resultado["clasificacion"] = None
        pred_reorden_all = y_reorden  # sin modelo, se muestra la etiqueta por regla

    # --- Predicciones para la tabla (todos los insumos) ---
    pred_consumo_all = [max(0.0, round(float(v), 2)) for v in reg.predict(X)]
    resultado["predicciones"] = [
        {
            "nombre": dataset[i]["nombre"],
            "consumo_real": dataset[i]["total_consumido"],
            "consumo_predicho": pred_consumo_all[i],
            "reorden": pred_reorden_all[i],
        }
        for i in range(n)
    ]
    return resultado


# ==========================================
# MÉTRICAS (puras, testeables)
# ==========================================

def rmse(y_true, y_pred):
    """Raíz del error cuadrático medio entre valores reales y predichos."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true y y_pred deben tener la misma longitud")
    if not y_true:
        raise ValueError("Se requiere al menos un valor")
    suma = sum((float(t) - float(p)) ** 2 for t, p in zip(y_true, y_pred))
    return math.sqrt(suma / len(y_true))


def matriz_confusion(y_true, y_pred):
    """Matriz de confusión binaria (1 = positivo). Devuelve tp/tn/fp/fn."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true y y_pred deben tener la misma longitud")
    m = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for real, pred in zip(y_true, y_pred):
        real, pred = int(real), int(pred)
        if real == 1 and pred == 1:
            m["tp"] += 1
        elif real == 0 and pred == 0:
            m["tn"] += 1
        elif real == 0 and pred == 1:
            m["fp"] += 1
        else:  # real == 1 and pred == 0
            m["fn"] += 1
    return m


def metricas_clasificacion(y_true, y_pred):
    """Matriz de confusión + accuracy/precision/recall/f1 (sin dividir por cero)."""
    m = matriz_confusion(y_true, y_pred)
    tp, tn, fp, fn = m["tp"], m["tn"], m["fp"], m["fn"]
    total = tp + tn + fp + fn

    def _safe(num, den):
        return num / den if den else 0

    precision = _safe(tp, tp + fp)
    recall = _safe(tp, tp + fn)
    return {
        "matriz": m,
        "total": total,
        "accuracy": _safe(tp + tn, total),
        "precision": precision,
        "recall": recall,
        "f1": _safe(2 * precision * recall, precision + recall),
    }
