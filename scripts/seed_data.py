"""
Seed de datos para Restaurante Callejón 9 — Fase CRISP-DM: Data Understanding
Genera 2000 ventas y comandas con distribuciones realistas para analytics y K-means.

Uso:
    python scripts/seed_data.py              # inserta 2000 registros
    python scripts/seed_data.py --limpiar    # elimina seeds anteriores y vuelve a insertar
    python scripts/seed_data.py --n 500      # inserta N registros
"""
import os
import sys
import random
from datetime import datetime, timedelta

import numpy as np
from bson import ObjectId

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import pymongo

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB_NAME", "callejon9")
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

# MESEROS y MENU se cargan desde la BD en seed() — no hardcodeados

METODOS_PAGO  = ["efectivo", "tarjeta", "transferencia", "mercadopago"]
METODOS_PESOS = [0.50, 0.30, 0.05, 0.15]

# ---------------------------------------------------------------------------
# Configuración de mesas — define los 3 clusters para K-means
#   VIP (1-2):        alta frecuencia + ticket alto   → cluster A
#   Regular (3-6):    frecuencia media + ticket medio → cluster B
#   Ocasional (7-12): baja frecuencia + ticket bajo   → cluster C
# ---------------------------------------------------------------------------
MESAS = {
    # VIP: ticket alto pero frecuencia moderada (vienen poco, gastan mucho)
    1: {"cluster": "vip",       "peso": 0.14, "ticket_mean": 400, "ticket_std": 65},
    2: {"cluster": "vip",       "peso": 0.10, "ticket_mean": 480, "ticket_std": 75},
    # Regular: ticket medio, MUY alta frecuencia (vienen seguido)
    3: {"cluster": "regular",   "peso": 0.20, "ticket_mean": 160, "ticket_std": 28},
    4: {"cluster": "regular",   "peso": 0.18, "ticket_mean": 150, "ticket_std": 25},
    5: {"cluster": "regular",   "peso": 0.16, "ticket_mean": 165, "ticket_std": 30},
    # Ocasional: ticket similar a Regular pero MUY baja frecuencia
    6: {"cluster": "ocasional", "peso": 0.09, "ticket_mean": 155, "ticket_std": 28},
    7: {"cluster": "ocasional", "peso": 0.07, "ticket_mean": 140, "ticket_std": 22},
    8: {"cluster": "ocasional", "peso": 0.06, "ticket_mean": 160, "ticket_std": 30},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fecha_aleatoria(dias_atras=180):
    """Fecha con distribución realista: pesos fin de semana y horas pico."""
    offset = random.randint(0, dias_atras)
    base   = datetime.utcnow() - timedelta(days=offset)

    # Hora: 45% almuerzo (12-14), 40% cena (19-21), 15% resto
    r = random.random()
    if r < 0.45:
        hora = random.randint(12, 14)
    elif r < 0.85:
        hora = random.randint(19, 21)
    else:
        hora = random.choice([11, 15, 16, 17, 18, 22])

    return base.replace(
        hour=hora,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )


def _generar_items(ticket_target, menu):
    """Construye lista de items usando el menú real de la BD."""
    items = []
    total = 0.0

    categorias_principales = {"principales", "tacos"}
    principales = [p for p in menu if p["categoria"] in categorias_principales]
    if not principales:
        principales = menu  # fallback si no hay categorías conocidas

    # Siempre al menos un plato principal
    principal  = random.choice(principales)
    cantidad   = random.randint(1, 3)
    subtotal_p = principal["precio"] * cantidad
    items.append({
        "producto_id":     str(principal["_id"]),
        "nombre":          principal["nombre"],
        "cantidad":        cantidad,
        "precio_unitario": float(principal["precio"]),
        "precio":          float(principal["precio"]),
        "subtotal":        float(subtotal_p),
    })
    total += subtotal_p

    # Agregar extras hasta cubrir el ticket objetivo
    for _ in range(6):
        if total >= ticket_target * 0.85:
            break
        item       = random.choice(menu)
        cantidad   = random.randint(1, 2)
        subtotal_i = item["precio"] * cantidad
        items.append({
            "producto_id":     str(item["_id"]),
            "nombre":          item["nombre"],
            "cantidad":        cantidad,
            "precio_unitario": float(item["precio"]),
            "precio":          float(item["precio"]),
            "subtotal":        float(subtotal_i),
        })
        total += subtotal_i

    return items, round(total, 2)


def _propina_pct(metodo):
    """Devuelve porcentaje de propina como entero (0, 10, 15 ó 20)."""
    if metodo in ("tarjeta", "mercadopago"):
        return random.choices([0, 10, 15, 20], weights=[0.15, 0.30, 0.35, 0.20])[0]
    if metodo == "efectivo":
        return random.choices([0, 10, 15],     weights=[0.40, 0.35, 0.25])[0]
    return random.choices([0, 10, 15, 20],     weights=[0.20, 0.30, 0.30, 0.20])[0]


# ---------------------------------------------------------------------------
# Generadores de documentos
# ---------------------------------------------------------------------------

def _venta(mesero, mesa_num, cfg, menu):
    ticket_target = max(60.0, float(np.random.normal(cfg["ticket_mean"], cfg["ticket_std"])))
    items, subtotal = _generar_items(ticket_target, menu)

    metodo      = random.choices(METODOS_PAGO, weights=METODOS_PESOS)[0]
    pct_propina = _propina_pct(metodo)
    impuesto    = round(subtotal * 0.16, 2)
    propina     = round(subtotal * pct_propina / 100, 2)
    total       = round(subtotal + impuesto, 2)        # sin propina, igual que en app real
    total_final = round(total + propina, 2)
    fecha       = _fecha_aleatoria()
    personas    = random.randint(1, 6)

    doc = {
        "mesa_id":            str(mesa_num),
        "mesa_nombre":        f"Mesa {mesa_num}",
        "mesa_numero":        mesa_num,
        "mesero_id":          str(mesero["_id"]),
        "mesero_nombre":      mesero["nombre"],
        "cliente_nombre":     f"Cliente {random.randint(100, 999)}",
        "items":              items,
        "platillos":          items,
        "subtotal":           subtotal,
        "impuesto":           impuesto,
        "descuento":          0.0,
        "propina":            propina,
        "porcentaje_propina": pct_propina,
        "total":              total,
        "total_final":        total_final,
        "metodo_pago":        metodo,
        "comensales":         personas,
        "num_personas":       personas,
        "estado":             "completada",
        "notas":              "",
        "fecha":              fecha,
        "fecha_creacion":     fecha,
        "fecha_actualizacion": fecha,
        "fecha_completada":   fecha,
        "_seeded":            True,
    }
    if metodo == "mercadopago":
        doc["payment_id"] = random.randint(100_000_000_000, 999_999_999_999)
    return doc


def _comanda(venta, mesero, mesa_num):
    duracion    = timedelta(minutes=random.randint(30, 90))
    fecha_cierre = venta["fecha"] + duracion
    doc = {
        "mesa_numero":        mesa_num,
        "num_comensales":     venta["comensales"],
        "mesero_id":          mesero["_id"],
        "mesero_nombre":      mesero["nombre"],
        "estado":             random.choice(["pagada", "cerrada"]),
        "items":              venta["items"],
        "total":              venta["total"],
        "propina":            venta["propina"],
        "porcentaje_propina": venta["porcentaje_propina"],
        "total_final":        venta["total_final"],
        "metodo_pago":        venta["metodo_pago"],
        "fecha_apertura":     venta["fecha"],
        "fecha_cierre":       fecha_cierre,
        "fecha_actualizacion": fecha_cierre,
        "folio":              f"COM-{venta['fecha'].strftime('%y%m%d%H%M%S')}",
        "_seeded":            True,
    }
    if venta["metodo_pago"] == "mercadopago":
        doc["payment_id"] = venta["payment_id"]
    return doc


# ---------------------------------------------------------------------------
# Definición de las 8 mesas reales del restaurante
# ---------------------------------------------------------------------------
MESAS_RESTAURANTE = [
    {"numero": 1, "capacidad": 4, "tipo": "interior", "seccion": "A"},
    {"numero": 2, "capacidad": 4, "tipo": "interior", "seccion": "A"},
    {"numero": 3, "capacidad": 4, "tipo": "interior", "seccion": "B"},
    {"numero": 4, "capacidad": 4, "tipo": "terraza",  "seccion": "C"},
    {"numero": 5, "capacidad": 8, "tipo": "terraza",  "seccion": "C"},
    {"numero": 6, "capacidad": 4, "tipo": "interior", "seccion": "A"},
    {"numero": 7, "capacidad": 2, "tipo": "interior", "seccion": "B"},
    {"numero": 8, "capacidad": 6, "tipo": "terraza",  "seccion": "C"},
]


def seed_mesas():
    """Asegura que existan exactamente 8 mesas en la colección 'mesas'."""
    col = db["mesas"]
    ahora = datetime.utcnow()

    insertadas = 0
    for m in MESAS_RESTAURANTE:
        existe = col.find_one({"numero": m["numero"]})
        if not existe:
            col.insert_one({
                "numero":     m["numero"],
                "capacidad":  m["capacidad"],
                "tipo":       m["tipo"],
                "seccion":    m["seccion"],
                "estado":     "disponible",
                "activa":     True,
                "created_at": ahora,
            })
            insertadas += 1

    total = col.count_documents({"activa": True})
    print(f"  Mesas: {insertadas} nuevas insertadas — {total} activas en total")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def seed(n=2000, limpiar=False):
    print("  Verificando mesas...")
    seed_mesas()

    # Cargar menú real desde la BD
    menu = list(db.platillos.find({"disponible": True}, {"_id": 1, "nombre": 1, "precio": 1, "categoria": 1}))
    if not menu:
        print("  ⚠️  No se encontraron platillos en la BD. Abortando.")
        return
    print(f"  Menú cargado: {len(menu)} platillos — {[p['nombre'] for p in menu]}")

    # Cargar meseros reales desde la BD (rol 2)
    meseros_bd = list(db.usuarios.find(
        {"usuario_rol": "2"},
        {"_id": 1, "usuario_nombre": 1, "nombre": 1}
    ))
    meseros = [
        {"_id": m["_id"], "nombre": m.get("usuario_nombre") or m.get("nombre", "Mesero")}
        for m in meseros_bd
    ]
    if not meseros:
        print("  ⚠️  No se encontraron meseros (rol 2) en la BD. Abortando.")
        return
    print(f"  Meseros cargados: {[m['nombre'] for m in meseros]}")

    if limpiar:
        r_v = db.ventas.delete_many({"_seeded": True})
        r_c = db.comandas.delete_many({"_seeded": True})
        print(f"  Eliminados: {r_v.deleted_count} ventas, {r_c.deleted_count} comandas.")

    mesas_ids    = list(MESAS.keys())
    mesas_pesos  = [MESAS[m]["peso"] for m in mesas_ids]

    ventas_docs   = []
    comandas_docs = []

    for _ in range(n):
        mesa_num = random.choices(mesas_ids, weights=mesas_pesos)[0]
        cfg      = MESAS[mesa_num]
        mesero   = random.choice(meseros)

        v = _venta(mesero, mesa_num, cfg, menu)
        c = _comanda(v, mesero, mesa_num)

        ventas_docs.append(v)
        comandas_docs.append(c)

    db.ventas.insert_many(ventas_docs)
    db.comandas.insert_many(comandas_docs)

    vip_n  = int(sum(MESAS[m]["peso"] for m in [1, 2]) * n)
    reg_n  = int(sum(MESAS[m]["peso"] for m in [3, 4, 5]) * n)
    ocas_n = int(sum(MESAS[m]["peso"] for m in [6, 7, 8]) * n)

    print(f"\n  {n} ventas  insertadas en '{MONGO_DB}.ventas'")
    print(f"  {n} comandas insertadas en '{MONGO_DB}.comandas'")
    print(f"\n  Distribución de clusters:")
    print(f"    VIP       (mesas 1-2):  ~{vip_n:>4} registros  | ticket ~360-400 MXN")
    print(f"    Regular   (mesas 3-5):  ~{reg_n:>4} registros  | ticket ~195-225 MXN")
    print(f"    Ocasional (mesas 6-8):  ~{ocas_n:>4} registros  | ticket  ~95-125 MXN")
    print(f"\n  Meseros usados:")
    for m in meseros:
        print(f"    - {m['nombre']}  ({m['_id']})")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed Restaurante Callejón 9")
    parser.add_argument("--n",       type=int, default=2000, help="Número de registros (default: 2000)")
    parser.add_argument("--limpiar", action="store_true",    help="Eliminar seeds previos antes de insertar")
    args = parser.parse_args()

    print(f"\nConectando a {MONGO_DB}...")
    seed(n=args.n, limpiar=args.limpiar)
    print("\nDone.\n")
