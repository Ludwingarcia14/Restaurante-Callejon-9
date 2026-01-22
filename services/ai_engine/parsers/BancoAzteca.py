import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN BANCO AZTECA
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = [
    "TRASPASO", "CUENTAS PROPIAS", "MISMA CUENTA",
    "INVERSION", "MERCADO DE DINERO", "PAGO DE CHEQUE"
]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "VENTA", "TERMINAL", "AFILIACION"]

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
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

# ====================================================================

def calcular_promedio_ponderado(saldo_inicial, transacciones, dias_totales=30):
    if dias_totales <= 0:
        return 0.0

    saldo_actual = saldo_inicial
    saldo_acumulado = 0.0
    movimientos = {}

    for dia, monto in transacciones:
        movimientos.setdefault(dia, 0.0)
        movimientos[dia] += monto

    for d in range(1, dias_totales + 1):
        if d in movimientos:
            saldo_actual += movimientos[d]
        saldo_acumulado += saldo_actual

    return saldo_acumulado / dias_totales

# ====================================================================
# 🔥 MOTOR MATEMÁTICO AZTECA (CARGO / ABONO REAL)
# ====================================================================

def procesar_fila_matematica(numeros_fila, fecha_str, desc, saldo_actual, transacciones, data):
    posible_nuevo_saldo = numeros_fila[-1]
    diff = posible_nuevo_saldo - saldo_actual

    if abs(diff) < 0.01:
        return saldo_actual

    # En Azteca:
    # [..., CARGO, ABONO, SALDO]
    cargo = numeros_fila[-3] if len(numeros_fila) >= 3 else 0.0
    abono = numeros_fila[-2] if len(numeros_fila) >= 2 else 0.0

    if diff > 0 and abono > 0:
        monto = abono
        es_ingreso = True
    elif diff < 0 and cargo > 0:
        monto = cargo
        es_ingreso = False
    else:
        return saldo_actual

    # Día del movimiento
    match_dia = re.search(r"\d{4}-\d{2}-(\d{2})", fecha_str)
    dia = int(match_dia.group(1)) if match_dia else 1
    transacciones.append((dia, diff))

    if es_ingreso:
        desc_norm = normalizar(desc)
        tipo = "VALIDO"

        if any(k in desc_norm for k in KW_TRASPASOS):
            data["descartes"]["traspasos"] += monto
            tipo = "TRASPASO"

        elif any(k in desc_norm for k in KW_CREDITOS):
            data["descartes"]["creditos"] += monto
            tipo = "CREDITO"

        elif any(k in desc_norm for k in KW_DEVOLUCIONES):
            data["descartes"]["devoluciones"] += monto
            tipo = "DEVOLUCION"

        else:
            data["ingresos_netos"] += monto

        if any(k in desc_norm for k in KW_TPV):
            data["tpv"] += monto

        data["ingresos_brutos"] += monto
        data["log_transacciones"].append(
            f"[+] ${monto:,.2f} ({tipo}) | {desc[:50]}..."
        )

    return posible_nuevo_saldo

# ====================================================================

def analizar_bancoazteca(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "BANCO AZTECA",
        "periodo": "No Encontrado",
        "saldo_inicial": 0.0,
        "saldo_promedio": 0.0,
        "ingresos_brutos": 0.0,
        "ingresos_netos": 0.0,
        "descartes": {"traspasos": 0.0, "creditos": 0.0, "devoluciones": 0.0},
        "tpv": 0.0,
        "log_transacciones": []
    }

    transacciones = []
    dias_del_periodo = 30

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        # PERIODO
        m = re.search(r"DEL\s+(\d{1,2}\s+AL\s+\d{1,2}\s+DE\s+[A-Z]+\s+\d{4})", full_text, re.I)
        if m:
            data["periodo"] = m.group(1).upper()

        # SALDOS
        m = re.search(r"SALDO INICIAL.*?\$\s*([\d,]+\.\d{2})", full_text, re.I)
        if m:
            data["saldo_inicial"] = parse_float(m.group(1))

        m = re.search(r"SALDO PROMEDIO.*?\$\s*([\d,]+\.\d{2})", full_text, re.I)
        if m:
            data["saldo_promedio"] = parse_float(m.group(1))

        print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")
        saldo_actual = data["saldo_inicial"]
        movimientos_encontrados = False

        # ==============================
        # FASE A: TABLAS
        # ==============================
        for p in pdf.pages:
            for table in p.extract_tables() or []:
                for row in table:
                    row = [str(c).strip() if c else "" for c in row]

                    if not row or not re.match(r"\d{4}-\d{2}-\d{2}", row[0]):
                        continue

                    numeros = [parse_float(c) for c in row if parse_float(c) is not None]
                    if len(numeros) < 3:
                        continue

                    desc = " ".join(c for c in row if parse_float(c) is None)

                    nuevo = procesar_fila_matematica(
                        numeros, row[0], desc,
                        saldo_actual, transacciones, data
                    )

                    if nuevo != saldo_actual:
                        saldo_actual = nuevo
                        movimientos_encontrados = True

        # ==============================
        # FASE B: FALLBACK TEXTO
        # ==============================
        if not movimientos_encontrados:
            logging.info("Tablas no detectadas, usando escáner de texto...")
            saldo_actual = data["saldo_inicial"]

            for line in full_text.split("\n"):
                if not re.search(r"\d{4}-\d{2}-\d{2}", line):
                    continue

                montos = [parse_float(x) for x in re.findall(r"[\d,]+\.\d{2}", line)]
                montos = [m for m in montos if m is not None]
                if len(montos) < 3:
                    continue

                fecha = re.search(r"(\d{4}-\d{2}-\d{2})", line).group(1)

                nuevo = procesar_fila_matematica(
                    montos, fecha, line,
                    saldo_actual, transacciones, data
                )

                if nuevo != saldo_actual:
                    saldo_actual = nuevo

        # PROMEDIO
        if data["saldo_promedio"] == 0:
            print("Calculando Saldo Promedio Matemáticamente...")
            data["saldo_promedio"] = calcular_promedio_ponderado(
                data["saldo_inicial"], transacciones, dias_del_periodo
            )

    return data

# ====================================================================

if __name__ == "__main__":
    archivo = "BancoAzteca.pdf"
    print(f"ANALIZANDO BANCO AZTECA: {archivo}")
    res = analizar_bancoazteca(archivo)

    print("\n" + "=" * 50)
    print(f" REPORTE FINAL: {res['banco']}")
    print("=" * 50)
    print(f"Periodo:                {res['periodo']}")
    print(f"Saldo Anterior:         ${res['saldo_inicial']:,.2f}")
    print(f"Saldo Promedio:         ${res['saldo_promedio']:,.2f}")
    print("-" * 30)
    print(f"(+) INGRESOS BRUTOS:    ${res['ingresos_brutos']:,.2f}")
    print(f"(-) Traspasos Propios:  ${res['descartes']['traspasos']:,.2f}")
    print(f"(-) Créditos:           ${res['descartes']['creditos']:,.2f}")
    print(f"(-) Devoluciones:       ${res['descartes']['devoluciones']:,.2f}")
    print("-" * 30)
    print(f"(=) INGRESO NETO REAL:  ${res['ingresos_netos']:,.2f}")
    print("-" * 30)
    print(f"Ingresos TPV:           ${res['tpv']:,.2f}")
    print("=" * 50)

    if res["log_transacciones"]:
        print(f"\n[INFO] Movimientos detectados: {len(res['log_transacciones'])}")
        for l in res["log_transacciones"][:5]:
            print(l)
