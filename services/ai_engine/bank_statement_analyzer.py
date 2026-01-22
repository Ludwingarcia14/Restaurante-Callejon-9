import os
import re
import logging
import pdfplumber
import unicodedata
import matplotlib

# Importamos tu extractor con OCR
from services.ai_engine.text_extractor import extract_text_with_ocr

# ==================== INTEGRACIÓN DE TODOS TUS PARSERS ====================
try:
    from services.ai_engine.parsers import (
        heybanco, HSBC, afirme, banamex, banbajio, 
        BancoAzteca, bancoppel, banorte, BX,
        scotiabank, inbursa, KapitalBank, mercadopago, Mifel, Monex
    )
    logging.info("✅ Parsers específicos cargados correctamente.")
except ImportError as e:
    logging.warning(f"⚠️ Error cargando parsers: {e}")
    heybanco = HSBC = afirme = banamex = banbajio = BancoAzteca = bancoppel = banorte = BX = None
    scotiabank = inbursa = KapitalBank = mercadopago = Mifel = Monex = None

# ==================== CONFIGURACIÓN ====================

matplotlib.use('Agg')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==================== CATÁLOGO DE BANCOS ====================
BANCOS_CATALOGO = {
    "AFIRME":       {"clabe": "062", "keywords": ["AFIRME", "BANCA AFIRME"]},
    "BBVA":         {"clabe": "012", "keywords": ["BBVA", "BANCOMER"]},
    "SANTANDER":    {"clabe": "014", "keywords": ["SANTANDER"]},
    "BANAMEX":      {"clabe": "002", "keywords": ["BANAMEX", "CITIBANAMEX", "CITI"]},
    "BANORTE":      {"clabe": "072", "keywords": ["BANORTE", "BANCO MERCANTIL DEL NORTE"]},
    "HSBC":         {"clabe": "021", "keywords": ["HSBC"]},
    "SCOTIABANK":   {"clabe": "044", "keywords": ["SCOTIABANK", "INVERLAT"]},
    "INBURSA":      {"clabe": "036", "keywords": ["INBURSA", "GRUPO FINANCIERO INBURSA"]},
    "BANREGIO":     {"clabe": "058", "keywords": ["BANREGIO"]},
    "BANBAJIO":     {"clabe": "030", "keywords": ["BAJIO", "BANBAJIO"]},
    "AZTECA":       {"clabe": "127", "keywords": ["AZTECA", "BANCO AZTECA"]},
    "MIFEL":        {"clabe": "042", "keywords": ["MIFEL", "BANCA MIFEL"]},
    "MONEX":        {"clabe": "052", "keywords": ["MONEX", "MONEX GRUPO FINANCIERO"]},
    "BANCOPPEL":    {"clabe": "137", "keywords": ["BANCOPPEL", "COPPEL"]},
    "BX_PLUS":      {"clabe": "113", "keywords": ["BX+", "VE POR MAS", "VE POR MÁS"]},
    "HEYBANCO":     {"clabe": "000", "keywords": ["HEY BANCO", "HEYBANCO"]}, 
    "KAPITAL_BANK": {"clabe": "000", "keywords": ["KAPITAL", "KAPITAL BANK"]},
    "MERCADO_PAGO": {"clabe": "000", "keywords": ["MERCADO PAGO", "MERCADOPAGO"]},
    "NU_MEXICO":    {"clabe": "638", "keywords": ["NU MEXICO", "NU BN SERVICIOS"]},
    "STP":          {"clabe": "646", "keywords": ["SISTEMA DE TRANSFERENCIAS", "STP"]}
}

# ==================== UTILIDADES ====================

def clean_text(text):
    if not text: return ""
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'\s+', ' ', text.replace('\xa0', ' '))
    return text.strip()

# ==================== DETECCIÓN INTELIGENTE (MEJORADA) ====================

def detectar_banco(ocr_full_text, native_full_text, file_path=None):
    ocr_header = ocr_full_text[:3000].upper() if ocr_full_text else "" 
    full_body = (native_full_text + " " + ocr_full_text).upper() 
    
    # ---------------------------------------------------------
    # 1. DETECCIÓN POR NOMBRE DE ARCHIVO (PRIORIDAD ALTA)
    # ---------------------------------------------------------
    if file_path:
        filename = os.path.basename(file_path).upper()
        # Ignorar extensiones y IDs generados (ej: bec9c4ce..._BANORTE.pdf)
        for nombre, datos in BANCOS_CATALOGO.items():
            for kw in datos["keywords"]:
                # Buscamos la keyword como palabra completa o parte significativa
                if kw in filename:
                    logging.info(f"📁 Banco detectado por NOMBRE DE ARCHIVO: {nombre}")
                    return nombre

    # ---------------------------------------------------------
    # 2. DETECCIÓN POR CLABE (PRIORIDAD EXACTA)
    # ---------------------------------------------------------
    text_nums_only = re.sub(r'\D', '', full_body)
    # Busca 18 dígitos donde el primero no sea 0 (a veces pasa) o estándar
    match_clabe = re.search(r'(\d{3})\d{15}', text_nums_only)
    
    if match_clabe:
        prefijo = match_clabe.group(1)
        for nombre, datos in BANCOS_CATALOGO.items():
            if datos["clabe"] == prefijo:
                logging.info(f"🔢 Banco detectado por CLABE ({prefijo}): {nombre}")
                return nombre

    # ---------------------------------------------------------
    # 3. DETECCIÓN POR POSICIÓN EN TEXTO (COMPETENCIA)
    # ---------------------------------------------------------
    logging.info("🔎 Analizando posiciones de logos en texto OCR...")
    
    candidatos = [] # Lista de tuplas (indice_aparicion, nombre_banco)

    for nombre, datos in BANCOS_CATALOGO.items():
        for kw in datos["keywords"]:
            # Buscamos la posición donde aparece la palabra clave
            idx = ocr_header.find(kw)
            if idx != -1:
                # Guardamos qué banco es y en qué caracter apareció (mientras más cerca del 0, mejor)
                candidatos.append((idx, nombre))

    if candidatos:
        # Ordenamos por índice: el que aparece PRIMERO en el documento gana
        candidatos.sort(key=lambda x: x[0])
        ganador = candidatos[0][1]
        logging.info(f"🏆 Banco ganador por posición (Logo/Header): {ganador} (Aparece en char {candidatos[0][0]})")
        return ganador

    return "DESCONOCIDO"

# ==================== ADAPTADOR DE SALIDAS ====================

def normalizar_salida_especifica(resultado, nombre_banco, log_path):
    try:
        if "error" in resultado:
             return {"status": "error", "message": resultado["error"], "log_path": log_path}

        ingresos = (
            resultado.get('ingresos_netos') or 
            resultado.get('ingresos_reales') or 
            resultado.get('ingresos') or 
            resultado.get('total_abonos_resumen') or 
            0.0
        )

        saldo = resultado.get('saldo_promedio', 0.0)
        if saldo == 0.0 and ('saldo_inicial' in resultado or 'saldo_final' in resultado):
            s_ini = resultado.get('saldo_inicial', 0.0) or 0.0
            s_fin = resultado.get('saldo_final', 0.0) or resultado.get('saldo_final_detectado', s_ini)
            saldo = (s_ini + s_fin) / 2

        tpv = resultado.get('tpv', 0.0)
        log_trans = resultado.get('log_transacciones') or resultado.get('log') or []

        evaluacion = "Perfil débil"
        if ingresos > 50000: evaluacion = "Perfil medio"
        if ingresos > 100000 and saldo > 20000: evaluacion = "Perfil sólido"

        return {
            "status": "success",
            "banco": nombre_banco,
            "periodo_valido": True,
            "ingresos_reales": float(ingresos),
            "ingresos_tpv": float(tpv),
            "saldo_promedio": float(saldo),
            "evaluacion_express": evaluacion,
            "movimientos_detectados": len(log_trans),
            "log_path": log_path,
            "origen": "PARSER_ESPECIFICO"
        }
    except Exception as e:
        logging.error(f"Error normalizando salida: {e}")
        return {"status": "error", "message": str(e), "log_path": log_path}

# ==================== WRAPPER ====================

def ejecutar_parser(func, pdf_path, cliente=""):
    try:
        return func(pdf_path, cliente)
    except TypeError:
        return func(pdf_path)

# ==================== ROUTER DE PARSERS ====================
PARSERS_ESPECIFICOS = {
    "AFIRME":       afirme.analizar_afirme_texto if afirme else None,
    "BANAMEX":      banamex.analizar_banamex_final if banamex else None,
    "BANBAJIO":     banbajio.analizar_banbajio if banbajio else None,
    "AZTECA":       BancoAzteca.analizar_bancoazteca if BancoAzteca else None,
    "BANCOPPEL":    bancoppel.analizar_bancoppel_final if bancoppel else None,
    "BANORTE":      banorte.analizar_banorte_final if banorte else None,
    "BX_PLUS":      BX.analizar_bx_pypdf if BX else None,
    "HEYBANCO":     heybanco.analizar_heybanco if heybanco else None,
    "HSBC":         HSBC.analizar_hsbc if HSBC else None,
    "SCOTIABANK":   scotiabank.analizar_scotiabank if scotiabank else None,
    "INBURSA":      inbursa.analizar_inbursa if inbursa else None,
    "KAPITAL_BANK": KapitalBank.analizar_kapitalbank if KapitalBank else None,
    "MERCADO_PAGO": mercadopago.analizar_mercadopago if mercadopago else None,
    "MIFEL":        Mifel.analizar_mifel if Mifel else None,
    "MONEX":        Monex.analizar_monex if Monex else None,
}

# ==================== ORQUESTADOR ====================

def extract_and_analyze_pdf(pdf_path):
    logging.info(f"📄 Procesando PDF: {pdf_path}")
    
    ocr_text = ""
    native_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages: native_text += p.extract_text() or ""
        ocr_text = extract_text_with_ocr(pdf_path)
    except Exception as e:
        logging.error(f"Error lectura PDF: {e}")

    # --- CAMBIO IMPORTANTE: Pasamos el pdf_path para revisar el nombre del archivo ---
    nombre_banco = detectar_banco(ocr_text, native_text, file_path=pdf_path)
    logging.info(f"🏦 Banco identificado: {nombre_banco}")

    log_path = f"{pdf_path}.debug.txt"
    
    if nombre_banco in PARSERS_ESPECIFICOS and PARSERS_ESPECIFICOS[nombre_banco]:
        logging.info(f"🚀 Ejecutando parser específico para {nombre_banco}")
        parser_func = PARSERS_ESPECIFICOS[nombre_banco]
        
        try:
            resultado_crudo = ejecutar_parser(parser_func, pdf_path, cliente="")
            return normalizar_salida_especifica(resultado_crudo, nombre_banco, log_path)
        except Exception as e:
            logging.error(f"❌ Error crítico en parser {nombre_banco}: {e}")
            return {"status": "error", "message": f"Falló parser {nombre_banco}: {str(e)}", "log_path": log_path}

    logging.warning("⚠️ Banco no soportado específicamente. Usando fallback.")
    return {
        "status": "error",
        "message": f"Banco {nombre_banco} detectado pero sin parser.",
        "log_path": log_path
    }