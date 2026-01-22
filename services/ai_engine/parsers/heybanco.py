import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN HEY BANCO (V7 - PERIODO COMPLETO)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO", "AUTOMOTRIZ", "TARJETA DE CREDITO"]
KW_TRASPASOS = [
    "TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "TRASPASO A CUENTA", "MISMA CUENTA", 
    "TRASPASO A TERCEROS", "TRASPASO A CTA", "TRASPASO BEM", "TEF", "TRASPASO", 
    "DE LA CUENTA", "INVERSION", "MERCADO DE DINERO", "PROPIA", "TRASPASO ENV",
    "ENVIADO A CUENTA", "TRASPASO A TERCEROS", "PAGO CAPITAL", "PAGO INTERES"
]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV", "DEP POR TPV"]

def parse_float(text):
    if not text: return None
    clean = re.sub(r'[^\d.-]', '', str(text).replace(',', ''))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

def calcular_promedio_ponderado(saldo_inicial, transacciones, dias_totales=30):
    if dias_totales <= 0: return 0.0
    saldo_diario_acumulado = 0.0
    saldo_actual = saldo_inicial
    movs_por_dia = {}
    
    for dia, monto in transacciones:
        if dia not in movs_por_dia: movs_por_dia[dia] = 0.0
        movs_por_dia[dia] += monto
        
    for dia in range(1, dias_totales + 1):
        if dia in movs_por_dia:
            saldo_actual += movs_por_dia[dia]
        saldo_diario_acumulado += saldo_actual
        
    return saldo_diario_acumulado / dias_totales

def analizar_heybanco(pdf_path, cliente_objetivo=""):
    if not os.path.exists(pdf_path): return {"error": "Archivo no encontrado"}

    data = {
        "banco": "HEY BANCO",
        "periodo": "No Encontrado",
        "saldo_promedio": 0.0,
        "saldo_inicial": 0.0,
        "ingresos_brutos": 0.0,
        "ingresos_netos": 0.0,
        "descartes": {"traspasos": 0.0, "creditos": 0.0, "devoluciones": 0.0},
        "tpv": 0.0,
        "log_transacciones": []
    }
    
    transacciones_con_fecha = []
    dias_del_periodo = 30
    seccion_credito_activa = False

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for p in pdf.pages:
                full_text += p.extract_text(x_tolerance=2, y_tolerance=3) + "\n"

            # 1. PERIODO (CORREGIDO PARA MOSTRAR RANGO COMPLETO)
            # Busca la frase completa: "del 01 al 30 de ABRIL 2025"
            match_per = re.search(r'((?:del|al)\s+\d{1,2}\s+(?:al|de)\s+\d{1,2}\s+de\s+[A-Z]+\s+\d{4})', full_text, re.IGNORECASE)
            if match_per:
                # Tomamos todo el grupo capturado (la frase completa)
                data["periodo"] = match_per.group(1).upper()
                
            # Extraer días del periodo para el cálculo de promedio
            match_dias = re.search(r'(\d+)\s+Días', full_text, re.IGNORECASE)
            if match_dias: dias_del_periodo = int(match_dias.group(1))

            # 2. SALDO PROMEDIO
            match_prom = re.search(r'Saldo Promedio.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom: data["saldo_promedio"] = parse_float(match_prom.group(1))

            # 3. SALDO INICIAL
            if data["saldo_inicial"] == 0:
                match_ini = re.search(r'Saldo Inicial\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_ini: data["saldo_inicial"] = parse_float(match_ini.group(1))
            
            if data["saldo_inicial"] == 0:
                match_ant = re.search(r'Saldo Anterior\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_ant: data["saldo_inicial"] = parse_float(match_ant.group(1))

            print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

            # 4. MOTOR MATEMÁTICO
            saldo_actual = data["saldo_inicial"]
            cliente_norm = normalizar(cliente_objetivo) if cliente_objetivo else ""
            usar_filtro_nombre = len(cliente_norm) > 4 and "GENERICO" not in cliente_norm and "DESCONOCIDO" not in cliente_norm

            lines = full_text.split('\n')
            
            for line in lines:
                line_norm = normalizar(line)
                
                # --- DETECTOR DE SECCIÓN DE CRÉDITO ---
                if "CREDITO" in line_norm or "AUTOMOTRIZ" in line_norm:
                    seccion_credito_activa = True
                if "CUENTA" in line_norm or "CHEQUES" in line_norm or "NEGOCIOS" in line_norm:
                    seccion_credito_activa = False
                if seccion_credito_activa: continue

                # --- FILTRO DE LÍNEA ---
                match_linea = re.match(r'^(\d{2})\s+[A-Z]{3}', line_norm)
                if not match_linea: continue
                if "TOTAL" in line_norm: continue
                
                dia_movimiento = int(match_linea.group(1))

                montos_str = re.findall(r'[\d,]+\.\d{2}', line)
                montos = [parse_float(m) for m in montos_str]
                
                if len(montos) >= 2:
                    posible_nuevo_saldo = montos[-1]
                    diff = posible_nuevo_saldo - saldo_actual
                    
                    if abs(diff) < 0.1: continue
                    if abs(diff - posible_nuevo_saldo) < 1.0: 
                        saldo_actual = posible_nuevo_saldo; continue

                    monto_real = diff
                    transacciones_con_fecha.append((dia_movimiento, monto_real))
                    monto_calc = diff

                    # INGRESO
                    if diff > 0.1:
                        visual_ok = False
                        for m in montos[:-1]:
                            if abs(m - monto_calc) < 1.0: visual_ok = True; break
                        if not visual_ok: continue

                        tipo = "VALIDO"
                        desc = line.strip()

                        # Filtros Negocio
                        if any(kw in line_norm for kw in KW_TRASPASOS):
                            tipo = "TRASPASO_PROPIO"
                            data["descartes"]["traspasos"] += monto_calc
                        elif usar_filtro_nombre and cliente_norm in line_norm and "TRASPASO" in line_norm:
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
                    
                    elif diff < -0.1:
                        saldo_actual = posible_nuevo_saldo
            
            # 5. CÁLCULO FINAL DE PROMEDIO
            if data["saldo_promedio"] == 0:
                print("Calculando Saldo Promedio Matemáticamente...")
                data["saldo_promedio"] = calcular_promedio_ponderado(data["saldo_inicial"], transacciones_con_fecha, dias_del_periodo)

    except Exception as e:
        return {"error": str(e)}

    return data

if __name__ == "__main__":
    archivo = "heybanco.pdf"
    cliente = "CLIENTE_DESCONOCIDO"
    
    print(f"ANALIZANDO HEY BANCO (V7): {archivo}")
    res = analizar_heybanco(archivo, cliente)

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
            print(res["log_transacciones"][:3])
    else:
        print(f"Error: {res['error']}")