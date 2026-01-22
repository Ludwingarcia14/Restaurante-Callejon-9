import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class BuroCreditoProcessor:
    """
    Parser + analizador para Reportes de Buró de Crédito (formato observado en Buro.pdf).
    Trabaja sobre `raw_text` (texto plano extraído del PDF).
    """

    # Códigos MOP considerados de alto riesgo
    MOP_NEGATIVO_ALTO = {'7', '8', '9'}

    # Map de meses abreviados en español e inglés que aparecen en buró
    MONTHS_MAP = {
        'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AGO': 8, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12, 'DEC': 12
    }

    def __init__(self, raw_text: str):
        # normalizar saltos y exceso de espacios (mantener texto en mayúsculas para facilitar patterns)
        text = raw_text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        text = re.sub(r"\s{2,}", " ", text)
        self.raw_text = text.strip()
        self.structured_data: Dict[str, Any] = {}
        # abrir debug file inicial
        self._write_debug("=== NUEVO PROCESAMIENTO DE BURÓ ===")

    # ----------------------
    # UTILIDADES
    # ----------------------
    def _write_debug(self, contenido: str):
        with open("debug_buro.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.utcnow().isoformat()}] {contenido}\n")

    def _clean_number(self, s: Optional[str]) -> float:
        if not s:
            return 0.0
        s = str(s)
        # Eliminar símbolos y espacios
        s = re.sub(r"[^\d\-.,]", "", s)
        # Acomodar comas y puntos: asumir coma como separador de miles
        s = s.replace(".", "")  # por si hay puntos como separador de miles
        s = s.replace(",", "")
        try:
            return float(s)
        except:
            return 0.0

    def _parse_month_year(self, token: str) -> Optional[datetime]:
        """
        Convierte tokens como 'NOV - 25' o 'OCT-25' a datetime aproximado (día=1).
        Si recibe '25-NOV-2025' o '25-NOV-25' intenta parsear la fecha exacta.
        """
        t = token.strip().upper()
        # patrón dd-MMM-YYYY o dd-MMM-YY
        m = re.match(r"(\d{1,2})[-/ ]*([A-Z]{3,})[-/ ]*(\d{2,4})", t)
        if m:
            day = int(m.group(1))
            mon = m.group(2)
            year = int(m.group(3))
            if year < 100:
                year += 2000
            month = self.MONTHS_MAP.get(mon[:3], None)
            if month:
                try:
                    return datetime(year, month, min(day, 28))
                except:
                    pass

        # patrón MMM - YY o MMM-YY o MMM - YYYY
        m2 = re.match(r"([A-Z]{3})\s*-\s*(\d{2,4})", t)
        if m2:
            mon = m2.group(1)
            year = int(m2.group(2))
            if year < 100:
                year += 2000
            month = self.MONTHS_MAP.get(mon[:3], None)
            if month:
                try:
                    return datetime(year, month, 1)
                except:
                    pass

        # patrón MMM YYYY (p.e. NOV 2025)
        m3 = re.match(r"([A-Z]{3})\s+(\d{4})", t)
        if m3:
            mon = m3.group(1); year = int(m3.group(2))
            month = self.MONTHS_MAP.get(mon[:3], None)
            if month:
                return datetime(year, month, 1)

        return None

    # ----------------------
    # EXTRACCIÓN: DATOS GENERALES (Nombre, domicilios)
    # ----------------------
    def _extract_persona_y_domicilios(self) -> Dict[str, Any]:
        result = {"nombre": None, "domicilios": []}
        # Nombre: ... seguido de fecha de nacimiento en formato dd-MMM-YYYY o dd-MMM-YYYY sin espacio
        m = re.search(r"Nombre[:]\s*([A-ZÑÁÉÍÓÚÜ\s]+?)\s+(\d{1,2}[-][A-Z]{3}[-]\d{4})", self.raw_text, re.IGNORECASE)
        if m:
            result["nombre"] = m.group(1).strip()
        else:
            # alternativa: buscar 'Nombre' y tomar hasta 'DOMICILIO' o 'DOMICILIO(S)'
            m2 = re.search(r"Nombre[:]\s*(.+?)DOMICILIO", self.raw_text, re.IGNORECASE)
            if m2:
                result["nombre"] = m2.group(1).strip()

        # domicilios: buscar aparición del bloque 'DOMICILIO(S) REPORTADO(S)' y tomar direcciones cercanas
        mdom = re.search(r"DOMICILIO\(S\)\s*REPORTADO\(S\)(.*?)RESUMEN DE CRÉDITOS", self.raw_text, re.IGNORECASE | re.DOTALL)
        if mdom:
            block = mdom.group(1)
            # dividir por mayúsculas de ciudad/estado o por números de CP
            addresses = re.findall(r"([A-Z0-9ÁÉÍÓÚÑ.,\s]{10,300}?(?:M[EÉ]XICO|MEXICO|CP\s*\d{4,5}|C\.P\.\s*\d{4,5}))", block, re.IGNORECASE)
            # fallback: si no hay matches, trocear en fragmentos de 100-200 chars
            if not addresses:
                addresses = [block[i:i+200].strip() for i in range(0, min(len(block), 1000), 200)]
            result["domicilios"] = [a.strip() for a in addresses if a.strip()]
        self._write_debug(f"[PERSONA] {result}")
        return result

    # ----------------------
    # EXTRACCIÓN: RESUMEN DE CRÉDITOS
    # ----------------------
    def _extract_resumen_creditos(self) -> List[Dict[str, Any]]:
        """
        Busca en la sección RESUMEN DE CRÉDITOS y extrae:
        - Entidad
        - Producto (si aparece cercano)
        - Status (ACTIVO/CERRADO)
        - Fecha de actualización (ej. 'NOV - 25' -> convertido)
        - Saldo actual (numero)
        - Comportamiento textual (si aparece 'UR' o 'CUENTA SIN INFORMACION' o iconos indicativos)
        """
        resultados: List[Dict[str, Any]] = []

        # extraer bloque principal entre 'RESUMEN DE CRÉDITOS' y 'DOCUMENTO SIN VALOR' o 'DETALLE DE CRÉDITOS'
        mblock = re.search(r"RESUMEN DE CRÉDITOS(.*?)(DETALLE DE CRÉDITOS|DOCUMENTO SIN VALOR|DETALLE DE CONSULTAS)", self.raw_text, re.IGNORECASE | re.DOTALL)
        block = mblock.group(1) if mblock else self.raw_text

        # patrón: Entidad ... [TIPO] (ACTIVO|CERRADO) ... luego aparece 'X. MMM - YY SALDO'
        # Buscamos todas las entidades conocidas y por cada una, tratamos de recuperar los datos siguientes
        entidades_pattern = re.compile(r"\b([A-Z&\s]{3,40}?)\s+(\d{6,20}|[A-Z0-9]{4,20})?\s*(TARJETA DE CRÉDITO|COMPRA DE AUTOMÓVIL|LÍNEA DE CRÉDITO|PRÉSTAMO PERSONAL|PRÉSTAMO|PAGOS FIJOS|REVOLVENTE|PAGOS FIJOS|PAGOS)\s*(ACTIVO|CERRADO)?", re.IGNORECASE)
        # Iteramos buscando ocurrencias tipo 'LIVERPOOL ... TARJETA ... ACTIVO'
        for em in entidades_pattern.finditer(block):
            entidad_raw = em.group(1).strip()
            producto_raw = em.group(3) or ""
            status_raw = em.group(4) or ""
            start_idx = em.end()

            # Buscar próximo patrón '(\d{1,2}\.)?\s*([A-Z]{3}\s*-\s*\d{2})\s+([\d,]+)'
            after = block[start_idx:start_idx+200]  # ventana corta
            m_after = re.search(r"(\d{1,2}\.)?\s*([A-Z]{3}\s*-\s*\d{2,4})\s+([\d,]+)", block[start_idx:start_idx+300], re.IGNORECASE)
            fecha_token = None
            saldo_val = 0.0
            if m_after:
                fecha_token = m_after.group(2)
                saldo_val = self._clean_number(m_after.group(3))

            # si no se encontró en ventana corta, buscar más adelante
            if not m_after:
                m_far = re.search(r"([A-Z]{3}\s*-\s*\d{2,4})\s+([\d,]{1,})", block[start_idx:start_idx+800], re.IGNORECASE)
                if m_far:
                    fecha_token = m_far.group(1)
                    saldo_val = self._clean_number(m_far.group(2))

            fecha_dt = self._parse_month_year(fecha_token) if fecha_token else None

            comportamiento = "buen comportamiento"
            # si status_raw contiene 'UR' o 'UR-CUENTA' o se encuentra 'UR' cerca, marcar mal comportamiento
            slice_near = block[max(0, em.start()-80):em.end()+200].upper()
            if "UR-CUENTA" in slice_near or "UR-" in slice_near or "SIN INFORMACION" in slice_near:
                comportamiento = "mal comportamiento"
            # Si status raw es CERRADO, no necesariamente es negativo salvo que tenga UR o similar
            if status_raw and status_raw.strip().upper() == "CERRADO":
                comportamiento = "cerrado"

            resultados.append({
                "Entidad": entidad_raw.title(),
                "Producto": producto_raw.title() if producto_raw else None,
                "Status": status_raw.strip().upper() if status_raw else None,
                "Actualizado_token": fecha_token,
                "Actualizado": fecha_dt.isoformat() if fecha_dt else None,
                "Saldo_actual": saldo_val,
                "Comportamiento": comportamiento
            })

        # write debug
        self._write_debug(f"[RESUMEN_EXTRAIDO] total={len(resultados)} lista={resultados}")
        return resultados

    # ----------------------
    # EXTRACCIÓN: DETALLE DE CRÉDITOS
    # ----------------------
    def _extract_detalle_creditos(self) -> List[Dict[str, Any]]:
        """
        Extrae bloques del DETALLE DE CRÉDITOS con
        Otorgante, No. de Cuenta, Tipo de Crédito, Apertura, Limite de Crédito, Saldo Actual y MOP histórico (si aparece).
        """
        resultados: List[Dict[str, Any]] = []

        mblock = re.search(r"DETALLE DE CRÉDITOS(.*?)(DETALLE DE CONSULTAS|DOCUMENTO SIN VALOR|PÁGINA)", self.raw_text, re.IGNORECASE | re.DOTALL)
        block = mblock.group(1) if mblock else self.raw_text

        # Dividir por patrones que marcan el inicio de cada cuenta: típicamente 'OTORGANTE\n<no cuenta>\nTIPO...'
        # Usamos: un otorgante en mayúsculas seguido de espacio y un número de cuenta
        entries = re.split(r"(?=\b[A-Z]{3,30}\s+\d{6,20})", block)
        for e in entries:
            e_strip = e.strip()
            if not e_strip:
                continue
            # extraer otorgante (primera palabra larga en mayúsculas)
            m_ot = re.match(r"([A-Z&\s]{3,40})\s+([0-9]{4,20})", e_strip)
            if not m_ot:
                # intentar encontrar solo la entidad en mayúsculas al inicio
                m_ot2 = re.match(r"([A-Z&\s]{3,40})", e_strip)
                if not m_ot2:
                    continue
                otorgante = m_ot2.group(1).strip()
            else:
                otorgante = m_ot.group(1).strip()

            # Buscar Saldo Actual y Límite en la entrada
            # Patrones observados: '125,906142,397135,100MXNOV-25JUN-24' -> aquí el primer número suele ser SaldoActual
            nums = re.findall(r"([\d]{1,3}(?:,[\d]{3})+|[\d]+)", e_strip)
            saldo_actual = 0.0
            limite_credito = 0.0
            apertura = None
            mop_historico = []

            if nums:
                # heurística: tomar el primer número largo con coma como Saldo Actual
                for n in nums:
                    if len(n) >= 3:
                        # priorizar números con coma (miles) y que aparezcan en contextos esperados
                        if ',' in n or len(n) > 4:
                            saldo_actual = self._clean_number(n)
                            break
                # segundo número largo podría ser limite
                if len(nums) >= 2:
                    limite_credito = self._clean_number(nums[1])

            # Apertura: buscar token tipo 'SEP-25' o 'NOV-25' o 'NOV-25' pegado
            m_ap = re.search(r"([A-Z]{3}\s*-\s*\d{2,4})", e_strip)
            if m_ap:
                apertura = m_ap.group(1)

            # MOP histórico: buscar secuencias de '1 1 1 1 2' o '1,1,1' o cadena '2025 1 1 ...' o '1 1 1 1 1'
            mops = re.search(r"\b(MOP[: ]*[0-9U\*\s]+)|((?:\b202[0-9]\b[\s\dU\*\,]{5,200}))", e_strip, re.IGNORECASE)
            if mops:
                mop_token = mops.group(0)
                # limpiar y extraer dígitos, U y *
                mop_list = re.findall(r"[0-9U\*]", mop_token)
                mop_historico = mop_list

            resultados.append({
                "Otorgante": otorgante.title(),
                "Apertura": apertura,
                "Limite_Credito": limite_credito,
                "Saldo_Actual": saldo_actual,
                "MOP_Historico": mop_historico
            })

        self._write_debug(f"[DETALLE_EXTRAIDO] total={len(resultados)} lista_sample={resultados[:6]}")
        return resultados

    # ----------------------
    # EXTRACCIÓN: CONSULTAS (DETALLE DE CONSULTAS)
    # ----------------------
    def _extract_detalle_consultas(self) -> List[Dict[str, Any]]:
        resultados: List[Dict[str, Any]] = []
        mblock = re.search(r"DETALLE DE CONSULTAS(.*?)(DOCUMENTO SIN VALOR|PÁGINA|$)", self.raw_text, re.IGNORECASE | re.DOTALL)
        block = mblock.group(1) if mblock else self.raw_text

        # patrones de consulta observados: 'BURO DE CREDITO ... 25-NOV-2025' o 'HAYCASH 5527274586 20-NOV-2025'
        pattern = re.compile(r"([A-Z&\s]{2,40}?)\s+(\d{1,2}[-/][A-Z]{3}[-/]\d{2,4})", re.IGNORECASE)
        for m in pattern.finditer(block):
            inst = m.group(1).strip()
            fecha_token = m.group(2).strip()
            fecha_dt = self._parse_month_year(fecha_token)
            resultados.append({
                "Institucion": inst.title(),
                "Fecha_token": fecha_token,
                "Fecha": fecha_dt.isoformat() if fecha_dt else None
            })

        self._write_debug(f"[CONSULTAS_EXTRAIDAS] total={len(resultados)} lista={resultados}")
        return resultados

    # ----------------------
    # ORQUESTADOR
    # ----------------------
    def _run_extraction(self):
        self.structured_data = {}
        # personales
        self.structured_data['persona'] = self._extract_persona_y_domicilios()
        # resumen
        self.structured_data['summary_data'] = self._extract_resumen_creditos()
        # detalle
        self.structured_data['detail_data'] = self._extract_detalle_creditos()
        # consultas
        self.structured_data['inquiry_data'] = self._extract_detalle_consultas()

        self._write_debug(f"[STRUCTURED DATA] keys={list(self.structured_data.keys())}")

    # ----------------------
    # ANÁLISIS
    # ----------------------
    def _analyze_summary(self) -> Dict[str, Any]:
        results = {
            'creditos_abiertos_info': [],
            'conteo_abiertos': 0,
            'conteo_cerrados': 0,
            'conteo_status_negativo': 0
        }
        for item in self.structured_data.get('summary_data', []):
            status = (item.get('Status') or "").upper()
            comportamiento = (item.get('Comportamiento') or "").lower()
            if status == 'ACTIVO':
                results['conteo_abiertos'] += 1
                results['creditos_abiertos_info'].append({
                    'entidad': item.get('Entidad'),
                    'fecha_actualizacion': item.get('Actualizado'),
                    'saldo_actual': item.get('Saldo_actual'),
                    'producto': item.get('Producto')
                })
            elif status == 'CERRADO':
                results['conteo_cerrados'] += 1

            if 'mal comportamiento' in comportamiento or 'ur' in (item.get('Status') or "").lower():
                results['conteo_status_negativo'] += 1

        return results

    def _analyze_details(self) -> Dict[str, Any]:
        results = {
            'saldo_actual_activo_total': 0.0,
            'mop_alto_riesgo_existente': False,
            'cuentas_con_mop_alto_riesgo': [],
            'total_cuentas_por_cobrar': 0.0,
        }

        # sumar saldos de resumen donde status=ACTIVO
        for s in self.structured_data.get('summary_data', []):
            if (s.get('Status') or "").upper() == 'ACTIVO':
                results['saldo_actual_activo_total'] += float(s.get('Saldo_actual') or 0.0)

        # revisar detalle para MOP y cuentas por cobrar
        for d in self.structured_data.get('detail_data', []):
            # total cuentas por cobrar: heurística -> si aparece Cuentas_Por_Cobrar usarlo, si no, 0
            cpc = d.get('Cuentas_Por_Cobrar', 0)
            if results['total_cuentas_por_cobrar'] == 0.0 and cpc:
                results['total_cuentas_por_cobrar'] = float(cpc)

            mop_hist = d.get('MOP_Historico') or []
            high = False
            for code in mop_hist:
                if str(code) in self.MOP_NEGATIVO_ALTO:
                    results['mop_alto_riesgo_existente'] = True
                    high = True
                    break
            if high and d.get('Otorgante'):
                if d.get('Otorgante') not in results['cuentas_con_mop_alto_riesgo']:
                    results['cuentas_con_mop_alto_riesgo'].append(d.get('Otorgante'))

        return results

    def _analyze_inquiries(self) -> Dict[str, Any]:
        consultas_recientes = []
        fecha_limite = datetime.now() - timedelta(days=365)
        for it in self.structured_data.get('inquiry_data', []):
            fecha_iso = it.get('Fecha')
            if fecha_iso:
                try:
                    fecha_dt = datetime.fromisoformat(fecha_iso)
                    if fecha_dt >= fecha_limite:
                        consultas_recientes.append({'institucion': it.get('Institucion'), 'fecha': fecha_iso})
                except:
                    consultas_recientes.append({'institucion': it.get('Institucion'), 'fecha': fecha_iso, 'nota': 'fecha no parseable'})
            else:
                consultas_recientes.append({'institucion': it.get('Institucion'), 'fecha': it.get('Fecha_token'), 'nota': 'fecha no parseable'})

        return {'consultas_en_ultimos_12_meses': consultas_recientes}

    # ----------------------
    # FUNCION PRINCIPAL
    # ----------------------
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Ejecuta extracción + análisis y devuelve el informe final.
        """
        self._run_extraction()

        resumen_analisis = self._analyze_summary()
        detalle_analisis = self._analyze_details()
        consultas_analisis = self._analyze_inquiries()

        informe_final = {
            'PERSONA': self.structured_data.get('persona', {}),
            'ANALISIS_RESUMEN': resumen_analisis,
            'ANALISIS_DETALLE_CREDITOS': detalle_analisis,
            'ANALISIS_DETALLE_CONSULTAS': consultas_analisis,
            'METRICAS_CLAVE': {
                'creditos_activos_totales': resumen_analisis['conteo_abiertos'],
                'creditos_cerrados_totales': resumen_analisis['conteo_cerrados'],
                'saldo_actual_total_activo': detalle_analisis['saldo_actual_activo_total'],
                'mop_alto_riesgo_detectado': detalle_analisis['mop_alto_riesgo_existente'],
                'cuentas_con_mop_alto_riesgo': detalle_analisis['cuentas_con_mop_alto_riesgo'],
                'total_consultas_recientes': len(consultas_analisis['consultas_en_ultimos_12_meses']),
                'total_cuentas_por_cobrar_sumado': detalle_analisis['total_cuentas_por_cobrar']
            },
            'STRUCTURED_RAW': self.structured_data  # opcional, para debug/inspección
        }

        self._write_debug(f"[INFORME_FINAL] metrics={informe_final['METRICAS_CLAVE']}")
        self._write_debug("ANÁLISIS COMPLETADO ✔")
        return informe_final
