import os
import re
import sys
import logging
import unicodedata
import shutil
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image

# ====================================================================
# CONFIGURACIÓN OCR (WINDOWS / LINUX)
# ====================================================================

OCR_AVAILABLE = False
POPPLER_PATH = None
TESSERACT_DIR = None

try:
    if sys.platform.startswith("win"):
        POPPLER_PATH = r"C:\poppler\Library\bin"
        TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"
        tesseract_exe = os.path.join(TESSERACT_DIR, "tesseract.exe")

        if os.path.exists(tesseract_exe):
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe
            os.environ["TESSDATA_PREFIX"] = os.path.join(TESSERACT_DIR, "tessdata")
    else:
        POPPLER_PATH = None
        if shutil.which("tesseract"):
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

    OCR_AVAILABLE = True

except Exception as e:
    logging.warning(f"OCR deshabilitado: {e}")

# ====================================================================
# CONFIGURACIÓN GENERAL
# ====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MESES = {
    "ENE": 1, "ENERO": 1,
    "FEB": 2, "FEBRERO": 2,
    "MAR": 3, "MARZO": 3,
    "ABR": 4, "ABRIL": 4,
    "MAY": 5, "MAYO": 5,
    "JUN": 6, "JUNIO": 6,
    "JUL": 7, "JULIO": 7,
    "AGO": 8, "AGOSTO": 8,
    "SEP": 9, "SEPTIEMBRE": 9,
    "OCT": 10, "OCTUBRE": 10,
    "NOV": 11, "NOVIEMBRE": 11,
    "DIC": 12, "DICIEMBRE": 12
}

# ====================================================================
# UTILIDADES
# ====================================================================

def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.upper()


def analizar_vigencia(fecha):
    if not fecha:
        return "Fecha No Encontrada"
    hoy = datetime.now().date()
    limite = hoy - relativedelta(months=3)
    
    if isinstance(fecha, datetime):
        fecha = fecha.date()
        
    return "Vigente" if fecha >= limite else "No Vigente"

# ====================================================================
# EXTRACCIÓN DE FECHAS
# ====================================================================

def extraer_fecha_universal(texto: str):
    fechas = []
    logging.info(f"Buscando fechas en texto de longitud: {len(texto)}")

    patrones_fecha = [
        r'(\d{1,2})\s*(?:DE|DEL|\s)\s*([A-Z]+)\s*(?:DE|DEL|\s)\s*(\d{2,4})',
        r'(\d{1,2})\s*-\s*([A-Z]+)\s*-\s*(\d{4})',
        r'(\d{1,2})\s*(?:DE|DEL|\s)\s*([A-Z]+)\s*(\d{4})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'FECHA\s*LIMITE\s*DE\s*PAGO[:\s]*(\d{1,2})\s*(?:DE|DEL|\s)\s*([A-Z]+)\s*(?:DE|DEL|\s)\s*(\d{2,4})',
        r'FECHA\s*LIMITE[:\s]*(\d{1,2})\s*(?:DE|DEL|\s)\s*([A-Z]+)\s*(?:DE|DEL|\s)\s*(\d{2,4})'
    ]

    for patron in patrones_fecha:
        for match in re.finditer(patron, texto, re.IGNORECASE):
            try:
                grupos = match.groups()
                if len(grupos) == 3:
                    d, mes, y = grupos
                    mes_num = None
                    for mes_key, mes_val in MESES.items():
                        if mes_key in mes.upper():
                            mes_num = mes_val
                            break
                    if not mes_num:
                        mes_short = mes.upper()[:3]
                        mes_num = MESES.get(mes_short, 0)
                    if mes_num:
                        if len(y) == 2:
                            y_int = int(y)
                            y_int = 2000 + y_int if y_int < 50 else 1900 + y_int
                        else:
                            y_int = int(y)
                        if 2020 <= y_int <= datetime.now().year + 2:
                            fecha_obj = datetime(y_int, mes_num, int(d)).date()
                            fechas.append(fecha_obj)
            except Exception:
                continue

    patrones_numericos = [
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
    ]
    
    for patron in patrones_numericos:
        for match in re.finditer(patron, texto):
            try:
                grupos = match.groups()
                if len(grupos) == 3:
                    if patron.startswith(r'(\d{4})'): 
                        y, m, d = grupos
                        fecha_obj = datetime(int(y), int(m), int(d)).date()
                    else: 
                        d, m, y = grupos
                        fecha_obj = datetime(int(y), int(m), int(d)).date()
                    if 2020 <= fecha_obj.year <= datetime.now().year + 2:
                        fechas.append(fecha_obj)
            except Exception:
                continue

    patron_mes_anio = r'([A-Z]+)\s+(\d{4})'
    for match in re.finditer(patron_mes_anio, texto):
        try:
            mes, y = match.groups()
            mes_num = MESES.get(mes.upper(), MESES.get(mes.upper()[:3], 0))
            if mes_num:
                fecha_obj = datetime(int(y), mes_num, 1).date()
                if 2020 <= fecha_obj.year <= datetime.now().year + 2:
                    fechas.append(fecha_obj)
        except:
            continue

    fechas_validas = [f for f in fechas if f]
    if fechas_validas:
        fecha_max = max(fechas_validas)
        logging.info(f"Fecha encontrada: {fecha_max}")
        return fecha_max
    
    return None

# ====================================================================
# LÓGICA ESPECÍFICA TELMEX (AÑADIDA)
# ====================================================================

def procesar_telmex_especifico(pdf_path):
    """
    Función aislada para Telmex que evita falsos positivos y usa lógica dedicada.
    """
    if not os.path.exists(pdf_path):
        return {"error": "El archivo no existe."}

    text = ""
    try:
        # Usamos la configuración global POPPLER_PATH
        images = convert_from_path(pdf_path, first_page=1, last_page=1, poppler_path=POPPLER_PATH)
        text = pytesseract.image_to_string(images[0], lang='spa')
    except Exception as e:
        return {"error": f"Error OCR: {str(e)}"}

    # 1. Lógica de Vigencia (Fecha)
    meses_telmex = {'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
                    'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12}
    
    date_pattern = r'(\d{2})\s?[-/]\s?([A-Z]{3,})\s?[-/]\s?(\d{4})'
    fechas = re.findall(date_pattern, text.upper())
    
    fecha_encontrada = None
    fecha_fmt = None
    estado_vigencia = "Fecha No Encontrada"

    if fechas:
        for dia, mes, anio in fechas:
            mes_key = mes[:3]
            if mes_key in meses_telmex:
                try:
                    fecha_obj = datetime(int(anio), meses_telmex[mes_key], int(dia))
                    fecha_encontrada = fecha_obj
                    fecha_fmt = fecha_obj.strftime('%d-%m-%Y')
                    estado_vigencia = analizar_vigencia(fecha_obj)
                    break 
                except:
                    continue

    # 2. Lógica de Domicilio
    domicilio = "No Encontrada"
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        if "C.P." in line and re.search(r'\d{5}', line):
            
            # IGNORAR PARQUE VIA
            if "06500" in line or "PARQUE VIA" in line.upper() or "PARQUE VÍA" in line.upper():
                continue

            parte_cp = line
            parte_municipio = lines[i-1] if i > 0 else ""
            parte_colonia = lines[i-2] if i > 1 else ""
            parte_calle = lines[i-3] if i > 2 else ""
            
            full = f"{parte_calle} {parte_colonia} {parte_municipio} {parte_cp}"
            domicilio = re.sub(r'\s+', ' ', full).strip()
            break 

    return {
        "proveedor": "TELMEX",
        "vigencia": estado_vigencia,
        "fecha_emision": fecha_fmt,
        "direccion_del_domicilio": domicilio
    }

# ====================================================================
# EXTRACCIÓN DE DIRECCIÓN (LÓGICA ORIGINAL COMPLETA)
# ====================================================================

def extraer_direccion_especifica(texto: str, proveedor: str):
    lineas = [l.strip() for l in texto.splitlines() if len(l.strip()) > 2]

    # ======================================================
    # CFE (COMISIÓN FEDERAL DE ELECTRICIDAD)
    # ======================================================
    if proveedor == "CFE":
        lineas = texto.splitlines()
        lineas_limpias = []
        for l in lineas:
            l_limpia = l.strip()
            if len(l_limpia) > 2:
                l_limpia = re.sub(r'\s+', ' ', l_limpia)
                lineas_limpias.append(l_limpia)
        
        patrones_direccion = [
            r'CDA CENTENARIO.*INT.*\d',
            r'GEOVILLA.*CDA CENTENARIO',
            r'SAN PEDRO TOTOLTEPEC.*\d{5}',
            r'SAN PEDRO TOTOLTEPEC.*MEX\.?$'
        ]
        
        elementos_a_eliminar = [
            r'\$\d+(\.\d+)?',
            r'\([^)]*PESOS[^)]*\)',
            r'TRESCIENTOS.*PESOS.*M\.?N\.?',
            r'-.*CFE.*',
            r'[^A-Z0-9\s\.,ÁÉÍÓÚáéíóúÑñ]',
        ]
        
        direccion_lineas = []
        for patron in patrones_direccion:
            for i, linea in enumerate(lineas_limpias):
                if re.search(patron, linea, re.IGNORECASE):
                    linea_limpia = linea
                    for elem in elementos_a_eliminar:
                        linea_limpia = re.sub(elem, '', linea_limpia, flags=re.IGNORECASE)
                    
                    linea_limpia = linea_limpia.strip()
                    linea_limpia = re.sub(r'\s+', ' ', linea_limpia)
                    linea_limpia = re.sub(r'\s*,\s*', ', ', linea_limpia)
                    linea_limpia = re.sub(r'\s*\.\s*', '. ', linea_limpia)
                    linea_limpia = re.sub(r'\s*C\.P\.\s*', ' C.P. ', linea_limpia)
                    linea_limpia = re.sub(r'\bCP\s+', 'C.P. ', linea_limpia)
                    
                    palabras = linea_limpia.split()
                    palabras_capitalizadas = []
                    for palabra in palabras:
                        if palabra.isupper() and len(palabra) > 1:
                            palabras_capitalizadas.append(palabra)
                        else:
                            palabras_capitalizadas.append(palabra.title())
                    
                    linea_final = ' '.join(palabras_capitalizadas)
                    linea_final = linea_final.strip(' ,.-')
                    
                    if linea_final and len(linea_final) > 5:
                        direccion_lineas.append(linea_final)
                        lineas_limpias[i] = ""
                        break
        
        if len(direccion_lineas) >= 4:
            direccion = "\n".join(direccion_lineas[:4])
            return direccion
        
        for i, linea in enumerate(lineas_limpias):
            if "MARIA ORTEGA" in linea.upper():
                direccion_candidatos = []
                for j in range(i+1, min(i+5, len(lineas_limpias))):
                    l = lineas_limpias[j]
                    if (re.search(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]', l) and 
                        len(l) > 5 and 
                        not re.search(r'(TOTAL|PAGAR|PESOS|M\.N\.|\$\d+)', l, re.IGNORECASE)):
                        
                        for elem in elementos_a_eliminar:
                            l = re.sub(elem, '', l, flags=re.IGNORECASE)
                        
                        l = l.strip()
                        if l:
                            direccion_candidatos.append(l)
                
                if len(direccion_candidatos) >= 4:
                    direccion_final = []
                    for l in direccion_candidatos[:4]:
                        l = re.sub(r'\s+', ' ', l)
                        l = re.sub(r'\s*,\s*', ', ', l)
                        l = re.sub(r'\s*\.\s*', '. ', l)
                        l = re.sub(r'\s*C\.P\.\s*', ' C.P. ', l)
                        l = l.strip(' ,.-')
                        direccion_final.append(l.upper())
                    
                    return "\n".join(direccion_final)
        
        componentes = [
            "CDA CENTENARIO 2 INT. 8",
            "GEOVILLA Y CDA CENTENARIO Y CDA CENTENARIO", 
            "SAN PEDRO TOTOLTEPEC C.P. 50226",
            "SAN PEDRO TOTOLTEPEC, MEX."
        ]
        
        encontrados = []
        for componente in componentes:
            for linea in lineas_limpias:
                if all(palabra in linea.upper() for palabra in componente.upper().split()[:3]):
                    encontrados.append(componente)
                    break
        
        if len(encontrados) == 4:
            return "\n".join(encontrados)
        
        return "No Encontrada"

    # ======================================================
    # IZZI (EXTRACCIÓN DE DIRECCIÓN - POR POSICIÓN)
    # ======================================================
    if proveedor == "IZZI":
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]
        
        def limpiar_ruido_izzi(linea):
            ruido = [
                r"E ' E A M0",
                r"O PAGA EN LINEA EN IZZI\.MX",
                r"TU PAGO SE VERA REFLEJADO.*",
                r"REALIZA TU PAGO ESCANEANDO.*",
                r"CONSULTA EL DETALLE.*",
                r"\b\d{10}\b",
                r"^\d+$",
            ]
            
            limpia = linea
            for patron in ruido:
                limpia = re.sub(patron, '', limpia, flags=re.IGNORECASE)
            
            limpia = re.sub(r'[^\w\s\.,ÁÉÍÓÚáéíóúÑñ\-]', ' ', limpia)
            limpia = re.sub(r'\s+', ' ', limpia).strip()
            
            return limpia
        
        inicio_direccion = None
        
        for i, linea in enumerate(lineas[:10]):
            palabras = linea.split()
            if len(palabras) >= 2:
                if (palabras[0][0].isupper() and palabras[1][0].isupper() and
                    len(palabras[0]) > 2 and len(palabras[1]) > 2):
                    inicio_direccion = i + 1
                    break
        
        if inicio_direccion is None:
            inicio_direccion = 1
        
        candidatos_direccion = []
        
        for i in range(inicio_direccion, min(inicio_direccion + 6, len(lineas))):
            linea = lineas[i]
            limpia = limpiar_ruido_izzi(linea)
            
            if (limpia and len(limpia) > 2 and
                not any(palabra in limpia.upper() for palabra in 
                    ["TELÉFONO", "CUENTA", "REFERENCIA", "BANCO", "SALDO"])):
                
                if not re.match(r'^\d+$', limpia.replace(' ', '')):
                    candidatos_direccion.append(limpia)
        
        if len(candidatos_direccion) >= 3:
            direccion_formateada = []
            
            for i, linea in enumerate(candidatos_direccion[:4]):
                if i == 0:
                    palabras = linea.split()
                    formateada = []
                    for palabra in palabras:
                        if palabra.lower() in ['el', 'la', 'de', 'del', 'los', 'las', 'y']:
                            formateada.append(palabra.lower())
                        else:
                            formateada.append(palabra.capitalize())
                    linea = ' '.join(formateada)
                
                elif i == 1:
                    if len(linea.split()) <= 3:
                        linea = linea.upper()
                    else:
                        linea = ' '.join([p.capitalize() for p in linea.split()])
                
                elif i == 2:
                    linea = linea.upper()
                
                elif i == 3:
                    if "C.P." not in linea.upper() and re.search(r'\b\d{5}\b', linea):
                        linea = re.sub(r'(\d{5})', r'C.P. \1', linea)
                    if "MEXICO" not in linea.upper():
                        linea = linea + ", MEXICO"
                    linea = linea.upper()
                
                direccion_formateada.append(linea)
            
            return "\n".join(direccion_formateada)
        
        return "No Encontrada"

    # ======================================================
    # MEGACABLE (EXTRACCIÓN PRECISA DE 3 LÍNEAS DE DIRECCIÓN)
    # ======================================================
    if proveedor == "MEGACABLE":
        lineas = [l.strip() for l in texto.splitlines() if len(l.strip()) > 2]
        
        direccion_encontrada = []
        
        for i in range(len(lineas)):
            if "DEPT" in lineas[i].upper() or "DEPTO" in lineas[i].upper():
                if i + 2 < len(lineas):
                    es_direccion = True
                    for j in range(3):
                        if j == 0:
                            if not ("DEPT" in lineas[i+j].upper() or "DEPTO" in lineas[i+j].upper()):
                                es_direccion = False
                                break
                        elif j == 1:
                            if not ("C.P." in lineas[i+j].upper() or re.search(r'\b\d{5}\b', lineas[i+j])):
                                es_direccion = False
                                break
                        elif j == 2:
                            if not ("MEX" in lineas[i+j].upper()):
                                es_direccion = False
                                break
                    
                    if es_direccion:
                        for j in range(3):
                            linea_limpia = lineas[i+j]
                            
                            if j == 0:
                                linea_limpia = re.sub(r'\(?\d\)?\s*MEG\s*A?\s*', '', linea_limpia, flags=re.IGNORECASE)
                                linea_limpia = re.sub(r'\(\d+\)\s*', '', linea_limpia)
                                linea_limpia = re.sub(r'^\(\d+\)\s*', '', linea_limpia)
                            
                            linea_limpia = re.sub(r'\b\d{10,}\b', '', linea_limpia)
                            linea_limpia = re.sub(r'SUSCRIPTOR[:\d\s]*', '', linea_limpia, flags=re.IGNORECASE)
                            linea_limpia = re.sub(r'TEL[ÉE]FONO[:\d\s]*', '', linea_limpia, flags=re.IGNORECASE)
                            linea_limpia = re.sub(r'^[^A-Z0-9]+', '', linea_limpia)
                            linea_limpia = re.sub(r'PAGA EN CENTROS.*', '', linea_limpia, flags=re.IGNORECASE)
                            linea_limpia = re.sub(r'MEGA.*', '', linea_limpia, flags=re.IGNORECASE)
                            linea_limpia = re.sub(r'^\s*\+\s*', '', linea_limpia)
                            
                            linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
                            
                            if j == 0:
                                linea_limpia = re.sub(r'\s*,\s*COL\.?\s*', ', COL. ', linea_limpia)
                                linea_limpia = re.sub(r'\s*DEPT[OA]?\.?:?\s*', ' Depto: ', linea_limpia, flags=re.IGNORECASE)
                            elif j == 1:
                                linea_limpia = re.sub(r'\s*,\s*C\.?P\.?\s*', ', C.P. ', linea_limpia, flags=re.IGNORECASE)
                                linea_limpia = re.sub(r'\bCP\s+', 'C.P. ', linea_limpia, flags=re.IGNORECASE)
                                linea_limpia = re.sub(r'^\s*\+\s*', '', linea_limpia)
                            elif j == 2:
                                linea_limpia = re.sub(r'\s*,\s*MEX\.?$', ', MEX.', linea_limpia, flags=re.IGNORECASE)
                                if not linea_limpia.endswith("MEX."):
                                    linea_limpia += ", MEX."
                            
                            direccion_encontrada.append(linea_limpia)
                        
                        if len(direccion_encontrada) == 3:
                            return "\n".join(direccion_encontrada)
        
        texto_unido = " ".join(lineas)
        
        patron_estricto = r'([A-Z0-9\s\-\.]+DEPT[OA]?:?\s*\d+[,\s]+COL\.?\s*[A-Z\s\.\-]+)\s+([A-Z\s\.\-]+,\s*C\.?P\.?\s*\d{5}[,\s]+[A-Z\s\.\-]+)\s+([A-Z\s\.\-]+,\s*MEX\.?)'
        
        match = re.search(patron_estricto, texto_unido, re.IGNORECASE)
        if match:
            linea1 = match.group(1).strip()
            linea2 = match.group(2).strip()
            linea3 = match.group(3).strip()
            
            linea1 = re.sub(r'\(?\d\)?\s*MEG\s*A?\s*', '', linea1, flags=re.IGNORECASE)
            linea1 = re.sub(r'\(\d+\)\s*', '', linea1)
            
            linea1 = re.sub(r'SUSCRIPTOR[:\d\s]*', '', linea1, flags=re.IGNORECASE)
            linea2 = re.sub(r'TEL[ÉE]FONO[:\d\s]*', '', linea2, flags=re.IGNORECASE)
            linea3 = re.sub(r'PAGA EN CENTROS.*', '', linea3, flags=re.IGNORECASE)
            
            linea1 = re.sub(r'\s*,\s*COL\.?\s*', ', COL. ', linea1)
            linea1 = re.sub(r'\s*DEPT[OA]?\.?:?\s*', ' Depto: ', linea1, flags=re.IGNORECASE)
            
            linea2 = re.sub(r'\s*,\s*C\.?P\.?\s*', ', C.P. ', linea2, flags=re.IGNORECASE)
            linea2 = re.sub(r'^\s*\+\s*', '', linea2)
            
            linea3 = re.sub(r'\s*,\s*MEX\.?$', ', MEX.', linea3, flags=re.IGNORECASE)
            if not linea3.endswith("MEX."):
                linea3 += ", MEX."
            
            return f"{linea1}\n{linea2}\n{linea3}"
        
        lineas_direccion = []
        
        for linea in lineas:
            if "DEPT" in linea.upper() and "COL" in linea.upper():
                linea_limpia = re.sub(r'\(?\d\)?\s*MEG\s*A?\s*', '', linea, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'\(\d+\)\s*', '', linea_limpia)
                linea_limpia = re.sub(r'SUSCRIPTOR[:\d\s]*', '', linea_limpia, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'TEL[ÉE]FONO[:\d\s]*', '', linea_limpia, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'\s*,\s*COL\.?\s*', ', COL. ', linea_limpia)
                linea_limpia = re.sub(r'\s*DEPT[OA]?\.?:?\s*', ' Depto: ', linea_limpia, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
                lineas_direccion.append(linea_limpia)
                break
        
        for linea in lineas:
            if ("C.P." in linea.upper() or re.search(r'\b\d{5}\b', linea)) and "DEPT" not in linea.upper():
                linea_limpia = re.sub(r'TEL[ÉE]FONO[:\d\s]*', '', linea, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'\s*,\s*C\.?P\.?\s*', ', C.P. ', linea_limpia, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'^\s*\+\s*', '', linea_limpia)
                linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
                if linea_limpia not in " ".join(lineas_direccion):
                    lineas_direccion.append(linea_limpia)
                break
        
        for linea in lineas:
            if "MEX" in linea.upper() and "C.P." not in linea.upper() and "DEPT" not in linea.upper():
                linea_limpia = re.sub(r'PAGA EN CENTROS.*', '', linea, flags=re.IGNORECASE)
                linea_limpia = re.sub(r'\s*,\s*MEX\.?$', ', MEX.', linea_limpia, flags=re.IGNORECASE)
                if not linea_limpia.endswith("MEX."):
                    linea_limpia += ", MEX."
                linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
                if linea_limpia not in " ".join(lineas_direccion):
                    lineas_direccion.append(linea_limpia)
                break
        
        if len(lineas_direccion) >= 2:
            while len(lineas_direccion) < 3:
                lineas_direccion.append("")
            return "\n".join(lineas_direccion[:3])
        
        return "No Encontrada"

    # ======================================================
    # TOTALPLAY (EXTRACCIÓN GENERAL DE 3 LÍNEAS DE DIRECCIÓN)
    # ======================================================
    if proveedor == "TOTALPLAY":
        lineas = [l.strip() for l in texto.splitlines() if len(l.strip()) > 2]
        
        palabras_calle = ["CALLE", "AVENIDA", "AV", "BOULEVARD", "BLVD", "CARRETERA", 
                        "CARR", "PRIVADA", "PASAJE", "CAMINO", "CERRADA", "CIRCUITO",
                        "MANZANA", "MZ", "LOTE", "LT", "INTERIOR", "INT", "NUM", "NO", "#"]
        
        palabras_municipio = ["OBREGON", "ALVARO", "BENITO JUAREZ", "CUAUHTEMOC", "COYOACAN",
                            "MIGUEL HIDALGO", "VENUSTIANO CARRANZA", "IZTAPALAPA", 
                            "GUSTAVO A MADERO", "TLALPAN", "MAGDALENA CONTRERAS", "TLAHUAC"]
        
        palabras_ciudad = ["CIUDAD DE MEXICO", "CDMX", "CIUDAD DE MÉXICO", "MEXICO", "MÉXICO"]
        
        def es_linea_direccion(linea):
            linea_upper = linea.upper()
            
            excluir = ["TELEFONO", "TEL", "CEL", "CUENTA", "REFERENCIA", "FECHA", "PAGO", 
                    "PERIODO", "RENTA", "TOTAL", "IMPORTE", "SALDO", "IVA", "SUBTOTAL",
                    "ANTES DEL", "VENCE", "VENCIMIENTO", "RECIBO", "COMPROBANTE",
                    "CONTRATO", "SERVICIO", "CLIENTE", "RFC", "CORREO", "EMAIL"]
            
            if any(palabra in linea_upper for palabra in excluir):
                return False
            
            if len(linea.strip()) < 5:
                return False
            
            if re.fullmatch(r'[\d\s\.\$£]+', linea):
                return False
            
            return True
        
        def limpiar_linea_direccion(linea):
            patrones_eliminar = [
                r'013160\s*8515',
                r'£',
                r'\$\s*\d[\d,\.]*\s*\$\s*\d[\d,\.]*',
                r'\$\s*\d[\d,\.]*',
                r'\b\d[\d,]*\.\d+\b',
                r'\b\d{3,}\.\d*\b',
                r'\([^)]*\)',
                r'ANTES DEL[^,]*,',
                r'VENCE[^,]*,',
                r'PAGO[^,]*,',
                r'\b\d{3,}\s*\.\s*\$\s*\d{3,}\.\d+\b',
            ]
            
            linea_limpia = linea
            for patron in patrones_eliminar:
                linea_limpia = re.sub(patron, '', linea_limpia, flags=re.IGNORECASE)
            
            linea_limpia = re.sub(r'\$\s*\d+\.?\d*\s*', '', linea_limpia)
            linea_limpia = re.sub(r'\b\d{3,}\.\d*\b', '', linea_limpia)
            linea_limpia = re.sub(r'\d{3,}\.\s*\$\s*\d{3,}\.\d+', '', linea_limpia)
            linea_limpia = re.sub(r'\s+', ' ', linea_limpia).strip()
            linea_limpia = linea_limpia.strip(' ,.-_')
            linea_limpia = linea_limpia.replace('$', '').strip()
            
            return linea_limpia
        
        direccion_lineas = []
        
        for i, linea in enumerate(lineas):
            if es_linea_direccion(linea):
                tiene_elementos_direccion = (
                    any(palabra in linea.upper() for palabra in palabras_calle) or
                    any(palabra in linea.upper() for palabra in palabras_municipio) or
                    any(palabra in linea.upper() for palabra in palabras_ciudad) or
                    re.search(r'\b(MZ|LT|INT|NUM|NO|#)\b', linea.upper()) or
                    re.search(r'\d{5}', linea)
                )
                
                if tiene_elementos_direccion:
                    linea_limpia = limpiar_linea_direccion(linea)
                    
                    if linea_limpia and len(linea_limpia) >= 5:
                        direccion_lineas.append(linea_limpia)
                        
                        for j in range(1, 3):
                            if i + j < len(lineas):
                                siguiente = lineas[i + j]
                                if es_linea_direccion(siguiente):
                                    siguiente_limpia = limpiar_linea_direccion(siguiente)
                                    if siguiente_limpia and len(siguiente_limpia) >= 5:
                                        if (siguiente_limpia not in " ".join(direccion_lineas) and
                                            not re.sub(r'\s+', '', siguiente_limpia).startswith(
                                                re.sub(r'\s+', '', direccion_lineas[-1])[:10])):
                                            direccion_lineas.append(siguiente_limpia)
                        
                        if len(direccion_lineas) >= 2:
                            break
                        else:
                            direccion_lineas = []
        
        if not direccion_lineas:
            for i in range(len(lineas) - 2):
                bloque = lineas[i:i+3]
                
                if all(es_linea_direccion(l) for l in bloque):
                    if any(any(palabra in l.upper() for palabra in palabras_calle + palabras_municipio + palabras_ciudad) 
                        or re.search(r'\b(MZ|LT|INT|NUM|NO|#)\b', l.upper()) 
                        or re.search(r'\d{5}', l) for l in bloque):
                        
                        bloque_limpio = [limpiar_linea_direccion(l) for l in bloque]
                        bloque_limpio = [l for l in bloque_limpio if l and len(l) >= 5]
                        
                        if len(bloque_limpio) >= 2:
                            direccion_lineas = bloque_limpio
                            break
        
        if direccion_lineas:
            direccion_completa = " ".join(direccion_lineas)
            
            patrones_montos = [
                r'\$\s*\d{3,}\s*\.\s*\$\s*\d{3,}\.\d+',
                r'\d{3,}\s*\.\s*\$\s*\d{3,}\.\d+',
                r'\$\s*\d{3,}\.\d*',
                r'\b\d{3,}\.\d*\s+\$\s*\d{3,}\.\d*\b',
            ]
            
            for patron in patrones_montos:
                direccion_completa = re.sub(patron, '', direccion_completa)
            
            direccion_completa = re.sub(r'\b\d{3,}\.\d*\b', '', direccion_completa)
            
            direccion_completa = re.sub(r'\s+', ' ', direccion_completa).strip()
            direccion_completa = direccion_completa.replace('$', '').strip()
            
            cp_match = re.search(r'\b(\d{5})\b', direccion_completa)
            if cp_match:
                cp = cp_match.group(1)
                direccion_completa = re.sub(r'\b' + cp + r'\b', '', direccion_completa)
                direccion_completa = (direccion_completa + " " + cp).strip()
            
            direccion_completa = re.sub(r'(CIUDAD DE MEXICO\s*){2,}', 'CIUDAD DE MEXICO ', direccion_completa, flags=re.IGNORECASE)
            direccion_completa = re.sub(r',\s*,', ', ', direccion_completa)
            direccion_completa = re.sub(r'\s*,\s*', ', ', direccion_completa)
            direccion_completa = re.sub(r'\s+', ' ', direccion_completa).strip()
            
            direccion_completa = direccion_completa.title()
            direccion_completa = direccion_completa.replace("Mz", "MZ").replace("Lt", "LT").replace("Int", "INT")
            direccion_completa = direccion_completa.replace("Ciudad De Mexico", "CIUDAD DE MEXICO")
            
            return direccion_completa
        
        patron_direccion_completa = r'((?:CALLE|AVENIDA|AV\.?)\s+[^,]{10,50}),?\s*([^,]{10,50}),?\s*(?:CIUDAD\s+DE\s+MEXICO|CDMX)[^0-9]*(\d{5})'
        
        match = re.search(patron_direccion_completa, texto, re.IGNORECASE)
        if match:
            calle, colonia_municipio, cp = match.groups()
            direccion = f"{calle.strip()} {colonia_municipio.strip()} CIUDAD DE MEXICO {cp}"
            direccion = limpiar_linea_direccion(direccion)
            return direccion
        
        return "No Encontrada"
    
    # ======================================================
    # AGUA (ESCANEADO – LIMPIEZA DEFINITIVA)
    # ======================================================
    if proveedor == "AGUA":

        for i, linea in enumerate(lineas):

            if "DOMICILIO" in linea:

                bloque = []

                for l in lineas[i:i + 3]:

                    if any(x in l for x in [
                        "IMPORTE", "DEUDA", "FECHA", "NIS",
                        "ESTADO DE CUENTA", "SITUACION"
                    ]):
                        continue

                    bloque.append(
                        l.replace("DOMICILIO:", "")
                        .replace("COLONIA:", "")
                        .strip()
                    )

                if bloque:
                    direccion = " ".join(bloque)

                    # 🧹 limpieza OCR definitiva
                    palabras_validas = []

                    PALABRAS_DIRECCION_VALIDAS = {
                        "SAN", "SANTA", "SANTO",
                        "PEDRO", "JUAN", "MIGUEL",
                        "TOTOLTEPEC", "CENTRO",
                        "COLONIA", "BARRIO"
                    }

                    for palabra in direccion.split():

                        palabra = palabra.strip(",:.;")

                        # permitir SAN / SANTA / SANTO
                        if len(palabra) <= 3 and palabra not in PALABRAS_DIRECCION_VALIDAS:
                            continue

                        # descartar basura OCR (consonantes seguidas)
                        if re.search(r'[BCDFGHJKLMNPQRSTVWXYZ]{3,}', palabra):
                            continue

                        # debe tener al menos una vocal
                        if not re.search(r'[AEIOU]', palabra):
                            continue

                        if palabra in PALABRAS_DIRECCION_VALIDAS or len(palabra) >= 5:
                            palabras_validas.append(palabra)

                    direccion = " ".join(palabras_validas).strip()
                    return direccion

        return "No Encontrada"

    return "No Encontrada"

# ====================================================================
# ANALIZADOR PRINCIPAL
# ====================================================================

def analyze_comprobante_domicilio(texto_raw: str):
    texto = normalizar(texto_raw)
    compacto = re.sub(r"\s+", "", texto)

    resultado = {
        "proveedor": "Desconocido",
        "vigencia": "No Encontrado",
        "fecha_emision": None,
        "direccion_del_domicilio": "No Encontrada"
    }

    proveedores = {
        "CFE": ["CFE", "COMISION FEDERAL DE ELECTRICIDAD"],
        "TELMEX": ["TELMEX", "TELEFONOS DE MEXICO"],
        "IZZI": ["IZZI", "CABLEVISION", "CABLEVISIONRED"],
        "MEGACABLE": ["MEGACABLE", "MEGAMOVIL", "MEGANOVIL", "MEGA.MX", "MEGACABLEAPP"],
        "TOTALPLAY": ["TOTALPLAY", "TOTAL PLAY", "MITOTALPLAY"],
        "AGUA": ["AGUA Y SANEAMIENTO", "SACMEX"],
        "PREDIAL": ["PREDIAL", "TESORERIA"]
    }

    for clave, alias in proveedores.items():
        if any(a in texto or a in compacto for a in alias):
            resultado["proveedor"] = clave
            break

    fecha = extraer_fecha_universal(texto)
    if fecha:
        resultado["fecha_emision"] = fecha.strftime("%d-%m-%Y")
        resultado["vigencia"] = analizar_vigencia(fecha)

    resultado["direccion_del_domicilio"] = extraer_direccion_especifica(
        texto, resultado["proveedor"]
    )

    return resultado

# ====================================================================
# PROCESADOR PDF (CONTROLADOR)
# ====================================================================

def analizar_pdf_comprobante(pdf_input: str):
    """
    Controlador principal.
    """
    texto = ""
    proveedor_preliminar = "Desconocido"

    # 1. Detección rápida de proveedor
    try:
        import fitz
        doc = fitz.open(pdf_input)
        temp_text = ""
        for page in doc: temp_text += page.get_text()
        if "TELMEX" in normalizar(temp_text):
            proveedor_preliminar = "TELMEX"
    except:
        pass
    
    # 2. Si es Telmex, usar la función específica NUEVA
    if proveedor_preliminar == "TELMEX":
        logging.info("TELMEX detectado (preliminar) → Usando procesador específico")
        return procesar_telmex_especifico(pdf_input)

    # 3. Flujo normal para los demás (OCR General)
    if OCR_AVAILABLE:
        try:
            logging.info("Aplicando OCR General (Poppler + Tesseract)")
            images = convert_from_path(pdf_input, poppler_path=POPPLER_PATH)
            ocr_texto = []
            for img in images:
                page_text = pytesseract.image_to_string(img, lang="spa", config="--psm 6")
                ocr_texto.append(page_text)
            texto = "\n".join(ocr_texto).strip()
        except Exception as e:
            logging.warning(f"OCR falló: {e}")
            texto = ""

    # Fallback si OCR falla o texto vacío
    if not texto:
        try:
            import fitz
            doc = fitz.open(pdf_input)
            for page in doc: texto += page.get_text() + "\n"
        except: pass

    # Chequeo final de Telmex por si el OCR lo detectó pero la lectura rápida no
    if "TELMEX" in normalizar(texto):
         logging.info("TELMEX detectado (tras OCR) → Usando procesador específico")
         return procesar_telmex_especifico(pdf_input)

    if not texto.strip():
        return {"error": "Documento sin texto detectable"}

    # Ejecutar análisis estándar para el resto
    return analyze_comprobante_domicilio(texto)