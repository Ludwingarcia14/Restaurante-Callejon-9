import pdfplumber
import re
import logging
import unicodedata
import os

# ====================================================================
# CONFIGURACIÓN BANCOPPEL (V4 - Inferencia de Periodo)
# ====================================================================
logging.basicConfig(level=logging.INFO, format="%(message)s")

KW_INGRESOS_REALES = [
    "DEPOSITO", "ABONO", "RECEPCION", "RECIBIDO", "NOMINA", 
    "PRESTAMO", "CREDITO", "TRASPASO", "SPEI RECIBIDO", "INTERESTADO"
]

KW_EGRESOS = [
    "CARGO", "RETIRO", "PAGO", "COMISION", "CHEQUE", "SPEI ENVIADO", "COMPRA"
]

KW_TRASPASOS_PROPIOS = ["CUENTA PROPIA", "MISMA CUENTA", "ENTRE CUENTAS", "PROPIA"]
KW_CREDITOS = ["DISPOSICION", "CREDITO", "PRESTAMO"]
KW_DEVOLUCIONES = ["DEVOLUCION", "REVERSO"]
KW_TPV = ["TPV", "AFILIACION", "VENTA TERMINAL"]

def parse_float(text):
    if not text: return None
    clean = re.sub(r'[^\d.]', '', str(text).replace(',', ''))
    try:
        return float(clean)
    except:
        return None

def normalizar(text):
    return unicodedata.normalize("NFKD", str(text)).upper().strip()

def analizar_bancoppel_final(pdf_path, cliente_objetivo):
    if not os.path.exists(pdf_path):
        return {"error": "Archivo no encontrado"}

    data = {
        "banco": "BANCOPPEL",
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
            full_text = ""
            # Lista para guardar las fechas que veamos en las transacciones (ej: 08/08)
            fechas_movimientos = [] 
            
            for p in pdf.pages:
                full_text += p.extract_text(x_tolerance=3, y_tolerance=3) + "\n"

            # 1. BÚSQUEDA DE AÑO (Para completar las fechas cortas)
            match_anio = re.search(r'20\d{2}', full_text)
            anio_doc = match_anio.group(0) if match_anio else "20XX"

            # 2. ENCABEZADOS (Intento estándar)
            match_per = re.search(r'DEL\s+(\d{2}/\d{2}/\d{4})\s+AL\s+(\d{2}/\d{2}/\d{4})', full_text, re.IGNORECASE)
            if match_per:
                data["periodo"] = f"{match_per.group(1)} - {match_per.group(2)}"
            
            # Saldo Promedio
            match_prom = re.search(r'Saldo Promedio.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_prom: data["saldo_promedio"] = parse_float(match_prom.group(1))

            # Saldo Inicial
            match_ini = re.search(r'Saldo Anterior.*?\$?\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            if match_ini: data["saldo_inicial"] = parse_float(match_ini.group(1))

            print(f"Saldo Inicial Detectado: ${data['saldo_inicial']:,.2f}")

            # 3. ANÁLISIS DE LÍNEAS
            lines = full_text.split('\n')
            cliente_norm = normalizar(cliente_objetivo)
            
            for line in lines:
                line_norm = normalizar(line)
                if len(line) < 15: continue

                # A. BUSCAR FECHAS EN LA LÍNEA (DD/MM)
                # BanCoppel suele poner la fecha al inicio: "08/08 TRASPASO..."
                match_fecha_linea = re.search(r'\b(\d{2}/\d{2})\b', line)
                if match_fecha_linea:
                    fechas_movimientos.append(match_fecha_linea.group(1))

                # B. EXTRAER DINERO
                montos_str = re.findall(r'[\d,]+\.\d{2}', line)
                montos = [parse_float(m) for m in montos_str]
                
                if len(montos) >= 2:
                    posible_monto = montos[-2]
                    posible_saldo = montos[-1]
                    
                    es_ingreso = False
                    if any(kw in line_norm for kw in KW_INGRESOS_REALES): es_ingreso = True
                    if any(kw in line_norm for kw in KW_EGRESOS): es_ingreso = False 

                    # Lógica Traspaso
                    if "TRASPASO" in line_norm:
                        if "A CUENTA" in line_norm or "PAGO" in line_norm or "ENVIADO" in line_norm:
                            es_ingreso = False
                        else:
                            es_ingreso = True 

                    if es_ingreso:
                        monto = posible_monto
                        tipo = "VALIDO"
                        desc = line.strip()

                        if any(kw in line_norm for kw in KW_TRASPASOS_PROPIOS) or (cliente_norm in line_norm):
                            tipo = "TRASPASO_PROPIO"
                            data["descartes"]["traspasos"] += monto
                        elif any(kw in line_norm for kw in KW_CREDITOS):
                            tipo = "CREDITO"
                            data["descartes"]["creditos"] += monto
                        elif any(kw in line_norm for kw in KW_DEVOLUCIONES):
                            tipo = "DEVOLUCION"
                            data["descartes"]["devoluciones"] += monto
                        else:
                            data["ingresos_netos"] += monto
                        
                        if any(kw in line_norm for kw in KW_TPV):
                            data["tpv"] += monto

                        data["ingresos_brutos"] += monto
                        data["log_transacciones"].append(f"[+] ${monto:,.2f} ({tipo}) | {desc[:30]}...")
            
            # 4. INFERENCIA DE PERIODO (Si falló el regex del encabezado)
            if data["periodo"] == "No Encontrado" and fechas_movimientos:
                # BanCoppel suele ordenar del más nuevo al más viejo, o viceversa.
                # Tomamos el primero y el último de la lista para cubrir el rango.
                primera = fechas_movimientos[-1] # Probablemente la más antigua si ordena descendente
                ultima = fechas_movimientos[0]   # Probablemente la más reciente
                
                # Armamos el periodo con el año detectado
                data["periodo"] = f"{primera}/{anio_doc} - {ultima}/{anio_doc} (Inferido)"

    except Exception as e:
        return {"error": str(e)}

    return data

if __name__ == "__main__":
    archivo = "bancoppel.pdf"
    cliente = "JUAN EDUARDO GONZALEZ VALENCIA"
    
    print(f"ANALIZANDO BANCOPPEL (V4 - Periodo Inferido): {archivo}")
    res = analizar_bancoppel_final(archivo, cliente)

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
        print("-" * 30)
        print(f"(=) INGRESO NETO REAL:  ${res['ingresos_netos']:,.2f}")
        print("="*50)
    else:
        print(f"Error: {res['error']}")