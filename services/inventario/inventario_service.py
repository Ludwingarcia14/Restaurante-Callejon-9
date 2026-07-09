"""
Logica de negocio de inventario.

Centraliza las reglas que antes vivian en el controller (estado de stock) y la
valoracion del inventario que estaba duplicada en el dashboard y en reportes.
Son funciones puras: no acceden a la base de datos, solo aplican reglas.
"""

# Estados de stock posibles para un insumo
ESTADO_AGOTADO = "agotado"
ESTADO_CRITICO = "critico"
ESTADO_BAJO = "bajo"
ESTADO_NORMAL = "normal"

# Factor sobre el stock minimo a partir del cual el stock se considera "bajo"
_FACTOR_STOCK_BAJO = 1.5

# Tipos de movimiento (por valor; coinciden con el enum TipoMovimiento del modelo).
# Se comparan como texto para no acoplar el servicio al modelo (evita import circular).
_TIPO_ENTRADA = "entrada"
_TIPO_SALIDA = "salida"
_TIPO_AJUSTE = "ajuste"
_TIPO_MERMA = "merma"


def calcular_estado_stock(stock_actual, stock_minimo):
    """Determina el estado de un insumo a partir de su stock y su minimo."""
    if stock_actual == 0:
        return ESTADO_AGOTADO
    if stock_actual <= stock_minimo:
        return ESTADO_CRITICO
    if stock_actual <= stock_minimo * _FACTOR_STOCK_BAJO:
        return ESTADO_BAJO
    return ESTADO_NORMAL


def calcular_nuevo_stock(stock_actual, cantidad, tipo):
    """Calcula el stock resultante de aplicar un movimiento.

    - entrada: suma el valor absoluto (una entrada nunca resta).
    - ajuste: suma la cantidad tal cual (puede ser negativa para correcciones).
    - salida / merma: resta el valor absoluto.

    Lanza ValueError si el tipo es invalido o si el resultado seria negativo.
    """
    stock_actual = float(stock_actual)
    cantidad = float(cantidad)
    # No usar str(tipo): un miembro de un str-Enum ya es igual a su valor,
    # pero str(miembro) devolveria "Clase.MIEMBRO" y romperia la comparacion.

    if tipo == _TIPO_ENTRADA:
        nuevo_stock = stock_actual + abs(cantidad)
    elif tipo == _TIPO_AJUSTE:
        nuevo_stock = stock_actual + cantidad
    elif tipo in (_TIPO_SALIDA, _TIPO_MERMA):
        nuevo_stock = stock_actual - abs(cantidad)
    else:
        raise ValueError("Tipo de movimiento invalido")

    if nuevo_stock < 0:
        raise ValueError("Stock insuficiente")

    return nuevo_stock


def calcular_valor_inventario(insumos):
    """Suma el valor (stock_actual * costo_unitario) de una lista de insumos.

    Tolera valores numericos enviados como texto (p. ej. desde el frontend).
    """
    return sum(
        float(insumo.get("stock_actual", 0)) * float(insumo.get("costo_unitario", 0))
        for insumo in insumos
    )
