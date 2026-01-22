import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN BANCA MIFEL (V6 - TPV BLINDADO)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = [
    "DISPOSICION", "CREDITO", "PRESTAMO",
    "FINANCIAMIENTO", "LINEA DE CREDITO"
]

KW_DEVOLUCIONES = [
    "DEVOLUCION", "DEVOLUC",
    "REVERSO", "CANCELACION", "RETORNO"
]

# 🔥 TPV CON ID (TPxxxx / TMxxxx)
TPV_REGEX = re.compile(r'\b(TP|TM)\s*([0-9]{4,6})\b', re.IGNORECASE)

# SPEI normal
SPEI_REGEX = re.compile(r'\bSPEI\b', re.IGNORECASE)

# ====================================================================

def parse_float(text):
    if not text:
        return None
    clean = re.sub(r"[^\d.-]", "", str(text).replace(",", "")).rstrip(".")
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    if not text:
        return ""
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

# ====================================================================

def procesar_fila_matematica(numeros_fila, fecha_str, desc, saldo_actual, transacciones, data):
    posible_nuevo_saldo = numeros_fila[-1]
    diff = posible_nuevo_saldo - saldo_actual

    if abs(diff) < 0.01:
        return saldo_actual

    monto = None
    for n in reversed(numeros_fila[:-1]):
        if abs(abs(diff) - n) < 1.0:
            monto = n
            break

    if monto is None:
        return saldo_actual

    try:
        dia = int(fecha_str.split("/")[0])
    except:
        dia = 1
    transacciones.append((dia, diff))

    if diff > 0:
        desc_norm = normalizar(desc)
        tipo = "OPERATIVO"

        # 1️⃣ DEVOLUCIÓN
        if any(k in desc_norm for k in KW_DEVOLUCIONES):
            data["devoluciones"] += monto
            tipo = "DEVOLUCION"

        # 2️⃣ CRÉDITO
        elif any(k in desc_norm for k in KW_CREDITOS):
            data["creditos"] += monto
            tipo = "CREDITO"

        # 3️⃣ TPV (CON Y SIN ID)
        elif "TP" in desc_norm or "TM" in desc_norm:

            m = TPV_REGEX.search(desc_norm)

            # --- TPV CON ID ---
            if m:
                tpv_id = m.group(2)

                if tpv_id not in data["tpv_ids"]:
                    data["tpv_ids"].add(tpv_id)
                    data["ingreso_fiscal"] += monto
                    data["tpv"] += monto
                    tipo = "TPV_FISCAL"
                else:
                    tipo = "TPV_DUPLICADO"

            # --- TPV SIN ID (ej. TM 500,000.00) ---
            else:
                clave = (fecha_str, round(monto, 2))

                if clave not in data["tpv_sin_id"]:
                    data["tpv_sin_id"].add(clave)
                    data["ingreso_fiscal"] += monto
                    data["tpv"] += monto
                    tipo = "TPV_FISCAL"
                else:
                    tipo = "TPV_DUPLICADO"

        # 4️⃣ SPEI → FLUJO
        elif SPEI_REGEX.search(desc_norm):
            data["flujo"] += monto
            tipo = "FLUJO_SPEI"

        # 5️⃣ OPERATIVO
        else:
            data["ingreso_operativo"] += monto
            tipo = "OPERATIVO"

        data["ingresos_brutos"] += monto

        if tipo != "TPV_DUPLICADO":
            data["log"].append(
                f"[+] ${monto:,.2f} ({tipo}) | {desc[:60]}..."
            )

    return posible_nuevo_saldo

# ====================================================================

def analizar_mifel(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "MIFEL",
        "periodo": "No Encontrado",
        "saldo_inicial": 0.0,
        "saldo_promedio": 0.0,

        "ingresos_brutos": 0.0,
        "ingreso_fiscal": 0.0,
        "ingreso_operativo": 0.0,
        "flujo": 0.0,
        "devoluciones": 0.0,
        "creditos": 0.0,
        "tpv": 0.0,

        # 🔥 CONTROL TPV
        "tpv_ids": set(),
        "tpv_sin_id": set(),

        "log": []
    }

    transacciones = []

    with pdfplumber.open(pdf_path) as pdf:
        texto_completo = ""
        for p in pdf.pages:
            texto_completo += p.extract_text(x_tolerance=2, y_tolerance=3) or "" + "\n"

        # PERIODO
        m = re.search(
            r"DEL\s+(\d{2}/\d{2}/\d{4})\s+AL\s+(\d{2}/\d{2}/\d{4})",
            texto_completo, re.IGNORECASE
        )
        if m:
            data["periodo"] = f"{m.group(1)} - {m.group(2)}"

        # SALDOS
        m = re.search(r"Saldo inicial\s*\$?\s*([\d,]+\.\d{2})", texto_completo, re.IGNORECASE)
        if m:
            data["saldo_inicial"] = parse_float(m.group(1))

        m = re.search(r"Saldo promedio diario\s*\$?\s*([\d,]+\.\d{2})", texto_completo, re.IGNORECASE)
        if m:
            data["saldo_promedio"] = parse_float(m.group(1))

        print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")
        saldo_actual = data["saldo_inicial"]

        # ==============================
        # FASE A: TABLAS
        # ==============================
        movimientos_detectados = False
        for p in pdf.pages:
            for table in p.extract_tables() or []:
                for row in table:
                    row_clean = [str(c).strip() if c else "" for c in row]
                    fecha = next((c for c in row_clean if re.match(r"\d{1,2}/\d{2}/\d{4}", c)), None)
                    if not fecha:
                        continue

                    nums = [parse_float(c) for c in row_clean if parse_float(c) is not None]
                    if len(nums) < 2:
                        continue

                    nuevo_saldo = procesar_fila_matematica(
                        nums, fecha, " ".join(row_clean),
                        saldo_actual, transacciones, data
                    )

                    if nuevo_saldo != saldo_actual:
                        saldo_actual = nuevo_saldo
                        movimientos_detectados = True

        # ==============================
        # FASE B: TEXTO (FALLBACK)
        # ==============================
        if not movimientos_detectados or data["ingresos_brutos"] == 0:
            print("⚠️ Modo Tablas sin resultados. Activando Escáner de Texto...")
            saldo_actual = data["saldo_inicial"]

            for line in texto_completo.split("\n"):
                m_fecha = re.search(r"(\d{1,2}/\d{2}/\d{4})", line)
                if not m_fecha:
                    continue

                fecha = m_fecha.group(1)
                montos = [parse_float(x) for x in re.findall(r"[\d,]+\.\d{2}", line)]
                montos = [m for m in montos if m is not None]

                if len(montos) < 2:
                    continue

                nuevo = procesar_fila_matematica(
                    montos, fecha, line,
                    saldo_actual, transacciones, data
                )

                if nuevo != saldo_actual:
                    saldo_actual = nuevo

    data["ingreso_neto_real"] = data["ingreso_fiscal"] + data["ingreso_operativo"]
    return data

# ====================================================================

if __name__ == "__main__":
    archivo = "Mifel.pdf"
    print(f"ANALIZANDO MIFEL (V6 TPV FINAL): {archivo}")
    res = analizar_mifel(archivo)

    print("\n" + "=" * 60)
    print(f" REPORTE FINAL: {res['banco']}")
    print("=" * 60)
    print(f"Periodo:              {res['periodo']}")
    print(f"Saldo Inicial:        ${res['saldo_inicial']:,.2f}")
    print(f"Saldo Promedio:       ${res['saldo_promedio']:,.2f}")
    print("-" * 40)
    print(f"Ingresos Brutos:      ${res['ingresos_brutos']:,.2f}")
    print(f"Ingreso Fiscal (TPV): ${res['ingreso_fiscal']:,.2f}")
    print(f"Ingreso Operativo:    ${res['ingreso_operativo']:,.2f}")
    print(f"Flujo (SPEI):         ${res['flujo']:,.2f}")
    print("-" * 40)
    print(f"Devoluciones:         ${res['devoluciones']:,.2f}")
    print(f"Créditos:             ${res['creditos']:,.2f}")
    print("=" * 60)
