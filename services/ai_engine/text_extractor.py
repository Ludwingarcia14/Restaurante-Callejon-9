import fitz  # PyMuPDF
import logging
import sys
import os
import shutil

# Librerías para OCR
try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    logging.warning("⚠️ Librerías de OCR (pytesseract/pdf2image) no instaladas. El modo OCR fallará.")

# ==================== CONFIGURACIÓN DE RUTAS (WINDOWS/LINUX) ====================

# Ajusta estas rutas si instalaste Poppler o Tesseract en carpetas diferentes
POPPLER_PATH = None

if sys.platform.startswith('win'):
    # === RUTAS PARA WINDOWS ===
    # 1. Ruta de Poppler (bin) - NECESARIA para pdf2image
    POPPLER_PATH = r"C:\poppler\Library\bin"  # <--- VERIFICA ESTA RUTA EN TU PC
    
    # 2. Ruta de Tesseract
    TESSERACT_DIR = r'C:\Program Files\Tesseract-OCR'
    tesseract_exe = os.path.join(TESSERACT_DIR, 'tesseract.exe')
    
    if os.path.exists(tesseract_exe):
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe
        # Configurar variable de entorno para datos de entrenamiento si es necesario
        os.environ['TESSDATA_PREFIX'] = os.path.join(TESSERACT_DIR, 'tessdata')
    else:
        logging.warning(f"⚠️ No se encontró Tesseract en: {tesseract_exe}")

else:
    # === CONFIGURACIÓN LINUX (Producción) ===
    # En Linux usualmente están en el PATH global
    if not shutil.which("tesseract"):
        # Fallback común en servidores
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# ==================== FUNCIONES DE EXTRACCIÓN ====================

def extract_text_from_pdf(file_path):
    """
    Extracción rápida usando metadatos del PDF (sin OCR).
    """
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        logging.error(f"Error en extracción nativa (PyMuPDF): {e}")
        return ""

def extract_text_with_ocr(file_path):
    """
    Extracción forzosa convirtiendo PDF a Imágenes -> Texto (OCR).
    Uso: Documentos escaneados o imágenes.
    """
    text = ""
    try:
        logging.info(f"📸 Iniciando conversión PDF a Imagen para: {file_path}")
        
        # 1. Convertir PDF a lista de imágenes
        # dpi=300 es el estándar para buena lectura de OCR
        images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)

        # 2. Procesar cada imagen con Tesseract
        logging.info(f"🔍 Ejecutando Tesseract en {len(images)} páginas...")
        
        for i, image in enumerate(images):
            # lang='spa' es crucial para bancos en español
            page_text = pytesseract.image_to_string(image, lang='spa')
            text += f"\n--- OCR PÁGINA {i + 1} ---\n{page_text}"
            
        return text.strip()

    except Exception as e:
        error_msg = f"❌ Error fatal en OCR: {str(e)}"
        logging.error(error_msg)
        # Devolvemos el error como texto para que quede en el log txt
        return error_msg