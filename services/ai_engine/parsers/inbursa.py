import pdfplumber
import re
import logging
import unicodedata
import os

logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_TRASPASOS_PROPIOS = [
    "TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "MISMA CUENTA",
    "INVERSION", "MERCADO DE DINERO", "PROPIA", "DE TU CUENTA",
    "A TU CUENTA"
]

KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV", "DEP POR TPV", "VENTA"]

def parse_float(text):
    if not text:
        return None
    clean = re.sub(r"[^\d.-]", "", str(text))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    if not text:
        return ""
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

def analizar_inbursa(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "INBURSA",
        "periodo": "NO ENCONTRADO",
        "saldo_promedio": 0.0,
        "saldo_inicial": 0.0,
        "ingresos_brutos": 0.0,
        "ingresos_netos": 0.0,
        "descartes": {"traspasos": 0.0, "devoluciones": 0.0},
        "tpv": 0.0,
        "log_transacciones": []
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for p in pdf.pages:
                full_text += (p.extract_text() or "") + "\n"

            match_per = re.search(
                r'Del\s+\d{2}\s+[A-Za-z]{3}\.?\s+\d{4}\s+al\s+\d{2}\s+[A-Za-z]{3}\.?\s+\d{4}',
                full_text,
                re.IGNORECASE
            )
            if match_per:
                data["periodo"] = match_per.group(0).upper()

            match_ini = re.search(r'SALDO ANTERIOR\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_ini:
                data["saldo_inicial"] = parse_float(match_ini.group(1)) or 0.0

            match_prom = re.search(r'SALDO PROMEDIO\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom:
                data["saldo_promedio"] = parse_float(match_prom.group(1)) or 0.0

            print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

            for page in pdf.pages:
                for table in page.extract_tables():
                    if not table or len(table) < 2:
                        continue

                    headers = [str(h).upper() if h else "" for h in table[0]]

                    if not any("CONCEPTO" in h for h in headers):
                        continue

                    for row in table[1:]:
                        row_text = " ".join([str(c) for c in row if c])
                        row_norm = normalizar(row_text)

                        if "COMISION" in row_norm or "IVA" in row_norm or "CARGO" in row_norm:
                            continue

                        montos = re.findall(r'\b\d{1,3}(?:,\d{3})*\.\d{2}\b', row_text)

                        for m in montos:
                            monto = parse_float(m)
                            if not monto or monto < 100:
                                continue

                            # 🔧 CAMBIO INICIA AQUÍ (SOLO LÓGICA)
                            es_spei = "SPEI" in row_norm
                            es_efectivo = "EFECTIVO" in row_norm

                            tipo = "VALIDO"

                            if (
                                "TRASPASO ENTRE CUENTAS" in row_norm
                                and "DE TU CUENTA" in row_norm
                                and not es_spei
                                and not es_efectivo
                            ):
                                tipo = "TRASPASO_PROPIO"
                                data["descartes"]["traspasos"] += monto

                            elif any(k in row_norm for k in KW_DEVOLUCIONES):
                                tipo = "DEVOLUCION"
                                data["descartes"]["devoluciones"] += monto

                            else:
                                data["ingresos_netos"] += monto
                            # 🔧 CAMBIO TERMINA AQUÍ

                            if any(k in row_norm for k in KW_TPV):
                                data["tpv"] += monto

                            data["ingresos_brutos"] += monto
                            data["log_transacciones"].append(
                                f"[+] ${monto:,.2f} ({tipo}) | {row_norm[:60]}..."
                            )

    except Exception as e:
        return {"error": str(e)}

    return data

# ------------------------------------------------------------------

if __name__ == "__main__":
    archivo = "inbursa.pdf"
    print(f"ANALIZANDO INBURSA (V2.2 AFINADO): {archivo}")

    res = analizar_inbursa(archivo)

    print("\n" + "=" * 60)
    print(f" REPORTE FINAL: {res['banco']}")
    print("=" * 60)
    print(f"Periodo:                {res['periodo']}")
    print(f"Saldo Anterior:         ${res['saldo_inicial']:,.2f}")
    print(f"Saldo Promedio:         ${res['saldo_promedio']:,.2f}")
    print("-" * 40)
    print(f"(+) INGRESOS BRUTOS:    ${res['ingresos_brutos']:,.2f}")
    print(f"(-) Traspasos Propios:  ${res['descartes']['traspasos']:,.2f}")
    print(f"(-) Devoluciones:       ${res['descartes']['devoluciones']:,.2f}")
    print("-" * 40)
    print(f"(=) INGRESO NETO REAL:  ${res['ingresos_netos']:,.2f}")
    print("-" * 40)
    print(f"Ingresos TPV:           ${res['tpv']:,.2f}")
    print("=" * 60)

    print(f"\n[INFO] Movimientos detectados: {len(res['log_transacciones'])}")
    print(res['log_transacciones'][:5])
