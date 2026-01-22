import pytesseract
from pdf2image import convert_from_path
import re
import unicodedata
import os

# ============================
# CONFIG OCR
# ============================
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ============================
# PALABRAS CLAVE
# ============================

KW_IGNORE = [
    "SALDO PROMEDIO",
    "DEPOSITOS", "RETIROS", "CARGOS",
    "COMISIONES", "IVA", "0.00%", "NO APLICA"
]

KW_EGRESOS = [
    "PAGO", "CARGO", "RETIRO", "TRANSFERENCIA A", "COMPRA"
]

KW_TRASPASOS = [
    "TRASPASO", "MISMA CUENTA"
]

KW_CREDITOS = [
    "CREDITO", "PRESTAMO", "FINANCIAMIENTO"
]

KW_DEVOLUCIONES = [
    "DEVOLUCION", "REVERSO"
]

KW_TPV = [
    "TPV", "TERMINAL"
]

# ============================
# UTILS
# ============================

def normalizar(texto):
    return unicodedata.normalize("NFKD", str(texto)).upper()

def parse_float(texto):
    m = re.findall(r'[\d,]+\.\d{2}', texto.replace(" ", ""))
    return float(m[0].replace(",", "")) if m else None

class Dedupe:
    def __init__(self):
        self.vistos = set()

    def nuevo(self, dia, monto):
        key = (dia, round(monto, 2))
        if key in self.vistos:
            return False
        self.vistos.add(key)
        return True

# ============================
# OCR
# ============================

def ocr_pdf(pdf_path):
    texto = ""
    imagenes = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
    for img in imagenes:
        texto += pytesseract.image_to_string(img, lang="spa") + "\n"
    return texto.replace("|", "")

# ============================
# ANALIZADOR HSBC
# ============================

def analizar_hsbc(pdf_path):
    res = {
        "saldo_inicial": None,
        "saldo_final_detectado": None,
        "ingresos": 0.0,
        "egresos": 0.0,
        "traspasos": 0.0,
        "creditos": 0.0,
        "devoluciones": 0.0,
        "tpv": 0.0,
        "log": []
    }

    dedupe = Dedupe()
    texto = ocr_pdf(pdf_path)

    for linea in texto.splitlines():
        l = normalizar(linea)

        # ============================
        # SALDOS DIRECTOS (HSBC)
        # ============================
        if "SALDO INICIAL" in l:
            m = parse_float(l)
            if m is not None:
                res["saldo_inicial"] = m
            continue

        if "SALDO FINAL" in l:
            m = parse_float(l)
            if m is not None:
                res["saldo_final_detectado"] = m
            continue

        # ============================
        # IGNORAR BASURA
        # ============================
        if any(k in l for k in KW_IGNORE):
            continue

        # ============================
        # DIA
        # ============================
        m_dia = re.match(r'\s*(\d{1,2})\s+', l)
        if not m_dia:
            continue

        dia = int(m_dia.group(1))
        if not 1 <= dia <= 31:
            continue

        # ============================
        # MONTOS (monto + saldo)
        # ============================
        montos = re.findall(r'[\d,]+\.\d{2}', l)
        if len(montos) < 2:
            continue

        monto = parse_float(montos[-2])
        saldo = parse_float(montos[-1])

        if monto is None or saldo is None:
            continue

        # Guardar primer saldo como saldo inicial si no vino explícito
        if res["saldo_inicial"] is None:
            res["saldo_inicial"] = saldo + monto

        # Siempre actualizar último saldo detectado
        res["saldo_final_detectado"] = saldo

        # ============================
        # DEDUPE CONTABLE
        # ============================
        es_nuevo = dedupe.nuevo(dia, monto)

        # ============================
        # CLASIFICACION
        # ============================
        if any(k in l for k in KW_TRASPASOS):
            tipo = "TRASPASO"
            if es_nuevo:
                res["traspasos"] += monto

        elif any(k in l for k in KW_CREDITOS):
            tipo = "CREDITO"
            if es_nuevo:
                res["creditos"] += monto

        elif any(k in l for k in KW_DEVOLUCIONES):
            tipo = "DEVOLUCION"
            if es_nuevo:
                res["devoluciones"] += monto

        elif any(k in l for k in KW_EGRESOS):
            tipo = "EGRESO"
            if es_nuevo:
                res["egresos"] += monto

        else:
            tipo = "INGRESO"
            if es_nuevo:
                res["ingresos"] += monto

        if any(k in l for k in KW_TPV) and es_nuevo:
            res["tpv"] += monto

        if not es_nuevo:
            tipo = "DUPLICADO"

        res["log"].append(f"[{tipo}] ${monto:,.2f} | {l[:90]}")

    return res

# ============================
# MAIN
# ============================

if __name__ == "__main__":
    res = analizar_hsbc("HSBC.pdf")

    saldo_calculado = (
        (res["saldo_inicial"] or 0)
        + res["ingresos"]
        - res["egresos"]
    )

    print("\n" + "="*50)
    print(" REPORTE FINAL: HSBC")
    print("="*50)
    print(f"Saldo inicial:     ${res['saldo_inicial']:,.2f}")
    print(f"(+) INGRESOS:      ${res['ingresos']:,.2f}")
    print(f"(-) EGRESOS:       ${res['egresos']:,.2f}")
    print(f"(-) TRASPASOS:     ${res['traspasos']:,.2f}")
    print(f"(+) CREDITOS:      ${res['creditos']:,.2f}")
    print(f"(+) DEVOLUCIONES:  ${res['devoluciones']:,.2f}")
    print(f"Ingresos TPV:      ${res['tpv']:,.2f}")
    print("-"*50)
    print(f"Saldo calculado:   ${saldo_calculado:,.2f}")
    print(f"Saldo HSBC real:   ${res['saldo_final_detectado']:,.2f}")
    print("="*50)

    print("\nDETALLE COMPLETO")
    print("-"*50)
    for i, l in enumerate(res["log"], 1):
        print(f"{i:03d}. {l}")
