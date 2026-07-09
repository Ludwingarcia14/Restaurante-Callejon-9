"""
Logica de negocio de configuracion del restaurante (tenant).

build_config_update transforma los datos del formulario en un update seguro
para Mongo: solo campos permitidos, con notacion de punto (para no pisar
subdocumentos completos) y el IVA convertido de porcentaje a fraccion.
"""

# Mapea campo del formulario -> ruta en el documento del tenant
_FIELD_MAP = {
    "nombre": "nombre",
    "primario": "tema.primario",
    "acento": "tema.acento",
    "moneda": "fiscal.moneda",
    "direccion": "contacto.direccion",
    "telefono": "contacto.telefono",
    "horarios": "contacto.horarios",
}


def build_config_update(data):
    """Devuelve el dict (con notacion de punto) para $set, solo con campos validos."""
    update = {}
    for src, dest in _FIELD_MAP.items():
        valor = data.get(src)
        if valor not in (None, ""):
            update[dest] = str(valor).strip()

    # IVA: el formulario lo captura como porcentaje (16); se guarda como fraccion (0.16)
    iva = data.get("iva")
    if iva not in (None, ""):
        try:
            update["fiscal.iva"] = round(float(iva) / 100, 4)
        except (TypeError, ValueError):
            pass

    return update
