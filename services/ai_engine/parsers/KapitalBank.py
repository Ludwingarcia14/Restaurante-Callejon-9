import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN KAPITAL BANK (V3 - RESUMEN + MOVIMIENTOS)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = [
    "TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "TRASPASO A CUENTA", "MISMA CUENTA",
    "TRASPASO A TERCEROS", "TRASPASO A CTA", "TRASPASO BEM", "TEF", "TRASPASO",
    "DE LA CUENTA", "INVERSION", "MERCADO DE DINERO", "PROPIA", "TRASPASO ENV",
    "ENVIADO A CUENTA", "PAGO CAPITAL", "PAGO INTERES"
]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV", "DEP POR TPV"]

# ====================================================================
# UTILIDADES
# ====================================================================

def parse_float(text):
    if not text:
        return 0.0
    try:
        return float(re.sub(r"[^\d.-]", "", str(text).replace(",", "")))
    except:
        return 0.0

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper().strip() if text else ""

def calcular_promedio_ponderado(saldo_inicial, transacciones, dias_totales):
    if dias_totales <= 0:
        return 0.0

    saldo = saldo_inicial
    acumulado = 0.0
    movs_por_dia = {}

    for dia, monto in transacciones:
        movs_por_dia[dia] = movs_por_dia.get(dia, 0.0) + monto

    for d in range(1, dias_totales + 1):
        if d in movs_por_dia:
            saldo += movs_por_dia[d]
        acumulado += saldo

    return acumulado / dias_totales

# ====================================================================
# ANALIZADOR PRINCIPAL
# ====================================================================

def analizar_kapitalbank(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "KAPITAL BANK",
        "periodo": "No Encontrado",
        "saldo_inicial": 0.0,
        "saldo_promedio": 0.0,
        "ingresos_brutos": 0.0,
        "ingresos_netos": 0.0,
        "descartes": {
            "traspasos": 0.0,
            "creditos": 0.0,
            "devoluciones": 0.0
        },
        "tpv": 0.0,
        "log_transacciones": []
    }

    transacciones_con_fecha = []
    dias_del_periodo = 30

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(
                p.extract_text(x_tolerance=2, y_tolerance=3) or ""
                for p in pdf.pages
            )

            # ============================================================
            # 1. PERIODO
            # ============================================================
            m = re.search(
                r"(\d{1,2}-[A-Za-z]{3,}-\d{4}\s+al\s+\d{1,2}-[A-Za-z]{3,}-\d{4})",
                full_text
            )
            if m:
                data["periodo"] = m.group(1).upper()

            m = re.search(r"No\.\s*de\s*d[ií]as\s+en\s+el\s+per[ií]odo\s*(\d+)", full_text, re.I)
            if m:
                dias_del_periodo = int(m.group(1))

            # ============================================================
            # 2. SALDOS (RESUMEN)
            # ============================================================
            m = re.search(r"Saldo\s+Inicial\s*\$?\s*([\d,]+\.\d{2})", full_text, re.I)
            if m:
                data["saldo_inicial"] = parse_float(m.group(1))

            m = re.search(r"Saldo\s+Promedio\s+Diario\s*\$?\s*([\d,]+\.\d{2})", full_text, re.I)
            if m:
                data["saldo_promedio"] = parse_float(m.group(1))

            logging.info(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

            # ============================================================
            # 3. INGRESOS DESDE RESUMEN (CLAVE EN KAPITAL)
            # ============================================================
            def sumar_resumen(regex):
                m = re.search(regex, full_text, re.I)
                return parse_float(m.group(1)) if m else 0.0

            ingresos_resumen = 0.0
            ingresos_resumen += sumar_resumen(r"Transferencias\s+Recibidas\s*\$\s*([\d,]+\.\d{2})")
            ingresos_resumen += sumar_resumen(r"Otros\s+Abonos\s+a\s+su\s+Cuenta\s*\$\s*([\d,]+\.\d{2})")
            ingresos_resumen += sumar_resumen(r"Intereses\s+Ganados\s*\$\s*([\d,]+\.\d{2})")

            data["ingresos_brutos"] = ingresos_resumen
            data["ingresos_netos"] = ingresos_resumen

            # ============================================================
            # 4. MOVIMIENTOS (SOLO VALIDACIÓN / DETALLE)
            # ============================================================
            saldo_actual = data["saldo_inicial"]

            for p in pdf.pages:
                for table in p.extract_tables():
                    headers = [str(h).upper() if h else "" for h in table[0]]

                    idx_dep = idx_ret = idx_fecha = idx_concept = -1
                    for i, h in enumerate(headers):
                        if "DEPÓSITO" in h or "DEPOSITO" in h:
                            idx_dep = i
                        if "RETIRO" in h:
                            idx_ret = i
                        if "FECHA" in h:
                            idx_fecha = i
                        if "CONCEPTO" in h:
                            idx_concept = i

                    if idx_dep == -1 and idx_ret == -1:
                        continue

                    for row in table[1:]:
                        row = [str(c).strip() if c else "" for c in row]
                        dep = parse_float(row[idx_dep]) if idx_dep < len(row) else 0
                        ret = parse_float(row[idx_ret]) if idx_ret < len(row) else 0

                        dia = 1
                        if idx_fecha < len(row):
                            m = re.search(r"(\d{1,2})", row[idx_fecha])
                            if m:
                                dia = int(m.group(1))

                        saldo_actual += dep - ret
                        if dep or ret:
                            transacciones_con_fecha.append((dia, dep - ret))

                        if dep > 0:
                            desc = normalizar(row[idx_concept]) if idx_concept < len(row) else ""

                            if any(k in desc for k in KW_TRASPASOS):
                                data["descartes"]["traspasos"] += dep
                            elif any(k in desc for k in KW_CREDITOS):
                                data["descartes"]["creditos"] += dep
                            elif any(k in desc for k in KW_DEVOLUCIONES):
                                data["descartes"]["devoluciones"] += dep

                            if any(k in desc for k in KW_TPV):
                                data["tpv"] += dep

                            data["log_transacciones"].append(
                                f"[+] ${dep:,.2f} | {desc[:40]}"
                            )

            # ============================================================
            # 5. SALDO PROMEDIO (SI NO VENÍA EN RESUMEN)
            # ============================================================
            if data["saldo_promedio"] == 0:
                data["saldo_promedio"] = calcular_promedio_ponderado(
                    data["saldo_inicial"],
                    transacciones_con_fecha,
                    dias_del_periodo
                )

    except Exception as e:
        return {"error": str(e)}

    return data

# ====================================================================
# EJECUCIÓN
# ====================================================================

if __name__ == "__main__":
    archivo = "KapitalBank.pdf"

    print(f"\nANALIZANDO KAPITAL BANK (V3): {archivo}")
    res = analizar_kapitalbank(archivo)

    if "error" in res:
        print("ERROR:", res["error"])
    else:
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
            print(f"\n[INFO] Movimientos detectados (ejemplo):")
            print(res["log_transacciones"][:5])
