"""
Tests de la agregacion de ventas por dia para la grafica de tendencia.

Logica pura (sin Mongo): recibe una lista de ventas y arma la serie diaria
rellenando con ceros los dias sin ventas. Se pasa `hoy` como parametro para que
el test sea determinista.
"""
from datetime import datetime, timedelta

from services.dashboard.dashboard_service import (
    serie_ventas_por_dia,
    online_cutoff,
    UMBRAL_ONLINE_SEG,
)


def test_online_cutoff_resta_el_umbral():
    now = datetime(2026, 6, 28, 12, 0, 0)
    assert online_cutoff(now, 120) == datetime(2026, 6, 28, 11, 58, 0)


def test_online_cutoff_usa_umbral_por_defecto():
    now = datetime(2026, 6, 28, 12, 0, 0)
    assert online_cutoff(now) == now - timedelta(seconds=UMBRAL_ONLINE_SEG)


def test_serie_tiene_un_punto_por_dia_ordenado():
    hoy = datetime(2026, 6, 28, 15, 0, 0)
    serie = serie_ventas_por_dia([], dias=7, hoy=hoy)

    assert len(serie) == 7
    assert serie[0]["fecha"] == "2026-06-22"   # mas antiguo primero
    assert serie[-1]["fecha"] == "2026-06-28"  # hoy al final
    assert all(p["total"] == 0 for p in serie)


def test_suma_totales_del_mismo_dia():
    hoy = datetime(2026, 6, 28, 12, 0, 0)
    ventas = [
        {"fecha": datetime(2026, 6, 28, 9, 0), "total": 100},
        {"fecha": datetime(2026, 6, 28, 20, 0), "total": 50.5},
        {"fecha": datetime(2026, 6, 27, 10, 0), "total": 30},
    ]
    serie = serie_ventas_por_dia(ventas, dias=7, hoy=hoy)
    por_dia = {p["fecha"]: p["total"] for p in serie}

    assert por_dia["2026-06-28"] == 150.5
    assert por_dia["2026-06-27"] == 30


def test_ignora_ventas_fuera_del_rango():
    hoy = datetime(2026, 6, 28, 12, 0)
    ventas = [{"fecha": datetime(2026, 6, 1, 10, 0), "total": 999}]  # fuera de 7 dias
    serie = serie_ventas_por_dia(ventas, dias=7, hoy=hoy)

    assert sum(p["total"] for p in serie) == 0


def test_tolera_total_faltante_o_none():
    hoy = datetime(2026, 6, 28, 12, 0)
    ventas = [
        {"fecha": datetime(2026, 6, 28, 10, 0)},
        {"fecha": datetime(2026, 6, 28, 11, 0), "total": None},
    ]
    serie = serie_ventas_por_dia(ventas, dias=7, hoy=hoy)
    por_dia = {p["fecha"]: p["total"] for p in serie}

    assert por_dia["2026-06-28"] == 0
