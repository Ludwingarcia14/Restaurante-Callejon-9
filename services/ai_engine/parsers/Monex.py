import pytesseract
from pdf2image import convert_from_path
import re
import unicodedata

# ============================
# CONFIG OCR
# ============================
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ============================
# KEYWORDS MONEX
# ============================

KW_IGNORE_MONEX = [
    "ACUMULADO",
    "INFORMATIVO",
    "GAT",
    "TASA",
    "CUENTA DIGITAL",
    "COMISION ANUAL",
    "PRODUCTO GARANTIZADO",
    "IPAB",
    "AVISO",
    "CONCEPTO DEL PERIODO",
    "SALDO PROMEDIO",
    "ISR",
    "INTERESES",
]

# ============================
# UTILS
# ============================

def normalizar(texto):
    return unicodedata.normalize("NFKD", str(texto)).upper()

def parse_float(texto):
    m = re.findall(r'[\d,]+\.\d{2}', texto.replace(" ", ""))
    return float(m[0].replace(",", "")) if m else None

# ============================
# OCR
# ============================

def ocr_pdf(pdf_path):
    texto = ""
    for img in convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH):
        texto += pytesseract.image_to_string(img, lang="spa") + "\n"
    return texto

# ============================
# ANALIZADOR MONEX
# ============================

def analizar_monex(pdf_path):
    res = {
        "saldo_inicial": None,
        "saldo_final": None,
        "total_abonos_resumen": None,
        "total_cargos_resumen": None,
        "ingresos": 0.0,
        "egresos": 0.0,
        "venta_divisas": 0.0,  # solo informativo
        "log": []
    }

    texto = ocr_pdf(pdf_path)

    for linea in texto.splitlines():
        l = normalizar(linea)

        # ============================
        # IGNORAR TEXTO NO CONTABLE
        # ============================
        if any(k in l for k in KW_IGNORE_MONEX):
            continue

        # ============================
        # RESUMEN OFICIAL MONEX
        # ============================
        if "SALDO INICIAL" in l and res["saldo_inicial"] is None:
            m = parse_float(l)
            if m is not None:
                res["saldo_inicial"] = m
                res["log"].append(f"[SALDO INICIAL] ${m:,.2f}")
            continue

        if "+ TOTAL ABONOS" in l:
            m = parse_float(l)
            if m is not None:
                res["total_abonos_resumen"] = m
                res["log"].append(f"[RESUMEN ABONOS] ${m:,.2f}")
            continue

        if "- TOTAL CARGOS" in l:
            m = parse_float(l)
            if m is not None:
                res["total_cargos_resumen"] = m
                res["log"].append(f"[RESUMEN CARGOS] ${m:,.2f}")
            continue

        if "SALDO FINAL" in l or "SALDO TOTAL" in l:
            m = parse_float(l)
            if m is not None:
                res["saldo_final"] = m
                res["log"].append(f"[SALDO FINAL] ${m:,.2f}")
            continue

        # ============================
        # VENTA DE DIVISAS (INFORMATIVO)
        # ============================
        # Solo contar la línea real de venta, NO el depósito por venta
        if "VENTA DE DIVISAS" in l and "DEPOSITO" not in l:
            m = parse_float(l)
            if m:
                res["venta_divisas"] = m  # solo una vez
                res["log"].append(f"[VENTA DIVISAS] ${m:,.2f} | {l[:90]}")
            continue

    # ============================
    # APLICAR RESUMEN (FUENTE DE VERDAD)
    # ============================
    if res["total_abonos_resumen"] is not None:
        res["ingresos"] = res["total_abonos_resumen"]

    if res["total_cargos_resumen"] is not None:
        res["egresos"] = res["total_cargos_resumen"]

    return res

# ============================
# MAIN
# ============================

if __name__ == "__main__":
    res = analizar_monex("MONEX.pdf")

    if res["saldo_inicial"] is None or res["saldo_final"] is None:
        raise ValueError("❌ No se detectó el saldo inicial o final en el estado de cuenta MONEX")

    saldo_calculado = (
        res["saldo_inicial"]
        + res["ingresos"]
        - res["egresos"]
    )

    print("\n" + "=" * 55)
    print(" REPORTE FINAL: MONEX")
    print("=" * 55)
    print(f"Saldo inicial:     ${res['saldo_inicial']:,.2f}")
    print(f"(+) INGRESOS:      ${res['ingresos']:,.2f}")
    print(f"(-) EGRESOS:       ${res['egresos']:,.2f}")
    print(f"Venta de divisas:  ${res['venta_divisas']:,.2f} (informativo)")
    print("-" * 55)
    print(f"Saldo calculado:   ${saldo_calculado:,.2f}")
    print(f"Saldo MONEX real:  ${res['saldo_final']:,.2f}")
    print("=" * 55)

    print("\nDETALLE")
    print("-" * 55)
    for i, l in enumerate(res["log"], 1):
        print(f"{i:03d}. {l}")
