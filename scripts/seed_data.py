"""
Seed de datos para Restaurante Callejón 9 — Fase CRISP-DM: Data Understanding
Genera ventas y comandas con distribuciones NO lineales para analytics y K-means.

Patrones incluidos:
  - Variación fuerte por día de semana (viernes/sábado ×2.5)
  - Estacionalidad mensual (Dic-Ene alto, Aug bajo)
  - Popularidad Pareto de platillos (20% de items = 80% de pedidos)
  - Eventos especiales (picos aleatorios ~1 por mes)
  - Solapamiento de clusters con ruido
  - Tendencia de crecimiento suave hacia fechas recientes
  - Asociaciones entre platillos (combos frecuentes)
  - Distribución de horas diferente en fin de semana vs semana

Uso:
    python scripts/seed_data.py              # inserta 2000 registros
    python scripts/seed_data.py --limpiar    # elimina seeds anteriores y re-inserta
    python scripts/seed_data.py --n 3000     # inserta N registros
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

METODOS_PAGO  = ["efectivo", "tarjeta", "transferencia", "mercadopago"]
METODOS_PESOS = [0.48, 0.32, 0.05, 0.15]

# ---------------------------------------------------------------------------
# Configuración de mesas — clusters con solapamiento intencional
# ---------------------------------------------------------------------------
MESAS = {
    1: {"cluster": "vip",       "peso": 0.14, "ticket_mean": 420, "ticket_std": 110},
    2: {"cluster": "vip",       "peso": 0.10, "ticket_mean": 500, "ticket_std": 130},
    3: {"cluster": "regular",   "peso": 0.20, "ticket_mean": 170, "ticket_std": 45},
    4: {"cluster": "regular",   "peso": 0.18, "ticket_mean": 155, "ticket_std": 40},
    5: {"cluster": "regular",   "peso": 0.16, "ticket_mean": 175, "ticket_std": 50},
    6: {"cluster": "ocasional", "peso": 0.09, "ticket_mean": 130, "ticket_std": 38},
    7: {"cluster": "ocasional", "peso": 0.07, "ticket_mean": 115, "ticket_std": 30},
    8: {"cluster": "ocasional", "peso": 0.06, "ticket_mean": 145, "ticket_std": 42},
}

# Multiplicador por día de semana (0=lunes … 6=domingo)
DIA_SEMANA_MULT = [0.55, 0.60, 0.70, 0.85, 1.40, 2.20, 1.80]

# Multiplicador por mes (1-12) — Dic-Ene temporada alta, Aug baja
MES_MULT = {
    1: 1.35, 2: 1.15, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.10,
    7: 0.90, 8: 0.75, 9: 0.85, 10: 1.00, 11: 1.10, 12: 1.40,
}

# ---------------------------------------------------------------------------
# Helpers de tiempo
# ---------------------------------------------------------------------------

def _fecha_aleatoria(dias_atras=180, eventos_especiales=None):
    """
    Fecha con variación real:
    - Fin de semana mucho más probable
    - Estacionalidad mensual
    - Tendencia de crecimiento suave (fechas recientes más probables)
    - Horas de fin de semana incluyen noche tardía
    """
    # Tendencia: más registros en los últimos 90 días
    offset = int(np.random.exponential(scale=60))
    offset = min(offset, dias_atras)
    base   = datetime.utcnow() - timedelta(days=offset)

    dia_mult = DIA_SEMANA_MULT[base.weekday()]
    mes_mult = MES_MULT[base.month]

    # Si hay evento especial en ese día, mult extra
    evento_mult = 1.0
    if eventos_especiales:
        dia_base = base.date()
        for ev in eventos_especiales:
            if ev == dia_base:
                evento_mult = random.uniform(1.8, 3.0)
                break

    _ = dia_mult * mes_mult * evento_mult  # usado por el llamador para peso

    es_finde = base.weekday() >= 4  # viernes, sábado, domingo

    if es_finde:
        # Fin de semana: almuerzo largo, cena tardía, algo de noche
        r = random.random()
        if r < 0.30:
            hora = random.randint(12, 15)
        elif r < 0.65:
            hora = random.randint(19, 22)
        elif r < 0.82:
            hora = random.randint(23, 23)
        else:
            hora = random.choice([11, 16, 17, 18])
    else:
        # Semana: almuerzo concentrado (rápido) y cena temprana
        r = random.random()
        if r < 0.50:
            hora = random.randint(13, 14)
        elif r < 0.85:
            hora = random.randint(19, 21)
        else:
            hora = random.choice([12, 15, 18])

    return base.replace(
        hour=hora,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )


def _peso_dia(fecha, eventos_especiales):
    """Calcula el peso de un día para aceptar/rechazar el registro (rejection sampling)."""
    dm = DIA_SEMANA_MULT[fecha.weekday()]
    mm = MES_MULT[fecha.month]
    ev = 1.0
    if eventos_especiales and fecha.date() in {e for e in eventos_especiales}:
        ev = 2.5
    # Tendencia: más peso para fechas recientes (últimos 30 días = base 1.3)
    dias = (datetime.utcnow() - fecha).days
    trend = max(0.7, 1.3 - dias / 300)
    return dm * mm * ev * trend


def _generar_eventos(dias_atras=180):
    """Genera ~1 evento especial por mes en días aleatorios."""
    eventos = set()
    inicio  = datetime.utcnow() - timedelta(days=dias_atras)
    for i in range(dias_atras // 28):
        dia = inicio + timedelta(days=random.randint(i * 28, (i + 1) * 28))
        # Preferir viernes o sábados para los eventos
        for _ in range(7):
            if dia.weekday() in (4, 5):
                break
            dia += timedelta(days=1)
        eventos.add(dia.date())
    return list(eventos)


# ---------------------------------------------------------------------------
# Generación de items con popularidad Pareto
# ---------------------------------------------------------------------------

def _construir_popularidad(menu):
    """
    Asigna pesos de popularidad Pareto: el 20% de los platillos
    genera el 80% de los pedidos. También define combos frecuentes.
    """
    n = len(menu)
    # Ordenar por precio desc → los platillos más caros no son necesariamente los más populares
    mezclado = list(menu)
    random.shuffle(mezclado)
    # Pesos power-law: platillo_i recibe peso proporcional a 1/rank^0.7
    pesos = np.array([1.0 / (i + 1) ** 0.7 for i in range(n)])
    pesos = pesos / pesos.sum()
    return mezclado, pesos.tolist()


def _generar_items(ticket_target, menu, popularidad, pesos_pop):
    """
    Items con popularidad Pareto + asociaciones implícitas.
    Algunos platillos "arrastran" a otros (combos naturales).
    """
    items_acum = {}
    total = 0.0

    categorias_principales = {"principales", "tacos", "carnes", "platillos"}
    principales  = [p for p in popularidad if p.get("categoria", "") in categorias_principales]
    if not principales:
        principales = popularidad[:max(1, len(popularidad) // 2)]

    p_pop_principales = [pesos_pop[popularidad.index(p)] for p in principales]
    suma = sum(p_pop_principales)
    p_pop_principales = [w / suma for w in p_pop_principales]

    # Siempre un plato principal
    principal  = random.choices(principales, weights=p_pop_principales)[0]
    cantidad   = random.randint(1, 3)
    key = str(principal["_id"])
    items_acum[key] = {
        "producto_id":     key,
        "nombre":          principal["nombre"],
        "cantidad":        cantidad,
        "precio_unitario": float(principal["precio"]),
        "precio":          float(principal["precio"]),
        "subtotal":        float(principal["precio"] * cantidad),
    }
    total += principal["precio"] * cantidad

    # Extras con probabilidad de combo (asociación): items similares más probables
    iteraciones = 0
    while total < ticket_target * 0.80 and iteraciones < 8:
        iteraciones += 1
        # 40% de chance de elegir un "complemento" de precio bajo
        if random.random() < 0.40:
            complementos = [p for p in popularidad if float(p["precio"]) < ticket_target * 0.20]
            pool  = complementos if complementos else popularidad
            ppop  = [pesos_pop[popularidad.index(p)] for p in pool]
            s = sum(ppop); ppop = [w/s for w in ppop]
        else:
            pool  = popularidad
            ppop  = pesos_pop
        item  = random.choices(pool, weights=ppop)[0]
        cant  = random.randint(1, 2)
        k2    = str(item["_id"])
        sub   = float(item["precio"]) * cant
        if k2 in items_acum:
            items_acum[k2]["cantidad"] += cant
            items_acum[k2]["subtotal"] += sub
        else:
            items_acum[k2] = {
                "producto_id":     k2,
                "nombre":          item["nombre"],
                "cantidad":        cant,
                "precio_unitario": float(item["precio"]),
                "precio":          float(item["precio"]),
                "subtotal":        sub,
            }
        total += sub

    return list(items_acum.values()), round(total, 2)


def _propina_pct(metodo, es_finde):
    """Propinas más altas en fin de semana."""
    base_pesos = {
        "tarjeta":     [0.10, 0.28, 0.37, 0.25],
        "mercadopago": [0.15, 0.30, 0.35, 0.20],
        "efectivo":    [0.38, 0.37, 0.25, 0.00],
        "transferencia":[0.20, 0.30, 0.30, 0.20],
    }
    opciones = [0, 10, 15, 20]
    pesos    = base_pesos.get(metodo, [0.20, 0.30, 0.30, 0.20])
    if es_finde:
        # En fin de semana la propina sube
        pesos = [max(0, p - 0.08) if opciones[i] == 0 else p + 0.02
                 for i, p in enumerate(pesos)]
        s = sum(pesos); pesos = [p/s for p in pesos]
    return random.choices(opciones, weights=pesos)[0]


# ---------------------------------------------------------------------------
# Ruido en clusters: ocasionalmente una mesa "regular" gasta como VIP
# ---------------------------------------------------------------------------

def _ticket_con_ruido(cfg, fecha):
    """
    Ticket con distribución no gaussiana:
    - 5% de chance de ser un outlier alto (evento, celebración)
    - 3% de chance de ser un outlier bajo (comida express)
    - El resto: distribución log-normal para evitar colas perfectamente simétricas
    """
    r = random.random()
    mean = cfg["ticket_mean"]
    std  = cfg["ticket_std"]

    if r < 0.05:
        # Outlier alto: celebración, grupo grande
        ticket = mean * random.uniform(1.8, 3.5)
    elif r < 0.08:
        # Outlier bajo: pedido rápido
        ticket = mean * random.uniform(0.30, 0.55)
    else:
        # Log-normal: media y varianza equivalentes pero cola derecha más pesada
        mu_ln  = np.log(mean ** 2 / np.sqrt(mean ** 2 + std ** 2))
        sig_ln = np.sqrt(np.log(1 + (std / mean) ** 2))
        ticket = np.random.lognormal(mu_ln, sig_ln)

    # Fin de semana +15% promedio
    if fecha.weekday() >= 4:
        ticket *= random.uniform(1.05, 1.25)

    return max(50.0, round(ticket, 2))


# ---------------------------------------------------------------------------
# Generadores de documentos
# ---------------------------------------------------------------------------

def _venta(mesero, mesa_num, cfg, menu, popularidad, pesos_pop, eventos):
    fecha    = _fecha_aleatoria(eventos_especiales=eventos)
    es_finde = fecha.weekday() >= 4

    ticket_target = _ticket_con_ruido(cfg, fecha)
    items, subtotal = _generar_items(ticket_target, menu, popularidad, pesos_pop)

    metodo      = random.choices(METODOS_PAGO, weights=METODOS_PESOS)[0]
    pct_propina = _propina_pct(metodo, es_finde)
    impuesto    = round(subtotal * 0.16, 2)
    propina     = round(subtotal * pct_propina / 100, 2)
    total       = round(subtotal + impuesto, 2)
    total_final = round(total + propina, 2)
    personas    = random.randint(1, 8) if es_finde else random.randint(1, 5)

    doc = {
        "mesa_id":             str(mesa_num),
        "mesa_nombre":         f"Mesa {mesa_num}",
        "mesa_numero":         mesa_num,
        "mesero_id":           str(mesero["_id"]),
        "mesero_nombre":       mesero["nombre"],
        "cliente_nombre":      f"Cliente {random.randint(100, 999)}",
        "items":               items,
        "platillos":           items,
        "subtotal":            subtotal,
        "impuesto":            impuesto,
        "descuento":           0.0,
        "propina":             propina,
        "porcentaje_propina":  pct_propina,
        "total":               total,
        "total_final":         total_final,
        "metodo_pago":         metodo,
        "comensales":          personas,
        "num_personas":        personas,
        "estado":              "completada",
        "notas":               "",
        "fecha":               fecha,
        "fecha_creacion":      fecha,
        "fecha_actualizacion": fecha,
        "fecha_completada":    fecha,
        "_seeded":             True,
    }
    if metodo == "mercadopago":
        doc["payment_id"] = random.randint(100_000_000_000, 999_999_999_999)
    return doc


def _comanda(venta, mesero, mesa_num):
    duracion     = timedelta(minutes=random.randint(20, 110))
    fecha_cierre = venta["fecha"] + duracion
    return {
        "mesa_numero":         mesa_num,
        "num_comensales":      venta["comensales"],
        "mesero_id":           mesero["_id"],
        "mesero_nombre":       mesero["nombre"],
        "estado":              random.choice(["pagada", "cerrada"]),
        "items":               venta["items"],
        "total":               venta["total"],
        "propina":             venta["propina"],
        "porcentaje_propina":  venta["porcentaje_propina"],
        "total_final":         venta["total_final"],
        "metodo_pago":         venta["metodo_pago"],
        "fecha_apertura":      venta["fecha"],
        "fecha_cierre":        fecha_cierre,
        "fecha_actualizacion": fecha_cierre,
        "folio":               f"COM-{venta['fecha'].strftime('%y%m%d%H%M%S')}-{random.randint(10,99)}",
        "_seeded":             True,
    }


# ---------------------------------------------------------------------------
# Mesas físicas
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
    col   = db["mesas"]
    ahora = datetime.utcnow()
    ins   = 0
    for m in MESAS_RESTAURANTE:
        if not col.find_one({"numero": m["numero"]}):
            col.insert_one({**m, "estado": "disponible", "activa": True, "created_at": ahora})
            ins += 1
    total = col.count_documents({"activa": True})
    print(f"  Mesas: {ins} nuevas — {total} activas")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def seed(n=2000, limpiar=False):
    print("  Verificando mesas...")
    seed_mesas()

    menu = list(db.platillos.find({"disponible": True}, {"_id": 1, "nombre": 1, "precio": 1, "categoria": 1}))
    if not menu:
        print("  ⚠️  No hay platillos disponibles. Abortando.")
        return
    print(f"  Menú: {len(menu)} platillos")

    meseros_bd = list(db.usuarios.find({"usuario_rol": "2"}, {"_id": 1, "usuario_nombre": 1, "nombre": 1}))
    meseros = [{"_id": m["_id"], "nombre": m.get("usuario_nombre") or m.get("nombre", "Mesero")} for m in meseros_bd]
    if not meseros:
        print("  ⚠️  No hay meseros (rol 2). Abortando.")
        return
    print(f"  Meseros: {[m['nombre'] for m in meseros]}")

    if limpiar:
        rv = db.ventas.delete_many({"_seeded": True})
        rc = db.comandas.delete_many({"_seeded": True})
        print(f"  Limpiado: {rv.deleted_count} ventas, {rc.deleted_count} comandas")

    # Popularidad Pareto sobre el menú real
    popularidad, pesos_pop = _construir_popularidad(menu)

    # Eventos especiales: ~1 por mes, preferentemente fin de semana
    eventos = _generar_eventos(dias_atras=180)
    print(f"  Eventos especiales: {len(eventos)} fechas con pico de demanda")

    mesas_ids   = list(MESAS.keys())
    mesas_pesos = [MESAS[m]["peso"] for m in mesas_ids]

    ventas_docs   = []
    comandas_docs = []

    for i in range(n):
        mesa_num = random.choices(mesas_ids, weights=mesas_pesos)[0]
        cfg      = MESAS[mesa_num]
        mesero   = random.choice(meseros)

        v = _venta(mesero, mesa_num, cfg, menu, popularidad, pesos_pop, eventos)
        c = _comanda(v, mesero, mesa_num)
        ventas_docs.append(v)
        comandas_docs.append(c)

        if (i + 1) % 500 == 0:
            print(f"  Generados {i+1}/{n}...")

    db.ventas.insert_many(ventas_docs)
    db.comandas.insert_many(comandas_docs)

    vip_n  = sum(1 for v in ventas_docs if v["mesa_numero"] in [1, 2])
    reg_n  = sum(1 for v in ventas_docs if v["mesa_numero"] in [3, 4, 5])
    ocas_n = sum(1 for v in ventas_docs if v["mesa_numero"] in [6, 7, 8])

    print(f"\n  {n} ventas   >> '{MONGO_DB}.ventas'")
    print(f"  {n} comandas >> '{MONGO_DB}.comandas'")
    print(f"\n  Distribución:")
    print(f"    VIP       (mesas 1-2):  {vip_n:>4}  | ticket log-normal, outliers incluidos")
    print(f"    Regular   (mesas 3-5):  {reg_n:>4}  | fin de semana +15-25%")
    print(f"    Ocasional (mesas 6-8):  {ocas_n:>4}  | días semana muy bajos")
    print(f"\n  Top 3 platillos por popularidad Pareto:")
    for i, p in enumerate(popularidad[:3]):
        print(f"    {i+1}. {p['nombre']}  (${p['precio']})")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed Restaurante Callejón 9 — distribuciones no lineales")
    parser.add_argument("--n",       type=int,            default=2000, help="Número de registros (default: 2000)")
    parser.add_argument("--limpiar", action="store_true",               help="Eliminar seeds previos antes de insertar")
    args = parser.parse_args()

    print(f"\nConectando a {MONGO_DB}...")
    seed(n=args.n, limpiar=args.limpiar)
    print("\nDone.\n")
