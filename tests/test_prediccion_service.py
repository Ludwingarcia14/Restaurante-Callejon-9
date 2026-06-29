"""
Tests de las métricas de evaluación del modelo de inventario.

Se implementan a mano (no solo sklearn) para demostrar comprensión y poder
testearlas: RMSE (regresión) y matriz de confusión + métricas (clasificación).
"""
import math
import pytest

from services.inventario.prediccion_service import (
    rmse,
    matriz_confusion,
    metricas_clasificacion,
    preparar_dataset,
)


def test_preparar_dataset_agrega_consumo_y_etiqueta_reorden():
    insumos = [
        {"_id": "a", "nombre": "Tomate", "stock_actual": 4, "stock_minimo": 10, "costo_unitario": 2},
        {"_id": "b", "nombre": "Sal", "stock_actual": 100, "stock_minimo": 5, "costo_unitario": 1},
    ]
    movimientos = [
        {"insumo_id": "a", "tipo": "salida", "cantidad": 10},
        {"insumo_id": "a", "tipo": "salida", "cantidad": 20},
        {"insumo_id": "a", "tipo": "entrada", "cantidad": 99},  # se ignora (no es salida)
    ]
    filas = preparar_dataset(insumos, movimientos, dias_ventana=30, umbral_dias=7)
    por_id = {f["insumo_id"]: f for f in filas}

    # Tomate: consumió 30 en 30 días → tasa 1/día; stock 4 → cobertura 4 días < 7 → reorden
    assert por_id["a"]["total_consumido"] == 30
    assert por_id["a"]["n_movs"] == 2
    assert por_id["a"]["tasa_diaria"] == 1.0
    assert por_id["a"]["label_reorden"] == 1

    # Sal: sin salidas → no se reordena
    assert por_id["b"]["total_consumido"] == 0
    assert por_id["b"]["label_reorden"] == 0


# ---- RMSE ----

def test_rmse_cero_si_iguales():
    assert rmse([3, 5, 2], [3, 5, 2]) == 0


def test_rmse_calculo():
    assert rmse([2, 4], [4, 6]) == 2.0
    assert math.isclose(rmse([0, 0], [3, 4]), math.sqrt(12.5))


def test_rmse_longitudes_distintas_falla():
    with pytest.raises(ValueError):
        rmse([1, 2], [1])


def test_rmse_vacio_falla():
    with pytest.raises(ValueError):
        rmse([], [])


# ---- Matriz de confusión ----

def test_matriz_confusion_cuenta_bien():
    m = matriz_confusion([1, 0, 1, 0], [1, 0, 0, 1])
    assert m == {"tp": 1, "tn": 1, "fp": 1, "fn": 1}


def test_matriz_confusion_todo_correcto():
    m = matriz_confusion([1, 1, 0], [1, 1, 0])
    assert m == {"tp": 2, "tn": 1, "fp": 0, "fn": 0}


# ---- Métricas derivadas ----

def test_metricas_clasificacion():
    r = metricas_clasificacion([1, 0, 1, 0], [1, 0, 0, 1])
    assert r["total"] == 4
    assert r["accuracy"] == 0.5      # (tp+tn)/total = 2/4
    assert r["precision"] == 0.5     # tp/(tp+fp) = 1/2
    assert r["recall"] == 0.5        # tp/(tp+fn) = 1/2


def test_metricas_sin_positivos_no_divide_por_cero():
    r = metricas_clasificacion([0, 0], [0, 0])
    assert r["precision"] == 0
    assert r["recall"] == 0
    assert r["accuracy"] == 1.0
