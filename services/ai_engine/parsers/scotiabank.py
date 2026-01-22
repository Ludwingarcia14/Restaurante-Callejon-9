import pdfplumber
import re
import logging
import unicodedata
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = ["TRASPASO", "CUENTAS PROPIAS", "MISMA CUENTA", "CONCENTRACION"]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION"]
KW_TPV = ["TPV", "TERMINAL", "COMERCIO"]

# ============================================================
# UTILIDADES
# ============================================================

def parse_float(text):
    if not text:
        return 0.0
    try:
        return float(re.sub(r"[^\d.-]", "", text.replace(",", "")))
    except:
        return 0.0

def normalizar(text):
    return unicodedata.normalize("NFKD", text).upper().strip() if text else ""

def calcular_promedio_ponderado(saldo_inicial, transacciones, dias):
    if dias <= 0:
        return 0.0
    saldo = saldo_inicial
    acumulado = 0.0
    por_dia = {}

    for dia, monto in transacciones:
        por_dia[dia] = por_dia.get(dia, 0) + monto

    for d in range(1, dias + 1):
        if d in por_dia:
            saldo += por_dia[d]
        acumulado += saldo

    return acumulado / dias

# ============================================================
# FALLBACK BANCARIO (SOLO SI FALLA TEXTO)
# ============================================================

def inferir_saldo_inicial(pdf):
    for p in pdf.pages:
        for table in p.extract_tables():
            headers = [str(h).upper() if h else "" for h in table[0]]
            idx_dep = idx_ret = idx_saldo = -1

            for i, h in enumerate(headers):
                if "PÓSITO" in h or "POSITO" in h:
                    idx_dep = i
                if "RETIRO" in h:
                    idx_ret = i
                if "SALDO" in h:
                    idx_saldo = i

            if idx_saldo == -1:
                continue

            for row in table[1:]:
                row = [str(c).strip() if c else "" for c in row]
                saldo = parse_float(row[idx_saldo])
                dep = parse_float(row[idx_dep]) if idx_dep != -1 else 0
                ret = parse_float(row[idx_ret]) if idx_ret != -1 else 0

                if saldo > 0:
                    return round(saldo - dep + ret, 2)
    return 0.0

# ============================================================
# ANALIZADOR PRINCIPAL
# ============================================================

def analizar_scotiabank(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "SCOTIABANK",
        "periodo": "No Encontrado",
        "saldo_inicial": 0.0,
        "saldo_promedio": 0.0,
        "ingresos_brutos": 0.0,
        "ingresos_netos": 0.0,
        "descartes": {"traspasos": 0.0, "creditos": 0.0, "devoluciones": 0.0},
        "tpv": 0.0,
    }

    transacciones = []
    dias_periodo = 30

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

            # ================= PERIODO =================
            m = re.search(r"(\d{1,2}-[A-Z]{3}-\d{2}/\d{1,2}-[A-Z]{3}-\d{2})", full_text)
            if m:
                data["periodo"] = m.group(1)

            m = re.search(r"No\.\s*de\s+d[ií]as.*?(\d+)", full_text, re.I)
            if m:
                dias_periodo = int(m.group(1))

            # ================= SALDO INICIAL (TU LÓGICA) =================
            m = re.search(
                r"Saldo\s+inicial\s*(?:=)?\s*\$?\s*([\d,]+\.\d{2})",
                full_text,
                re.I
            )
            if m:
                data["saldo_inicial"] = parse_float(m.group(1))

            if data["saldo_inicial"] == 0:
                data["saldo_inicial"] = inferir_saldo_inicial(pdf)

            logging.info(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

            saldo_actual = data["saldo_inicial"]

            # ================= MOVIMIENTOS =================
            for p in pdf.pages:
                for table in p.extract_tables():
                    headers = [str(h).upper() if h else "" for h in table[0]]

                    idx_dep = idx_ret = idx_fecha = idx_concepto = -1
                    for i, h in enumerate(headers):
                        if "PÓSITO" in h or "POSITO" in h:
                            idx_dep = i
                        if "RETIRO" in h:
                            idx_ret = i
                        if "FECHA" in h:
                            idx_fecha = i
                        if "CONCEPTO" in h:
                            idx_concepto = i

                    if idx_dep == -1 and idx_ret == -1:
                        continue

                    for row in table[1:]:
                        row = [str(c).strip() if c else "" for c in row]
                        dep = parse_float(row[idx_dep]) if idx_dep != -1 else 0
                        ret = parse_float(row[idx_ret]) if idx_ret != -1 else 0

                        dia = 1
                        if idx_fecha != -1:
                            m = re.search(r"(\d{1,2})", row[idx_fecha])
                            if m:
                                dia = int(m.group(1))

                        saldo_actual += dep - ret
                        transacciones.append((dia, dep - ret))

                        if dep > 0:
                            desc = normalizar(row[idx_concepto]) if idx_concepto != -1 else ""

                            if any(k in desc for k in KW_TRASPASOS):
                                data["descartes"]["traspasos"] += dep
                            elif any(k in desc for k in KW_CREDITOS):
                                data["descartes"]["creditos"] += dep
                            elif any(k in desc for k in KW_DEVOLUCIONES):
                                data["descartes"]["devoluciones"] += dep
                            else:
                                data["ingresos_netos"] += dep

                            if any(k in desc for k in KW_TPV):
                                data["tpv"] += dep

                            data["ingresos_brutos"] += dep

            # ================= SALDO PROMEDIO =================
            data["saldo_promedio"] = calcular_promedio_ponderado(
                data["saldo_inicial"], transacciones, dias_periodo
            )

    except Exception as e:
        return {"error": str(e)}

    return data

# ============================================================
# EJECUCIÓN (ESTA PARTE ERA LA QUE FALTABA)
# ============================================================

if __name__ == "__main__":
    archivo = "scotiabank.pdf"

    print(f"\nANALIZANDO SCOTIABANK: {archivo}")
    res = analizar_scotiabank(archivo)

    if "error" in res:
        print("ERROR:", res["error"])
    else:
        print("\n" + "=" * 60)
        print(f" BANCO: {res['banco']}")
        print("=" * 60)
        print(f"Periodo:            {res['periodo']}")
        print(f"Saldo Inicial:      ${res['saldo_inicial']:,.2f}")
        print(f"Saldo Promedio:     ${res['saldo_promedio']:,.2f}")
        print("-" * 40)
        print(f"Ingresos Brutos:    ${res['ingresos_brutos']:,.2f}")
        print(f"Traspasos:          ${res['descartes']['traspasos']:,.2f}")
        print(f"Créditos:           ${res['descartes']['creditos']:,.2f}")
        print(f"Devoluciones:       ${res['descartes']['devoluciones']:,.2f}")
        print("-" * 40)
        print(f"Ingreso Neto Real:  ${res['ingresos_netos']:,.2f}")
        print(f"Ingresos TPV:       ${res['tpv']:,.2f}")
        print("=" * 60)
