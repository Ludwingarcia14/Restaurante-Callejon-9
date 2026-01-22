import pdfplumber
import re
import logging
import unicodedata
import os

logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_TRASPASOS_PROPIOS = ["TRANSFERENCIA RECIBIDA"]
KW_DEVOLUCIONES = ["DEVOLUCION DE DINERO"]
KW_TPV = ["COBRO", "VENTA"]

KW_INGRESOS_VALIDOS = [
    "ENTRADA DE DINERO",
    "TRANSFERENCIA RECIBIDA",
    "LIBERACION DE DINERO",
    "GANANCIA RENDIMIENTOS",
    "GANANCIA BENEFICIO"
]

KW_EXCLUIR = [
    "PAGO",
    "COMPRA",
    "COBRO AUTOMATICO",
    "SUSCRIPCION",
    "SERVICIOS"
]

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

def analizar_mercadopago(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "MERCADO PAGO",
        "periodo": "NO ENCONTRADO",
        "saldo_inicial": 0.0,
        "saldo_promedio": 0.0,
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

            m_per = re.search(
                r'PERIODO:\s*DEL\s+\d+\s+AL\s+\d+\s+DE\s+[A-Z]+\s+DE\s+\d{4}',
                full_text,
                re.IGNORECASE
            )
            if m_per:
                data["periodo"] = m_per.group(0).upper()

            m_ini = re.search(
                r'SALDO INICIAL:\s*\$\s*([\d,]+\.\d{2})',
                full_text,
                re.IGNORECASE
            )
            if m_ini:
                data["saldo_inicial"] = parse_float(m_ini.group(1)) or 0.0

            print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

            bloque = re.split(r'DETALLE DE MOVIMIENTOS', full_text, flags=re.IGNORECASE)
            if len(bloque) < 2:
                return data

            # 🔧 CAMBIO REAL: PROCESAR TODAS LAS PÁGINAS
            lineas = "\n".join(bloque[1:]).splitlines()

            for linea in lineas:
                linea_norm = normalizar(linea)

                if any(k in linea_norm for k in KW_EXCLUIR):
                    continue

                montos_raw = re.findall(r'\$\s*\d{1,3}(?:,\d{3})*\.\d{2}', linea)
                if not montos_raw:
                    continue

                montos = [parse_float(m) for m in montos_raw if parse_float(m)]
                if not montos:
                    continue

                # Mercado Pago: último es saldo → se ignora
                monto = max(montos[:-1]) if len(montos) > 1 else montos[0]
                if monto <= 0:
                    continue

                tipo = "VALIDO"

                if any(k in linea_norm for k in KW_DEVOLUCIONES):
                    tipo = "DEVOLUCION"
                    data["descartes"]["devoluciones"] += monto

                elif any(k in linea_norm for k in KW_TRASPASOS_PROPIOS):
                    tipo = "TRASPASO_PROPIO"
                    data["descartes"]["traspasos"] += monto

                elif any(k in linea_norm for k in KW_INGRESOS_VALIDOS):
                    data["ingresos_netos"] += monto
                else:
                    continue

                if any(k in linea_norm for k in KW_TPV):
                    data["tpv"] += monto

                data["ingresos_brutos"] += monto
                data["log_transacciones"].append(
                    f"[+] ${monto:,.2f} ({tipo}) | {linea_norm[:70]}..."
                )

    except Exception as e:
        return {"error": str(e)}

    return data

if __name__ == "__main__":
    archivo = "MercadoPago.pdf"
    print(f"ANALIZANDO MERCADO PAGO: {archivo}")

    res = analizar_mercadopago(archivo)

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
