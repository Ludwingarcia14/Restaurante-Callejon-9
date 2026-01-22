import re
import logging
import unicodedata
import os
try:
    from pypdf import PdfReader
except ImportError:
    print("¡ERROR! Necesitas instalar pypdf. Ejecuta: pip install pypdf")
    exit()

# ====================================================================
# CONFIGURACIÓN BX+ (V4 - Motor pypdf)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = [
    "TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "TRASPASO A CUENTA", "MISMA CUENTA", 
    "TRASPASO A TERCEROS", "TRASPASO A CTA", "TRASPASO BEM", "TEF", "TRASPASO", 
    "DE LA CUENTA", "INVERSION", "MERCADO DE DINERO"
]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV"]

# Palabras de resumen a ignorar
KW_IGNORE = ["TOTAL", "SALDO PROMEDIO", "SALDO FINAL", "RESUMEN", "GAT", "TASA", "INTERES", "COMISION", "RENDIMIENTOS"]

def parse_float(text):
    if not text: return None
    clean = re.sub(r'[^\d.]', '', str(text).replace(',', ''))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

def analizar_bx_pypdf(pdf_path, cliente_objetivo):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "BX+ (VE POR MAS)",
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
        # 1. EXTRACCIÓN CON PYPDF (Más robusto para fuentes raras)
        reader = PdfReader(pdf_path)
        full_text = ""
        
        print("\n--- DEBUG TEXTO (pypdf) ---")
        # Extraemos texto página por página
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        print(f"Caracteres leídos: {len(full_text)}")
        print(f"Muestra: {full_text[:200].replace(chr(10), ' ')}")
        print("--- FIN DEBUG ---\n")

        if len(full_text) < 100:
            return {"error": "El PDF parece ser una imagen escaneada (requiere OCR)."}

        # 2. BÚSQUEDA DE PERIODO (BX+ Format: 01-01-2025 31-01-2025)
        # Regex busca dos fechas separadas por espacio o guion
        match_per = re.search(r'(\d{2}-\d{2}-\d{4})[\s-]+(\d{2}-\d{2}-\d{4})', full_text)
        if match_per:
            data["periodo"] = f"{match_per.group(1)} - {match_per.group(2)}"

        # 3. SALDOS
        match_prom = re.search(r'Saldo Promedio.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
        if match_prom: data["saldo_promedio"] = parse_float(match_prom.group(1))

        match_ini = re.search(r'Saldo (?:Anterior|Inicial).*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
        if match_ini: 
            data["saldo_inicial"] = parse_float(match_ini.group(1))
        else:
            # Fallback BX+: buscar en la primera línea de movimientos
            # A veces aparece como "Saldo anterior" dentro de la tabla
            match_tbl = re.search(r'Saldo anterior\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_tbl: data["saldo_inicial"] = parse_float(match_tbl.group(1))

        print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

        # 4. MOTOR MATEMÁTICO
        saldo_actual = data["saldo_inicial"]
        cliente_norm = normalizar(cliente_objetivo)
        lines = full_text.split('\n')
        
        for line in lines:
            line_norm = normalizar(line)
            
            if any(bad in line_norm for bad in KW_IGNORE): continue
            if "FECHA" in line_norm and "SALDO" in line_norm: continue
            
            # Buscar números
            montos_str = re.findall(r'[\d,]+\.\d{2}', line)
            montos = [parse_float(m) for m in montos_str]
            
            if len(montos) >= 2:
                # En BX+, a veces el orden es [Monto, Saldo] o [Saldo, Monto] dependiendo de la columna
                # Asumimos que el último número grande es el saldo
                posible_nuevo_saldo = montos[-1]
                diff = posible_nuevo_saldo - saldo_actual
                
                # Filtro espejo (misma línea leída dos veces o encabezado)
                if abs(diff) < 0.1 or abs(diff - posible_nuevo_saldo) < 1.0:
                    saldo_actual = posible_nuevo_saldo
                    continue

                # INGRESO
                if diff > 0.1:
                    monto_calc = diff
                    
                    # Validación visual
                    visual_ok = False
                    for m in montos[:-1]:
                        if abs(m - monto_calc) < 1.0:
                            visual_ok = True
                            break
                    
                    if not visual_ok: continue

                    tipo = "VALIDO"
                    desc = line.strip()
                    
                    # Filtros
                    if any(kw in line_norm for kw in KW_TRASPASOS):
                        tipo = "TRASPASO_PROPIO"
                        data["descartes"]["traspasos"] += monto_calc
                    elif cliente_norm in line_norm and "TRASPASO" in line_norm:
                        tipo = "TRASPASO_PROPIO"
                        data["descartes"]["traspasos"] += monto_calc
                    elif any(kw in line_norm for kw in KW_CREDITOS):
                        tipo = "CREDITO"
                        data["descartes"]["creditos"] += monto_calc
                    elif any(kw in line_norm for kw in KW_DEVOLUCIONES):
                        tipo = "DEVOLUCION"
                        data["descartes"]["devoluciones"] += monto_calc
                    else:
                        data["ingresos_netos"] += monto_calc
                    
                    if any(kw in line_norm for kw in KW_TPV):
                        data["tpv"] += monto_calc

                    data["ingresos_brutos"] += monto_calc
                    data["log_transacciones"].append(f"[+] ${monto_calc:,.2f} ({tipo}) | {desc[:40]}...")
                    
                    saldo_actual = posible_nuevo_saldo

                # RETIRO
                elif diff < -0.1:
                    saldo_actual = posible_nuevo_saldo

    except Exception as e:
        return {"error": str(e)}

    return data

if __name__ == "__main__":
    archivo = "BX.pdf"
    cliente = "SOLUCIONES KAAT AANTAH"
    
    print(f"ANALIZANDO BX+ (V4 - pypdf): {archivo}")
    res = analizar_bx_pypdf(archivo, cliente)

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
        
        if res["ingresos_brutos"] > 0:
            print(f"\n[INFO] Movimientos detectados: {len(res['log_transacciones'])}")
            print(res["log_transacciones"][:5])
    else:
        print(f"Error: {res['error']}")