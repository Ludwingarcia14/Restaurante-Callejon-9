"""
Tests de la logica de negocio de inventario (capa de servicio).

Son funciones puras (sin Mongo): reglas de negocio extraidas del controller
para cumplir SRP/SoC. Aqui se fija el comportamiento esperado.
"""
import pytest

from services.inventario.inventario_service import (
    calcular_estado_stock,
    calcular_valor_inventario,
    calcular_nuevo_stock,
)


# ---- calcular_estado_stock ----

def test_estado_agotado_cuando_stock_es_cero():
    assert calcular_estado_stock(stock_actual=0, stock_minimo=10) == "agotado"


def test_estado_critico_cuando_stock_igual_o_menor_al_minimo():
    assert calcular_estado_stock(stock_actual=10, stock_minimo=10) == "critico"
    assert calcular_estado_stock(stock_actual=5, stock_minimo=10) == "critico"


def test_estado_bajo_cuando_stock_hasta_1_5_veces_el_minimo():
    assert calcular_estado_stock(stock_actual=15, stock_minimo=10) == "bajo"


def test_estado_normal_cuando_stock_supera_1_5_veces_el_minimo():
    assert calcular_estado_stock(stock_actual=16, stock_minimo=10) == "normal"


# ---- calcular_valor_inventario ----

def test_valor_inventario_suma_stock_por_costo():
    insumos = [
        {"stock_actual": 10, "costo_unitario": 2},   # 20
        {"stock_actual": 5, "costo_unitario": 3.5},  # 17.5
    ]
    assert calcular_valor_inventario(insumos) == 37.5


def test_valor_inventario_tolera_campos_faltantes():
    insumos = [{"stock_actual": 4}, {"costo_unitario": 9}, {}]
    assert calcular_valor_inventario(insumos) == 0


def test_valor_inventario_lista_vacia_es_cero():
    assert calcular_valor_inventario([]) == 0


def test_valor_inventario_tolera_valores_numericos_como_texto():
    # El frontend a veces envia numeros como string en el JSON.
    insumos = [{"stock_actual": "10", "costo_unitario": "2.5"}]
    assert calcular_valor_inventario(insumos) == 25.0


# ---- calcular_nuevo_stock ----

def test_entrada_suma_al_stock():
    assert calcular_nuevo_stock(stock_actual=10, cantidad=5, tipo="entrada") == 15


def test_entrada_usa_valor_absoluto():
    # Una entrada nunca resta, aunque venga cantidad negativa.
    assert calcular_nuevo_stock(stock_actual=10, cantidad=-5, tipo="entrada") == 15


def test_salida_resta_del_stock():
    assert calcular_nuevo_stock(stock_actual=10, cantidad=4, tipo="salida") == 6


def test_merma_resta_del_stock():
    assert calcular_nuevo_stock(stock_actual=10, cantidad=3, tipo="merma") == 7


def test_ajuste_permite_cantidad_negativa():
    assert calcular_nuevo_stock(stock_actual=10, cantidad=-4, tipo="ajuste") == 6
    assert calcular_nuevo_stock(stock_actual=10, cantidad=3, tipo="ajuste") == 13


def test_salida_que_deja_stock_negativo_falla():
    with pytest.raises(ValueError, match="insuficiente"):
        calcular_nuevo_stock(stock_actual=10, cantidad=15, tipo="salida")


def test_tipo_invalido_falla():
    with pytest.raises(ValueError, match="invalido|inválido|Tipo"):
        calcular_nuevo_stock(stock_actual=10, cantidad=1, tipo="cualquiera")


def test_tolera_valores_como_texto():
    assert calcular_nuevo_stock(stock_actual="10", cantidad="2", tipo="salida") == 8


def test_acepta_tipo_como_str_enum():
    # El modelo pasa un miembro de TipoMovimiento (str, Enum). str(miembro) da
    # "Clase.MIEMBRO", no su valor, asi que no debe usarse str() para comparar.
    from enum import Enum

    class _Tipo(str, Enum):
        ENTRADA = "entrada"
        SALIDA = "salida"

    assert calcular_nuevo_stock(10, 5, _Tipo.ENTRADA) == 15
    assert calcular_nuevo_stock(10, 4, _Tipo.SALIDA) == 6
