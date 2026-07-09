"""
Logica de negocio del dashboard de administracion.

Funciones puras (sin Mongo): transforman datos ya consultados en estructuras
listas para graficar. Se reciben los parametros de tiempo (`hoy`) para que el
calculo sea determinista y testeable.
"""
from datetime import timedelta

# Un usuario se considera "en linea" si su ultimo latido (last_seen) ocurrio
# dentro de esta ventana. El cliente late cada ~45s, asi tolera 1-2 fallos.
UMBRAL_ONLINE_SEG = 120


def online_cutoff(now, umbral_seg=UMBRAL_ONLINE_SEG):
    """Devuelve el instante a partir del cual un last_seen cuenta como online."""
    return now - timedelta(seconds=umbral_seg)


def serie_ventas_por_dia(ventas, dias, hoy):
    """Arma la serie diaria de ventas de los ultimos `dias` dias hasta `hoy`.

    Devuelve una lista ordenada (mas antiguo primero) de
    {"fecha": "YYYY-MM-DD", "total": float}, rellenando con 0 los dias sin venta.
    Las ventas fuera del rango se ignoran.
    """
    inicio = (hoy - timedelta(days=dias - 1)).date()
    dias_keys = [inicio + timedelta(days=i) for i in range(dias)]
    totales = {dia: 0.0 for dia in dias_keys}

    for venta in ventas:
        fecha = venta.get("fecha")
        if not fecha:
            continue
        dia = fecha.date()
        if dia in totales:
            totales[dia] += float(venta.get("total") or 0)

    return [
        {"fecha": dia.isoformat(), "total": round(totales[dia], 2)}
        for dia in dias_keys
    ]
