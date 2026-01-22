import os
import re
import logging
from datetime import datetime, date
import shutil
import sys
from typing import Dict, Any, Optional
from flask import Flask
from bson.objectid import ObjectId
from calendar import monthrange
from config.db import db

# ====================================================================
# CONFIGURACIÓN DE OCR BASADA EN ARCHIVOS DE SU PROYECTO
# ====================================================================
fitz = None
pytesseract = None
convert_from_bytes = None
OCR_AVAILABLE = False

# Ruta fija para Poppler (evita depender del PATH del sistema)
POPPLER_PATH = r"C:\poppler\Library\bin"

try:
    import fitz
    from services.ai_engine.text_extractor import extract_text_from_pdf
    from pdf2image import convert_from_bytes
    import pytesseract
    from PIL import Image
    print("✅ Librerías de OCR/Texto cargadas correctamente.")
    print("SISTEMA DETECTADO:", "Windows" if sys.platform.startswith('win') else "Linux/Unix")
    # --- LÓGICA DE DETECCIÓN DE SISTEMA ---
    if sys.platform.startswith('win'):
        # CONFIGURACIÓN PARA WINDOWS (Tu entorno local)
        POPPLER_PATH = r"C:\poppler\Library\bin"
        
        TESSERACT_DIR = r'C:\Program Files\Tesseract-OCR'
        tesseract_exe = os.path.join(TESSERACT_DIR, 'tesseract.exe')
        
        if os.path.exists(tesseract_exe):
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe
            os.environ['TESSDATA_PREFIX'] = os.path.join(TESSERACT_DIR, 'tessdata')
    else:
        # CONFIGURACIÓN PARA LINUX (IONOS / Ubuntu)
        # En Linux, si instalaste con apt, no se necesita ruta para Poppler.
        POPPLER_PATH = None 
        
        # Verificar si tesseract está instalado en el sistema
        if shutil.which("tesseract"):
            # En Linux no se define tesseract_cmd si está en el PATH
            pass 
        else:
            # Fallback por si acaso está en una ruta no estándar
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

    OCR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Una o más dependencias de OCR/Texto no encontradas: {e}. El análisis de INE no funcionará.")
except Exception as e:
    logging.error(f"Error al configurar Tesseract: {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ====================================================================
# CONSTANTES Y REGEX
# ====================================================================

# 💡 REGEX para buscar candidatos a CURP (Flexible para errores de OCR)
FLEX_CURP_REGEX = re.compile(r"[A-Z0-9]{4}[0-9A-Z]{6}[A-Z0-9]{6}[0-9A-Z]{2}", re.IGNORECASE)

# REGEX Estricta para la validación final de la CURP
CURP_REGEX = re.compile(r"[A-Z]{4}[0-9]{6}[HMOE][A-Z]{5}[0-9A-Z]{2}", re.IGNORECASE)

# REGEX para buscar la Vigencia
VIGENCIA_REGEX = re.compile(r'(?:VIGENCIA|VENCE|FECHA\s+DE\s+EXPIRACION)\s*[:\s-]*\s*(\d{4}|\d{1,2}[/-]\d{4})', re.IGNORECASE)

# 💡 NUEVA REGEX para Domicilio
DOMICILIO_REGEX = re.compile(
    r'DOMICILIO\s*([\s\S]*?)\s*(?:CLAVE DE ELECTOR|CURP|FECHA DE NACIMIENTO|SECCIÓN|VIGENCIA|SEXO|NOMBRE|AÑO DE REGISTRO|\n\s*\n)',
    re.IGNORECASE | re.MULTILINE
)

# ====================================================================
# LÓGICA DE LIMPIEZA Y PARSEO
# ====================================================================

def clean_curp_candidate(curp_candidate: str) -> str:
    cleaned = curp_candidate.upper()

    if len(cleaned) != 18:
        return cleaned

    date_part = cleaned[4:10]
    date_part = date_part.replace('O', '0').replace('I', '1').replace('S', '5').replace('B', '8').replace('Z', '2')
    cleaned = cleaned[:4] + date_part + cleaned[10:]

    homoclave_part = cleaned[-2:]
    homoclave_part = homoclave_part.replace('O', '0').replace('I', '1')
    homoclave_part = homoclave_part.replace('S', '8')
    homoclave_part = homoclave_part.replace('B', '8').replace('Z', '2')

    cleaned = cleaned[:-2] + homoclave_part

    return cleaned


def extract_ine_text(file_path: str) -> str:

    if not OCR_AVAILABLE:
        logging.error("Las librerías de OCR/Texto no están disponibles para el análisis.")
        return ""
        
    file_extension = os.path.splitext(file_path)[1].lower()
    texto_completo = ""

    # 1. Extracción directa con PyMuPDF
    if file_extension == '.pdf':
        try:
            texto_completo = extract_text_from_pdf(file_path)
            if texto_completo.strip():
                logging.info(f"Extracción directa de texto PDF exitosa: {os.path.basename(file_path)}")
                return texto_completo.strip()
        except Exception as e:
            logging.warning(f"Falló la extracción directa de PDF: {e}. Recurriendo a OCR.")

    # 2. Recurso a OCR
    try:
        images = []

        if file_extension == '.pdf':
            pdf_bytes = open(file_path, 'rb').read()

            # 👇 AQUI SE ARREGLA EL ERROR: se especifica Poppler
            images = convert_from_bytes(
                pdf_bytes,
                poppler_path=POPPLER_PATH
            )

        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff']:
            images = [Image.open(file_path)]
        
        for i, img in enumerate(images):
            texto_pagina = pytesseract.image_to_string(img, lang="spa")
            texto_completo += texto_pagina + f"\n\n--- FIN DE PÁGINA {i+1} (OCR) ---\n\n"
        
        if texto_completo.strip():
            logging.info(f"Extracción por OCR exitosa para {os.path.basename(file_path)}")

    except Exception as e:
        logging.error(f"Error fatal durante el OCR de {os.path.basename(file_path)}: {e}")
        texto_completo = ""

    return texto_completo.strip()


def parse_ine_data(full_text: str) -> Dict[str, Any]:

    resultados = {
        "curp_extraida": None,
        "fecha_vigencia": None,
        "es_vigente": False,
        "estado_curp": "No encontrada",
        "domicilio_extraido": None
    }
    
    best_curp = None
    
    for curp_match in FLEX_CURP_REGEX.finditer(full_text):
        candidate = curp_match.group(0).upper()
        cleaned_candidate = clean_curp_candidate(candidate)
        
        if CURP_REGEX.fullmatch(cleaned_candidate):
            best_curp = cleaned_candidate
            logging.info(f"CURP limpia validada: {best_curp} (Original: {candidate})")
            break
            
    if best_curp:
        resultados["curp_extraida"] = best_curp
        resultados["estado_curp"] = "Válida"

    vigencia_match = VIGENCIA_REGEX.search(full_text)
    fecha_vigencia_obj = None
    
    if vigencia_match:
        fecha_str = vigencia_match.group(1).replace('-', '/')
        
        for fmt in ['%Y', '%m/%Y']:
            try:
                if len(fecha_str) == 4:
                    fecha_vigencia_obj = datetime.strptime(fecha_str, '%Y').replace(month=12, day=31).date()
                else:
                    dt = datetime.strptime(fecha_str, fmt)
                    last_day = monthrange(dt.year, dt.month)[1]
                    fecha_vigencia_obj = dt.replace(day=last_day).date()
                if fecha_vigencia_obj:
                    break
            except:
                continue

    if fecha_vigencia_obj:
        resultados["fecha_vigencia"] = fecha_vigencia_obj.strftime("%Y-%m-%d")
        resultados["es_vigente"] = fecha_vigencia_obj > date.today()

    domicilio_match = DOMICILIO_REGEX.search(full_text)
    if domicilio_match:
        domicilio_raw = domicilio_match.group(1).strip()
        domicilio_limpio = re.sub(r'\s+', ' ', domicilio_raw)
        resultados["domicilio_extraido"] = domicilio_limpio

    return resultados


# ====================================================================
# FUNCIÓN PRINCIPAL DE ANÁLISIS EN SEGUNDO PLANO
# ====================================================================

def analyze_ine_document(app: Flask, usuario_id: str, ine_archivos: Dict[str, str]):
    
    if not OCR_AVAILABLE:
        app.logger.error("No se puede ejecutar analyze_ine_document: Faltan dependencias OCR.")
        return

    with app.app_context():
        
        user_obj_id = ObjectId(usuario_id)
        resultados_analisis = {}
        
        for campo, ruta_completa in ine_archivos.items():
            
            full_text = extract_ine_text(ruta_completa)
            
            if not full_text:
                app.logger.warning(f"No se pudo extraer texto del INE: {os.path.basename(ruta_completa)}")
                continue

            datos_analizados = parse_ine_data(full_text)
            
            resultados_analisis[campo] = {
                "curp_extraida": datos_analizados["curp_extraida"],
                "estado_curp": datos_analizados["estado_curp"],
                "es_vigente": datos_analizados["es_vigente"],
                "fecha_vigencia": datos_analizados["fecha_vigencia"],
                "domicilio_extraido": datos_analizados["domicilio_extraido"],
                "fecha_analisis": datetime.utcnow()
            }
        
        if "ine_fisica" in ine_archivos:
            collection = db.documentofisica
        elif "ine_moral" in ine_archivos:
            collection = db.documentomoral
        else:
            app.logger.error("No se pudo determinar la colección para guardar el análisis del INE.")
            return

        update_doc_fields = {}

        for campo_ine, resultado in resultados_analisis.items():
            update_doc_fields[f"documentos.{campo_ine}.analisis_ine"] = resultado
            
            if resultado.get("estado_curp") == "Válida":
                update_doc_fields["curp_extraida"] = resultado.get("curp_extraida")

            if resultado.get("domicilio_extraido"):
                update_doc_fields["domicilio_extraido"] = resultado.get("domicilio_extraido")
                
        try:
            collection.update_one(
                {"usuario_id": user_obj_id},
                {"$set": update_doc_fields}
            )
            app.logger.info(f"✅ Resultados de análisis guardados para {usuario_id}.")
        except Exception as e:
            app.logger.error(f"Error al guardar análisis de INE: {e}")
