from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import logging
import unicodedata

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mapeo de meses (sin acentos para compatibilidad)
MESES = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
    "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def parse_fecha_textual(fecha_str):
    """Convierte una fecha textual como '05 DE MAYO DE 2025' → datetime.date."""
    # Limpia saltos de línea y múltiples espacios antes de parsear
    fecha_str = re.sub(r'\s+', ' ', fecha_str).strip()
    
    # Busca el patrón DD DE MES DE YYYY
    match = re.search(r'(\d{1,2})\s+DE\s+([A-ZÁÉÍÓÚ]+)\s+DE\s+(\d{4})', fecha_str, re.IGNORECASE)
    if match:
        try:
            dia = int(match.group(1))
            mes_str = match.group(2).upper()
            
            # Quitar acentos para la búsqueda
            mes_str = ''.join(c for c in mes_str if unicodedata.category(c) != 'Mn')
            
            mes = MESES.get(mes_str)
            anio = int(match.group(3))
            if mes:
                return datetime(anio, mes, dia).date()
        except Exception as e:
            logging.error(f"Error al parsear la fecha textual '{fecha_str}': {e}")
    return None

def analizar_vigencia(fecha_emision):
    """
    Determina si la fecha de emisión no es futura y no es mayor a 3 meses de antigüedad.
    """
    if not fecha_emision:
        return False
    
    hoy = datetime.now().date()
    
    # 1. Validar que la fecha no sea futura
    if fecha_emision > hoy:
        logging.warning(f"Fecha futura detectada: {fecha_emision}. Se marca como No Vigente.")
        return False

    # 2. Validar que no sea mayor a 3 meses (vigente si es igual o posterior al límite)
    fecha_limite = hoy - relativedelta(months=3)
    logging.info(f"Fecha emisión: {fecha_emision}, Fecha límite: {fecha_limite}")
    return fecha_emision >= fecha_limite

def analyze_pdf_text(pdf_text: str):
    result = {
        "vigente": None,
        "fecha_emision": None,
        "rfc": None, # ✅ NUEVO CAMPO: RFC extraído
        "giro": None,
        "actividades_economicas": [],
        "regimen_fiscal": None,
        "regimenes_fiscales": [] 
    }
    
    # --- 1️⃣ Extracción y análisis de la fecha de emisión ---
    fecha_pattern = r'Lugar y Fecha de Emisión\s*.*?A\s*(\d{1,2}\s+DE\s+[A-ZÁÉÍÓÚ]+\s+DE\s+\d{4})'
    fecha_match = re.search(fecha_pattern, pdf_text, re.IGNORECASE | re.DOTALL)

    if fecha_match:
        fecha_str_extraida = fecha_match.group(1).strip()
        result["fecha_emision"] = fecha_str_extraida.replace('\n', ' ')
        
        fecha_dt = parse_fecha_textual(fecha_str_extraida)
        
        if fecha_dt:
            es_vigente = analizar_vigencia(fecha_dt)
            result["vigente"] = "Vigente" if es_vigente else "No Vigente" 
            logging.info(f"Fecha extraída: {fecha_dt}, Vigencia: {result['vigente']}")
        else:
            logging.warning(f"No se pudo parsear la fecha: {fecha_str_extraida}")
    else:
        logging.warning("No se encontró el patrón de fecha de emisión.")


    # --- 2️⃣ Extracción del RFC (NUEVO) ---
    # Busca 'RFC:' seguido de 3-4 letras, 6 dígitos y 3 alfanuméricos. 
    # Soporta espacios intermedios que a veces genera el OCR.
    rfc_pattern = r'RFC\s*:?\s*([A-Z&Ñ]{3,4}\s*\d{6}\s*[A-Z0-9]{3})'
    rfc_match = re.search(rfc_pattern, pdf_text, re.IGNORECASE)
    
    if rfc_match:
        # Limpiar espacios internos y convertir a mayúsculas
        rfc_clean = rfc_match.group(1).replace(" ", "").upper()
        result["rfc"] = rfc_clean
        logging.info(f"RFC extraído: {result['rfc']}")
    else:
        logging.warning("No se encontró el patrón de RFC.")


    # --- 3️⃣ Extracción de regímenes fiscales (Múltiples) ---
    regimen_block_match = re.search(r'Regímenes:(.*?)(?=Obligaciones:|$)', pdf_text, re.IGNORECASE | re.DOTALL)
    
    if regimen_block_match:
        regimen_block = regimen_block_match.group(1)
        
        # Patrón para capturar el nombre del régimen (cualquier texto) antes de la primera fecha.
        # Esto captura CADA régimen en la tabla.
        regimen_matches = re.findall(
            r'^\s*([^\n\r]+?)\s+\d{2}/\d{2}/\d{4}', 
            regimen_block, 
            re.MULTILINE | re.IGNORECASE
        )
        
        if regimen_matches:
            # 1. Llenar la lista con todos los regímenes (limpios)
            lista_regimenes = [r.strip() for r in regimen_matches if r.strip()]
            result["regimenes_fiscales"] = lista_regimenes 
            
            # 2. Determinar el régimen principal para el campo 'regimen_fiscal' (singular)
            principal_regimen = next(
                (r for r in lista_regimenes if 'Actividades Empresariales' in r),
                lista_regimenes[0]
            )
            result["regimen_fiscal"] = principal_regimen
            logging.info(f"Regímenes encontrados: {result['regimenes_fiscales']}")
        else:
            logging.warning("No se encontraron regímenes fiscales en el bloque.")
    

    # --- 4️⃣ Extracción de Actividades Económicas (Giro) ---
    actividades_block_match = re.search(r'Actividades Económicas:(.*?)(?=Regímenes:|$)', pdf_text, re.IGNORECASE | re.DOTALL)
    
    if actividades_block_match:
        actividades_block = actividades_block_match.group(1)
        
        patron_fila_actividad = re.compile(
            r'^\s*(?:\d{1,2}|Remanente.+?Renta)\s*(.*?)\s+\d{1,3}(?:\.\d+)?\s*\d{2}/\d{2}/\d{4}', 
            re.MULTILINE | re.IGNORECASE | re.DOTALL 
        )

        actividades_matches = patron_fila_actividad.findall(actividades_block)

        # Limpieza y asignación
        lista_actividades = [re.sub(r'\s+', ' ', act).strip() for act in actividades_matches if act.strip()]
        
        result["actividades_economicas"] = lista_actividades
        
        if lista_actividades:
            result["giro"] = lista_actividades[0]
            logging.info(f"Actividades extraídas (Giro): {result['giro']}")
        else:
            logging.warning("No se encontraron actividades económicas con el patrón de tabla.")
            
    return result