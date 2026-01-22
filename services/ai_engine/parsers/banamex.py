import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN BANAMEX (V10 - Periodo Corregido)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = ["TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "TRASPASO A CUENTA", "MISMA CUENTA", "INVERSION PERFILES", "TRASPASO TERCEROS"]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV"]

def parse_float(text):
    if not text: return None
    clean = re.sub(r'[^\d.]', '', text.replace(',', ''))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

def analizar_banamex_final(pdf_path, cliente_objetivo):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "BANAMEX",
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
            # 1. TEXTO COMPLETO
            full_text = ""
            for p in pdf.pages:
                full_text += p.extract_text(x_tolerance=2, y_tolerance=3) + "\n"

            # 2. BÚSQUEDA DE PERIODO (NUEVOS PATRONES)
            
            # CASO A: "Del 1 al 31 de agosto del 2025" (Tu caso actual)
            # Busca: Del [Dia] al [Dia] de [Mes] del [Año]
            patron_corto = r'Del\s+(\d{1,2})\s+al\s+(\d{1,2})\s+de\s+([A-Z]+)\s+(?:del|de)\s+(\d{4})'
            match_corto = re.search(patron_corto, full_text, re.IGNORECASE)

            # CASO B: "Del 01 de Agosto al 31 de Agosto de 2025" (Formato largo)
            patron_largo = r'Del\s+(\d{1,2})\s+de\s+([A-Z]+)\s+al\s+(\d{1,2})\s+de\s+([A-Z]+)\s+(?:del|de)\s+(\d{4})'
            match_largo = re.search(patron_largo, full_text, re.IGNORECASE)

            if match_corto:
                d1, d2, mes, ano = match_corto.groups()
                data["periodo"] = f"{d1} AL {d2} DE {mes} {ano}".upper()
            elif match_largo:
                data["periodo"] = match_largo.group(0).upper().replace('\n', ' ')

            # 3. EXTRACCIÓN FINANCIERA (Igual que antes)
            match_prom = re.search(r'Saldo promedio.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom: data["saldo_promedio"] = parse_float(match_prom.group(1))

            match_ini = re.search(r'Saldo anterior.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_ini: data["saldo_inicial"] = parse_float(match_ini.group(1))
            
            # Fallback saldo inicial
            if data["saldo_inicial"] == 0:
                match_alt = re.search(r'Saldo al corte anterior.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_alt: data["saldo_inicial"] = parse_float(match_alt.group(1))

            # 4. MATEMÁTICA LÍNEA POR LÍNEA
            saldo_actual = data["saldo_inicial"]
            cliente_norm = normalizar(cliente_objetivo)
            lines = full_text.split('\n')
            
            for line in lines:
                line_norm = normalizar(line)
                
                # Ignorar encabezados
                if "FECHA" in line_norm and "SALDO" in line_norm: continue
                if "GAT" in line_norm or "TASAS" in line_norm: continue

                montos_str = re.findall(r'[\d,]+\.\d{2}', line)
                montos = [parse_float(m) for m in montos_str]
                
                if len(montos) >= 2:
                    posible_nuevo_saldo = montos[-1]
                    diff = posible_nuevo_saldo - saldo_actual
                    
                    # FILTRO ESPEJO (Evitar leer Saldo Inicial repetido)
                    if abs(diff - posible_nuevo_saldo) < 1.0:
                        saldo_actual = posible_nuevo_saldo
                        continue

                    # INGRESO
                    if diff > 0.1:
                        monto_operacion = diff
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
                        
                        saldo_actual = posible_nuevo_saldo

                    # RETIRO
                    elif diff < -0.1:
                        saldo_actual = posible_nuevo_saldo

    except Exception as e:
        return {"error": str(e)}

    return data

# ====================================================================
# EJECUCIÓN
# ====================================================================
if __name__ == "__main__":
    archivo = "BANAMEX AGOSTO.pdf" 
    cliente = "YULLTYELY TORRES VILCHIS" # Ajustado según tu debug anterior

    print(f"ANALIZANDO BANAMEX (V10): {archivo}")
    res = analizar_banamex_final(archivo, cliente)

    if "error" not in res:
        print("\n" + "="*50)
        print(f" REPORTE FINAL: {res['banco']}")
        print("="*50)
        print(f"Periodo Detectado:      {res['periodo']}")
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