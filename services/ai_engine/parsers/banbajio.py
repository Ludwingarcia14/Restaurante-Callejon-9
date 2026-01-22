import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN BANBAJIO (V5 - REPORTE DETALLADO FINAL)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO", "FINANCIAMIENTO", "LINEA DE CREDITO"]
KW_TRASPASOS = [
    "TRASPASO ENTRE CUENTAS", "CUENTAS PROPIAS", "TRASPASO A CUENTA", "MISMA CUENTA", 
    "TRASPASO A TERCEROS", "TRASPASO A CTA", "TRASPASO BEM", "TEF", "TRASPASO", 
    "DE LA CUENTA", "INVERSION", "MERCADO DE DINERO", "PROPIA", "TRASPASO ENV"
]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO", "CANCELACION", "RETORNO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL", "COMERCIOS", "CARGO POR TPV", "DEP POR TPV"]

KW_CARGOS = ["CARGO", "COMISION", "RETIRO", "CHEQUE", "IVA", "PAGO", "TRASPASO ENV", "COMPRA"]
KW_ABONOS = ["DEPOSITO", "ABONO", "RECEPCION", "NOMINA", "TRASPASO REC"]

MESES_ABREV = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

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

def analizar_banbajio(pdf_path, cliente_objetivo):
    if not os.path.exists(pdf_path): return {"error": "Archivo no encontrado"}

    data = {
        "banco": "BANBAJIO",
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

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for p in pdf.pages:
                full_text += p.extract_text(x_tolerance=2, y_tolerance=3) + "\n"

            # 1. Periodo
            match_per = re.search(r'PERIODO:?\s*(\d{1,2}\s+DE\s+[A-Z]+\s+AL\s+\d{1,2}\s+DE\s+[A-Z]+\s+DE\s+\d{4})', full_text, re.IGNORECASE)
            if match_per: data["periodo"] = match_per.group(1).upper()
            
            match_dias = re.search(r'DIAS DEL PERIODO:?\s*(\d+)', full_text, re.IGNORECASE)
            if match_dias: dias_del_periodo = int(match_dias.group(1))

            # 2. Saldo Promedio (Lectura inicial)
            match_prom = re.search(r'SALDO PROMEDIO (?!MENSUAL|MINIMO).*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom: data["saldo_promedio"] = parse_float(match_prom.group(1))

            # 3. Saldo Inicial
            if data["saldo_inicial"] == 0:
                match_ini = re.search(r'SALDO ANTERIOR\s.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
                if match_ini: data["saldo_inicial"] = parse_float(match_ini.group(1))
            
            if data["saldo_inicial"] == 0: # Intento Tabla
                p1 = pdf.pages[0]
                tables = p1.extract_tables()
                for table in tables:
                    for i, row in enumerate(table):
                        row_str = [str(c).upper() if c else "" for c in row]
                        if "SALDO ANTERIOR" in row_str:
                            try:
                                col_idx = row_str.index("SALDO ANTERIOR")
                                if i + 1 < len(table):
                                    val = parse_float(table[i+1][col_idx])
                                    if val is not None: data["saldo_inicial"] = val
                            except: pass

            # 4. Motor
            saldo_actual = data["saldo_inicial"]
            saldo_calculado = False
            cliente_norm = normalizar(cliente_objetivo)
            lines = full_text.split('\n')
            
            for line in lines:
                line_norm = normalizar(line)
                
                dia_movimiento = 1
                match_dia = re.match(r'^(\d{1,2})\s+', line_norm)
                if match_dia: dia_movimiento = int(match_dia.group(1))

                es_mov = False
                for mes in MESES_ABREV:
                    if re.search(r'\b\d{1,2}\s+' + mes, line_norm): es_mov = True; break
                if not es_mov: continue

                montos_str = re.findall(r'[\d,]+\.\d{2}', line)
                montos = [parse_float(m) for m in montos_str]
                
                if len(montos) >= 2:
                    posible_nuevo_saldo = montos[-1]
                    posible_monto_op = montos[-2]
                    
                    if saldo_actual == 0 and not saldo_calculado:
                        es_cargo = any(kw in line_norm for kw in KW_CARGOS)
                        es_abono = any(kw in line_norm for kw in KW_ABONOS) or "DEPOSITO" in line_norm
                        if es_cargo: saldo_actual = posible_nuevo_saldo + posible_monto_op
                        elif es_abono: saldo_actual = posible_nuevo_saldo - posible_monto_op
                        else: saldo_actual = posible_nuevo_saldo + posible_monto_op
                        data["saldo_inicial"] = saldo_actual
                        saldo_calculado = True

                    diff = posible_nuevo_saldo - saldo_actual
                    if abs(diff) < 0.1: continue
                    if abs(diff - posible_nuevo_saldo) < 1.0: 
                        saldo_actual = posible_nuevo_saldo; continue
                    
                    monto_real = diff
                    transacciones_con_fecha.append((dia_movimiento, monto_real))

                    if diff > 0.1: # Ingreso
                        monto_calc = diff
                        visual_ok = False
                        for m in montos[:-1]:
                            if abs(m - monto_calc) < 1.0: visual_ok = True; break
                        if not visual_ok: continue 

                        tipo = "VALIDO"
                        desc = line.strip()

                        if any(kw in line_norm for kw in KW_TRASPASOS) or (cliente_norm in line_norm and "TRASPASO" in line_norm):
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

            # 5. Cálculo Final de Promedio
            if data["saldo_promedio"] == 0 or data["saldo_promedio"] == 5000.00:
                data["saldo_promedio"] = calcular_promedio_ponderado(data["saldo_inicial"], transacciones_con_fecha, dias_del_periodo)

    except Exception as e: return {"error": str(e)}
    return data

if __name__ == "__main__":
    archivo = "banbajio.pdf"
    cliente = "LABORATORIO CLINICO NOVA TPM"
    
    print(f"ANALIZANDO BANBAJIO (V5): {archivo}")
    res = analizar_banbajio(archivo, cliente)

    if "error" not in res:
        print("\n" + "="*50)
        print(f" REPORTE FINAL: {res['banco']}")
        print("="*50)
        print(f"Periodo:                {res['periodo']}")
        print(f"Saldo Anterior:         ${res['saldo_inicial']:,.2f}")
        print(f"Saldo Promedio:         ${res['saldo_promedio']:,.2f}")
        print("-" * 30)
        print(f"(+) INGRESOS BRUTOS:    ${res['ingresos_brutos']:,.2f}")
        # --- AQUÍ ESTÁ EL DESGLOSE QUE PEDISTE ---
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