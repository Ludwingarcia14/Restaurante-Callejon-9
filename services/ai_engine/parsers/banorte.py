import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN BANORTE (V5 - Fechas Flexibles)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO", "CREDI"]
KW_TRASPASOS = [
    "TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "TRASPASO A CUENTA", "MISMA CUENTA", 
    "TRASPASO A TERCEROS", "TRASPASO A CTA", "TRASPASO BEM", "TEF",
    "DE LA CUENTA", "TRASPASO DE CUENTA", "INVERSION ENLACE", "MERCADO DE DINERO"
]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO", "DEV"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV", "DEP POR TPV"]

# Palabras que indican que la línea NO es una transacción real
KW_IGNORE = [
    "TOTAL", "SALDO PROMEDIO", "SALDO PROM", "SALDO ANTERIOR", "SALDO FINAL", 
    "RESUMEN", "INVERSION", "LIQ.INT.", "TOTAL DE", "GAT", "TASA", "INTERES", 
    "IMPUESTO", "RETENCION", "ISR", "BRUTA", "ANUAL", "COMISION"
]

def parse_float(text):
    if not text: return None
    clean = re.sub(r'[^\d.]', '', text.replace(',', ''))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

def analizar_banorte_final(pdf_path, cliente_objetivo):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "BANORTE",
        "periodo": "No Encontrado",
        "saldo_promedio": 0.0,
        "saldo_inicial": 0.0,
        "ingresos_brutos": 0.0,
        "ingresos_netos": 0.0,
        "descartes": {"traspasos": 0.0, "creditos": 0.0, "devoluciones": 0.0},
        "tpv": 0.0,
        "log_transacciones": []
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 1. EXTRACCIÓN Y DEBUG
            full_text = ""
            print("\n--- TEXTO ENCABEZADO (DEBUG) ---")
            p1_text = pdf.pages[0].extract_text(x_tolerance=2, y_tolerance=3)
            print(p1_text[:300]) # Muestra los primeros 300 caracteres para verificar fecha
            print("--- FIN DEBUG ---\n")
            
            for p in pdf.pages:
                full_text += p.extract_text(x_tolerance=2, y_tolerance=3) + "\n"

            # 2. BÚSQUEDA DE PERIODO (REGEX MEJORADO)
            # Soporta: "PERIODO DEL 01/JUL/2025...", "Del 01-07-25...", espacios entre barras, años cortos
            patron_flexible = r'(?:PERIODO|DEL|AL)?\s*(?:DEL)?\s*[:\s]*(\d{1,2}\s*[/\-]\s*[A-Z0-9]+\s*[/\-]\s*\d{2,4})\s+(?:AL|A)\s+(\d{1,2}\s*[/\-]\s*[A-Z0-9]+\s*[/\-]\s*\d{2,4})'
            
            match_per = re.search(patron_flexible, full_text, re.IGNORECASE)
            if match_per:
                # Limpiamos espacios extra dentro de la fecha (ej: 01 / JUL -> 01/JUL)
                f1 = re.sub(r'\s+', '', match_per.group(1))
                f2 = re.sub(r'\s+', '', match_per.group(2))
                data["periodo"] = f"{f1} - {f2}".upper()
            else:
                # Intento secundario (Formato texto largo: 01 DE JULIO DE 2025)
                match_largo = re.search(r'DEL\s+(\d{1,2})\s+DE\s+([A-Z]+).*?AL\s+(\d{1,2})\s+DE\s+([A-Z]+)', full_text, re.IGNORECASE | re.DOTALL)
                if match_largo:
                    data["periodo"] = f"{match_largo.group(1)}/{match_largo.group(2)} - {match_largo.group(3)}/{match_largo.group(4)}".upper()

            # 3. DATOS INICIALES
            match_prom = re.search(r'Saldo Promedio.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom: 
                data["saldo_promedio"] = parse_float(match_prom.group(1))
            else:
                match_prom_alt = re.search(r'SALDO PROM.*?([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_prom_alt: data["saldo_promedio"] = parse_float(match_prom_alt.group(1))

            match_ini = re.search(r'Saldo Anterior.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_ini: data["saldo_inicial"] = parse_float(match_ini.group(1))
            if data["saldo_inicial"] == 0:
                match_alt = re.search(r'Saldo Inicial.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_alt: data["saldo_inicial"] = parse_float(match_alt.group(1))

            print(f"Saldo Anterior Detectado: ${data['saldo_inicial']:,.2f}")

            # 4. PROCESAMIENTO
            saldo_actual = data["saldo_inicial"]
            cliente_norm = normalizar(cliente_objetivo)
            lines = full_text.split('\n')
            
            for line in lines:
                line_norm = normalizar(line)
                
                # Ignorar basura explícita
                if any(bad_word in line_norm for bad_word in KW_IGNORE): continue
                if "FECHA" in line_norm and "SALDO" in line_norm: continue

                montos_str = re.findall(r'[\d,]+\.\d{2}', line)
                montos = [parse_float(m) for m in montos_str]
                
                if len(montos) >= 2:
                    posible_nuevo_saldo = montos[-1]
                    diff = posible_nuevo_saldo - saldo_actual
                    
                    # Filtro espejo (Saldo inicial repetido)
                    if abs(diff - posible_nuevo_saldo) < 1.0:
                        saldo_actual = posible_nuevo_saldo
                        continue

                    # INGRESO DETECTADO
                    if diff > 0.1:
                        monto_calculado = diff
                        
                        # --- VALIDACIÓN VISUAL OBLIGATORIA ---
                        encontrado_en_texto = False
                        for m in montos[:-1]: 
                            if abs(m - monto_calculado) < 1.0:
                                encontrado_en_texto = True
                                break
                        
                        if not encontrado_en_texto:
                            continue 

                        # ES UN INGRESO REAL
                        tipo = "VALIDO"
                        desc = line.strip()
                        
                        # Filtros de Negocio
                        es_traspaso = False
                        if any(kw in line_norm for kw in KW_TRASPASOS): es_traspaso = True
                        if (cliente_norm in line_norm and ("TRASPASO" in line_norm or "ABONO" in line_norm)): es_traspaso = True
                        
                        if es_traspaso:
                            tipo = "TRASPASO_PROPIO"
                            data["descartes"]["traspasos"] += monto_calculado
                        elif any(kw in line_norm for kw in KW_CREDITOS):
                            tipo = "CREDITO"
                            data["descartes"]["creditos"] += monto_calculado
                        elif any(kw in line_norm for kw in KW_DEVOLUCIONES):
                            tipo = "DEVOLUCION"
                            data["descartes"]["devoluciones"] += monto_calculado
                        else:
                            data["ingresos_netos"] += monto_calculado
                        
                        if any(kw in line_norm for kw in KW_TPV):
                            data["tpv"] += monto_calculado

                        data["ingresos_brutos"] += monto_calculado
                        data["log_transacciones"].append(f"[+] ${monto_calculado:,.2f} ({tipo}) | {desc[:40]}...")
                        
                        saldo_actual = posible_nuevo_saldo

                    # RETIRO
                    elif diff < -0.1:
                        saldo_actual = posible_nuevo_saldo

    except Exception as e:
        return {"error": str(e)}

    return data

if __name__ == "__main__":
    archivo = "BANORTE JULIO 2025 (1).pdf"
    cliente = "CONSTRUCCIONES URBANIZACIONES"
    
    print(f"ANALIZANDO BANORTE (V5): {archivo}")
    res = analizar_banorte_final(archivo, cliente)

    if "error" not in res:
        print("\n" + "="*50)
        print(f" REPORTE FINAL: {res['banco']}")
        print("="*50)
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
        print("="*50)
    else:
        print(f"Error: {res['error']}")