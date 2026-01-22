import pdfplumber
import re
import logging
import unicodedata
import os
import pandas as pd

# ====================================================================
# CONFIGURACIÓN
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = ["TRASPASO ENTRE CUENTAS", "MISMA CUENTA", "TRASPASO A CUENTA", "TRASPASO A TERCEROS"]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS"]

def parse_float(text):
    """Convierte $1,234.56 a 1234.56"""
    if not text: return None
    # Eliminar todo lo que no sea dígito o punto
    clean = re.sub(r'[^\d.]', '', text.replace(',', ''))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper()

# ====================================================================
# LÓGICA DE TEXTO PLANO (SIN TABLAS)
# ====================================================================

def analizar_afirme_texto(pdf_path, cliente_objetivo):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "AFIRME",
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
            # ----------------------------------------------------
            # 1. ESCANEO INICIAL (Página 1: Saldos y Fechas)
            # ----------------------------------------------------
            full_text = ""
            for p in pdf.pages:
                full_text += p.extract_text(x_tolerance=2) + "\n" # x_tolerance ayuda a unir espacios
            
            # Buscar Periodo (Formato flexible: 01 AGO 2025 AL 31...)
            # Busca fecha inicio y fin aunque haya saltos de línea
            match_per = re.search(r'(\d{1,2}\s+[A-Z]{3,}\s+\d{4})\s*AL\s*(\d{1,2}\s+[A-Z]{3,}\s+\d{4})', full_text, re.IGNORECASE)
            if match_per:
                data["periodo"] = f"{match_per.group(1)} - {match_per.group(2)}".upper()

            # Buscar Saldo Promedio
            match_prom = re.search(r'Saldo promedio.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom:
                data["saldo_promedio"] = parse_float(match_prom.group(1))

            # Buscar Saldo Inicial (CRÍTICO)
            match_ini = re.search(r'Saldo inicial.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_ini:
                data["saldo_inicial"] = parse_float(match_ini.group(1))
            else:
                # Fallback: Intentar buscar "Saldo anterior"
                match_ant = re.search(r'Saldo anterior.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_ant: data["saldo_inicial"] = parse_float(match_ant.group(1))

            print(f"--- DATOS INICIALES ---")
            print(f"Saldo Inicial Base: ${data['saldo_inicial']:,.2f}")
            
            # ----------------------------------------------------
            # 2. PROCESAMIENTO LÍNEA POR LÍNEA
            # ----------------------------------------------------
            saldo_actual = data["saldo_inicial"]
            cliente_norm = normalizar(cliente_objetivo)
            
            # Dividir todo el texto en líneas para procesar secuencialmente
            lines = full_text.split('\n')
            
            for line in lines:
                line_norm = normalizar(line)
                
                # Ignorar encabezados y pies de página
                if "SALDO" in line_norm or "HOJA" in line_norm or "PAGINA" in line_norm:
                    continue
                
                # BUSCAR TODOS LOS MONTOS EN LA LÍNEA
                # Regex captura números como 1,234.56 o 1234.56 al final o en medio
                montos_str = re.findall(r'[\d,]+\.\d{2}', line)
                montos = [parse_float(m) for m in montos_str]
                
                if len(montos) >= 2:
                    # Asumimos: El ÚLTIMO número es el SALDO RESULTANTE
                    posible_nuevo_saldo = montos[-1]
                    
                    # El penúltimo O alguno de los anteriores podría ser el monto de la operación
                    # Probamos la matemática:
                    
                    es_ingreso = False
                    monto_operacion = 0.0
                    
                    # 1. Comprobar si es INGRESO (Saldo Anterior + Monto = Nuevo Saldo)
                    # Usamos un margen de error de 0.10 por redondeos
                    diff = posible_nuevo_saldo - saldo_actual
                    
                    if diff > 0.1:
                        # Confirmar si la diferencia aparece escrita en la línea
                        # (Esto evita confundir números de referencia con montos)
                        found_diff = False
                        for m in montos[:-1]: # Revisar todos menos el saldo final
                            if abs(m - diff) < 1.0: # Si el monto escrito coincide con la diferencia matemática
                                found_diff = True
                                monto_operacion = m
                                break
                        
                        if found_diff or len(montos)==2: # Si solo hay 2 nums, asumimos que son [Monto, Saldo]
                            if not found_diff: monto_operacion = diff # Confianza en la matemática
                            
                            es_ingreso = True
                            
                            # --- CLASIFICACIÓN DEL INGRESO ---
                            tipo = "VALIDO"
                            desc = line.strip()
                            
                            if any(kw in line_norm for kw in KW_TRASPASOS) or (cliente_norm in line_norm and "TRASPASO" in line_norm):
                                tipo = "TRASPASO_PROPIO"
                                data["descartes"]["traspasos"] += monto_operacion
                            elif any(kw in line_norm for kw in KW_CREDITOS):
                                tipo = "CREDITO"
                                data["descartes"]["creditos"] += monto_operacion
                            elif any(kw in line_norm for kw in KW_DEVOLUCIONES):
                                tipo = "DEVOLUCION"
                                data["descartes"]["devoluciones"] += monto_operacion
                            else:
                                data["ingresos_netos"] += monto_operacion
                            
                            if any(kw in line_norm for kw in KW_TPV):
                                data["tpv"] += monto_operacion

                            data["ingresos_brutos"] += monto_operacion
                            data["log_transacciones"].append(f"[+] ${monto_operacion:,.2f} ({tipo}) | {desc[:40]}...")
                            
                            # ACTUALIZAR SALDO
                            saldo_actual = posible_nuevo_saldo
                            continue # Pasamos a sig línea

                    # 2. Comprobar si es RETIRO (Saldo Anterior - Monto = Nuevo Saldo)
                    # Esto sirve para mantener el 'saldo_actual' sincronizado
                    elif diff < -0.1:
                         # Es un retiro, solo actualizamos el saldo
                         # Validación opcional: verificar si abs(diff) está en la línea
                         saldo_actual = posible_nuevo_saldo

    except Exception as e:
        return {"error": str(e)}

    return data

# ====================================================================
# EJECUCIÓN
# ====================================================================

if __name__ == "__main__":
    archivo = "AFIRME .pdf"
    cliente = "CONSTRUCCIONES URBANIZACIONES" 
    
    print(f"ANÁLISIS V6 (TEXTO PLANO) PARA: {archivo}")
    res = analizar_afirme_texto(archivo, cliente)
    
    if "error" not in res:
        print("\n" + "="*50)
        print(f" REPORTE FINAL: {res['banco']}")
        print("="*50)
        print(f"Periodo:                {res['periodo']}")
        print(f"Saldo Inicial Detectado:${res['saldo_inicial']:,.2f}")
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
            print("\n[DETALLE] Primeras 5 transacciones detectadas:")
            for log in res["log_transacciones"][:5]:
                print(log)
        else:
            print("\n[ALERTA] No se detectaron ingresos. Verifique si el PDF es legible (OCR).")
            
    else:
        print(f"Error: {res['error']}")