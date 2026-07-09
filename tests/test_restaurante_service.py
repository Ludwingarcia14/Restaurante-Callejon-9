"""
Tests de la construccion del update de configuracion del restaurante (tenant).

Logica pura: toma los datos del formulario, deja solo campos permitidos, los
anida con notacion de punto (para no pisar subdocumentos) y convierte el IVA de
porcentaje a fraccion.
"""
from services.restaurante.restaurante_service import build_config_update


def test_whitelists_and_nests_fields():
    upd = build_config_update({
        "nombre": "Mi Resto",
        "primario": "#F2913D",
        "acento": "#059669",
        "moneda": "MXN",
        "direccion": "Calle 1",
        "telefono": "555",
        "horarios": "9-18",
    })
    assert upd["nombre"] == "Mi Resto"
    assert upd["tema.primario"] == "#F2913D"
    assert upd["tema.acento"] == "#059669"
    assert upd["fiscal.moneda"] == "MXN"
    assert upd["contacto.direccion"] == "Calle 1"
    assert upd["contacto.telefono"] == "555"
    assert upd["contacto.horarios"] == "9-18"


def test_iva_percentage_to_fraction():
    assert build_config_update({"iva": "16"})["fiscal.iva"] == 0.16


def test_ignores_unknown_fields():
    assert build_config_update({"hacker": "x", "nombre": "A"}) == {"nombre": "A"}


def test_omits_missing_or_empty_fields():
    assert build_config_update({}) == {}
    assert build_config_update({"nombre": "", "primario": None}) == {}


def test_iva_invalido_se_omite():
    assert "fiscal.iva" not in build_config_update({"iva": "abc"})
