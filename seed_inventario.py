"""
Seed de Inventario - Restaurante Callejón 9
Vacía insumos y movimientos_inventario, luego inserta datos de prueba realistas.
Ejecutar: python seed_inventario.py
"""
from config.db import db
from datetime import datetime, timedelta
import random

insumos_col     = db["insumos"]
movimientos_col = db["movimientos_inventario"]

# ─── 0. LIMPIAR COLECCIONES ─────────────────────────────────────────────────
insumos_col.delete_many({})
movimientos_col.delete_many({})
print("🗑️  Colecciones vaciadas: insumos, movimientos_inventario")

# ─── 1. INSUMOS ──────────────────────────────────────────────────────────────
nuevos_insumos = [
    # carnes
    {"nombre": "Carne de Res",         "categoria": "carnes",      "unidad_medida": "kg",      "stock_actual": 18,  "stock_minimo": 10, "costo_unitario": 180},
    {"nombre": "Pollo Entero",         "categoria": "carnes",      "unidad_medida": "kg",      "stock_actual": 25,  "stock_minimo": 12, "costo_unitario": 85},
    {"nombre": "Chorizo",              "categoria": "carnes",      "unidad_medida": "kg",      "stock_actual": 4,   "stock_minimo": 6,  "costo_unitario": 120},
    {"nombre": "Costilla de Cerdo",    "categoria": "carnes",      "unidad_medida": "kg",      "stock_actual": 10,  "stock_minimo": 5,  "costo_unitario": 155},
    # verduras
    {"nombre": "Cebolla Blanca",       "categoria": "verduras",    "unidad_medida": "kg",      "stock_actual": 10,  "stock_minimo": 5,  "costo_unitario": 15},
    {"nombre": "Jitomate",             "categoria": "verduras",    "unidad_medida": "kg",      "stock_actual": 8,   "stock_minimo": 6,  "costo_unitario": 20},
    {"nombre": "Chile Serrano",        "categoria": "verduras",    "unidad_medida": "kg",      "stock_actual": 2,   "stock_minimo": 3,  "costo_unitario": 35},
    {"nombre": "Aguacate",             "categoria": "verduras",    "unidad_medida": "kg",      "stock_actual": 5,   "stock_minimo": 4,  "costo_unitario": 55},
    {"nombre": "Cilantro",             "categoria": "verduras",    "unidad_medida": "kg",      "stock_actual": 1.5, "stock_minimo": 1,  "costo_unitario": 30},
    # lacteos
    {"nombre": "Queso Fresco",         "categoria": "lacteos",     "unidad_medida": "kg",      "stock_actual": 6,   "stock_minimo": 4,  "costo_unitario": 95},
    {"nombre": "Crema",                "categoria": "lacteos",     "unidad_medida": "lt",      "stock_actual": 9,   "stock_minimo": 5,  "costo_unitario": 42},
    {"nombre": "Leche Entera",         "categoria": "lacteos",     "unidad_medida": "lt",      "stock_actual": 12,  "stock_minimo": 6,  "costo_unitario": 22},
    # granos
    {"nombre": "Arroz",                "categoria": "granos",      "unidad_medida": "kg",      "stock_actual": 30,  "stock_minimo": 10, "costo_unitario": 22},
    {"nombre": "Frijol Negro",         "categoria": "granos",      "unidad_medida": "kg",      "stock_actual": 20,  "stock_minimo": 8,  "costo_unitario": 28},
    {"nombre": "Maiz Pozolero",        "categoria": "granos",      "unidad_medida": "kg",      "stock_actual": 3,   "stock_minimo": 5,  "costo_unitario": 18},
    # bebidas
    {"nombre": "Agua Purificada",      "categoria": "bebidas",     "unidad_medida": "lt",      "stock_actual": 60,  "stock_minimo": 20, "costo_unitario": 5},
    {"nombre": "Refresco Lata",        "categoria": "bebidas",     "unidad_medida": "pza",     "stock_actual": 48,  "stock_minimo": 24, "costo_unitario": 14},
    {"nombre": "Cerveza Carta Blanca", "categoria": "bebidas",     "unidad_medida": "pza",     "stock_actual": 12,  "stock_minimo": 24, "costo_unitario": 18},
    # condimentos
    {"nombre": "Pimienta Negra",       "categoria": "condimentos", "unidad_medida": "kg",      "stock_actual": 1.5, "stock_minimo": 1,  "costo_unitario": 180},
    {"nombre": "Comino",               "categoria": "condimentos", "unidad_medida": "kg",      "stock_actual": 0.8, "stock_minimo": 1,  "costo_unitario": 220},
    {"nombre": "Aceite Vegetal",       "categoria": "condimentos", "unidad_medida": "lt",      "stock_actual": 8,   "stock_minimo": 4,  "costo_unitario": 35},
    # desechables
    {"nombre": "Servilletas",          "categoria": "desechables", "unidad_medida": "paquete", "stock_actual": 15,  "stock_minimo": 5,  "costo_unitario": 35},
    {"nombre": "Vasos Desechables",    "categoria": "desechables", "unidad_medida": "paquete", "stock_actual": 8,   "stock_minimo": 4,  "costo_unitario": 48},
    # limpieza
    {"nombre": "Cloro",                "categoria": "limpieza",    "unidad_medida": "lt",      "stock_actual": 3,   "stock_minimo": 2,  "costo_unitario": 25},
    {"nombre": "Jabón Líquido",        "categoria": "limpieza",    "unidad_medida": "lt",      "stock_actual": 5,   "stock_minimo": 2,  "costo_unitario": 40},
]

ahora = datetime.utcnow()
docs_insumos = [
    {**i, "activo": True, "created_at": ahora, "updated_at": ahora}
    for i in nuevos_insumos
]
res = insumos_col.insert_many(docs_insumos)

# Mapa nombre -> (ObjectId, costo_unitario, categoria, unidad)
ids_mapa = {}
for doc, oid in zip(docs_insumos, res.inserted_ids):
    ids_mapa[doc["nombre"]] = {
        "id":       oid,
        "costo":    doc["costo_unitario"],
        "categoria":doc["categoria"],
        "unidad":   doc["unidad_medida"],
    }

print(f"✅ Insumos insertados: {len(docs_insumos)}")

# ─── 2. MOVIMIENTOS (últimos 30 días) ────────────────────────────────────────
# (nombre, tipo, cant_min, cant_max)
plantilla = [
    ("Carne de Res",         "entrada", 5,   15),
    ("Carne de Res",         "salida",  2,   8),
    ("Carne de Res",         "merma",   0.3, 1.5),
    ("Pollo Entero",         "entrada", 8,   20),
    ("Pollo Entero",         "salida",  3,   10),
    ("Chorizo",              "salida",  1,   4),
    ("Chorizo",              "merma",   0.5, 1.5),
    ("Costilla de Cerdo",    "entrada", 4,   10),
    ("Costilla de Cerdo",    "salida",  2,   6),
    ("Cebolla Blanca",       "entrada", 5,   12),
    ("Cebolla Blanca",       "salida",  2,   6),
    ("Jitomate",             "entrada", 4,   10),
    ("Jitomate",             "salida",  2,   5),
    ("Jitomate",             "merma",   0.5, 2),
    ("Chile Serrano",        "salida",  0.5, 2),
    ("Aguacate",             "entrada", 5,   10),
    ("Aguacate",             "salida",  2,   5),
    ("Aguacate",             "merma",   0.5, 2),
    ("Cilantro",             "entrada", 1,   3),
    ("Cilantro",             "salida",  0.3, 1),
    ("Cilantro",             "merma",   0.2, 0.8),
    ("Queso Fresco",         "entrada", 3,   8),
    ("Queso Fresco",         "salida",  1,   3),
    ("Crema",                "salida",  1,   3),
    ("Leche Entera",         "entrada", 5,   15),
    ("Leche Entera",         "salida",  2,   6),
    ("Leche Entera",         "merma",   0.5, 1.5),
    ("Arroz",                "entrada", 10,  25),
    ("Arroz",                "salida",  3,   8),
    ("Frijol Negro",         "entrada", 8,   15),
    ("Frijol Negro",         "salida",  2,   6),
    ("Maiz Pozolero",        "salida",  1,   3),
    ("Maiz Pozolero",        "merma",   0.3, 1),
    ("Agua Purificada",      "entrada", 20,  40),
    ("Agua Purificada",      "salida",  5,   15),
    ("Refresco Lata",        "entrada", 24,  48),
    ("Refresco Lata",        "salida",  6,   18),
    ("Cerveza Carta Blanca", "salida",  6,   12),
    ("Aceite Vegetal",       "entrada", 2,   6),
    ("Aceite Vegetal",       "salida",  0.5, 2),
    ("Pimienta Negra",       "salida",  0.1, 0.4),
    ("Comino",               "salida",  0.1, 0.3),
    ("Servilletas",          "entrada", 5,   10),
    ("Servilletas",          "salida",  1,   3),
    ("Vasos Desechables",    "entrada", 4,   8),
    ("Vasos Desechables",    "salida",  1,   3),
    ("Cloro",                "entrada", 2,   4),
    ("Jabón Líquido",        "entrada", 2,   4),
    # ajustes de inventario (correcciones de conteo)
    ("Carne de Res",         "ajuste",  1,   3),
    ("Arroz",                "ajuste",  2,   5),
    ("Frijol Negro",         "ajuste",  1,   3),
    ("Aguacate",             "ajuste",  0.5, 2),
    ("Queso Fresco",         "ajuste",  0.5, 2),
]

movimientos = []

for dias_atras in range(30, 0, -1):
    fecha_dia = ahora - timedelta(days=dias_atras)
    seleccionados = random.sample(plantilla, min(random.randint(6, 12), len(plantilla)))

    for nombre, tipo, cmin, cmax in seleccionados:
        if nombre not in ids_mapa:
            continue
        info     = ids_mapa[nombre]
        cantidad = round(random.uniform(cmin, cmax), 2)
        costo_u  = info["costo"]
        hora     = timedelta(hours=random.randint(7, 21), minutes=random.randint(0, 59))

        movimientos.append({
            "tipo":          tipo,
            "insumo_id":     info["id"],
            "insumo_nombre": nombre,
            "categoria":     info["categoria"],
            "cantidad":      cantidad,
            "unidad_medida": info["unidad"],
            "stock_anterior": round(random.uniform(5, 30), 2),
            "stock_nuevo":    round(random.uniform(5, 30), 2),
            "costo_unitario": costo_u,
            "costo_total":    round(cantidad * costo_u, 2),
            "usuario_id":    None,
            "motivo":        "Semilla de datos",
            "fecha":         fecha_dia.replace(hour=0, minute=0, second=0) + hora,
        })

movimientos_col.insert_many(movimientos)
print(f"✅ Movimientos insertados: {len(movimientos)}")
print("\n🎉 Listo. Recarga la página de Reportes de Inventario.")
