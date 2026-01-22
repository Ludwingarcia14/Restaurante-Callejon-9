from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
from services.ai_engine.bank_statement_analyzer import extract_and_analyze_pdf
from services.ai_engine.match_engine import MatchEngine
from services.notificaciones.notification_service import notificar_financiera, notificar_usuario
import traceback

def procesar_perfil_background(app, usuario_id, file_paths, tipo_doc):
    """
    Procesa una lista de estados de cuenta en background.
    """
    with app.app_context():
        try:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            print(f"🔄 Iniciando análisis IA usuario {usuario_id} - Archivos a procesar: {len(file_paths)}")

            acumulado_ingresos = 0.0
            acumulado_saldos = 0.0
            conteo_exitoso = 0
            
            # 1. Iterar y procesar cada archivo individualmente
            for path in file_paths:
                try:
                    print(f"📄 Analizando archivo: {path}")
                    resultado = extract_and_analyze_pdf(path)

                    if resultado.get("status") == "success":
                        ingreso_mes = float(resultado.get("ingresos_reales", 0.0))
                        saldo_mes = float(resultado.get("saldo_promedio", 0.0))
                        
                        print(f"   ✅ Datos extraídos: Ingreso=${ingreso_mes:,.2f}, Saldo=${saldo_mes:,.2f}")

                        acumulado_ingresos += ingreso_mes
                        acumulado_saldos += saldo_mes
                        conteo_exitoso += 1
                    else:
                        print(f"⚠️ Advertencia en {path}: {resultado.get('message')}")

                except Exception as e_file:
                    print(f"❌ Error procesando archivo {path}: {e_file}")
                    continue

            if conteo_exitoso == 0:
                notificar_usuario(usuario_id, "ERROR_ANALISIS", "No se pudo extraer información válida de los documentos subidos.")
                return

            # 2. Calcular PROMEDIOS (Consolidación)
            promedio_ingresos = acumulado_ingresos / conteo_exitoso
            promedio_saldo = acumulado_saldos / conteo_exitoso

            print(f"📊 Resultados Consolidados ({conteo_exitoso} meses): Ingreso Promedio=${promedio_ingresos:,.2f}, Saldo Promedio=${promedio_saldo:,.2f}")

            # 3. Calcular Evaluación Express
            evaluacion = "Perfil financiero débil"
            if promedio_ingresos > 100000 and promedio_saldo > 30000:
                evaluacion = "Perfil financiero sólido"
            elif promedio_ingresos > 50000:
                evaluacion = "Perfil financiero medio"

            datos_ia = {
                "promedio_depositos": promedio_ingresos, # [IMPORTANTE] Usar este nombre clave para el Dashboard
                "saldo_promedio": promedio_saldo,
                "ingresos_promedio": promedio_ingresos,
                "evaluacion": evaluacion,
                "giro": "General", 
                "meses_analizados": conteo_exitoso,
                "fecha_analisis": datetime.utcnow()
            }

            # -------------------------------------------------------------------------
            # [NUEVO] GUARDAR EN COLECCIÓN DE DOCUMENTOS PARA EL DASHBOARD
            # -------------------------------------------------------------------------
            # Esto permite que clientController.py encuentre los datos en "analisis_financiero"
            
            # Determinamos la colección correcta basándonos en el tipo de documento o una lógica general
            # Asumimos 'fisica' por defecto, pero idealmente 'tipo_doc' debería decirnos
            collection_docs = db.documentofisica 
            
            # Si tienes manera de saber si es moral (ej. consultando el usuario), ajusta aquí:
            usuario = db.clientes.find_one({"_id": ObjectId(usuario_id)})
            if usuario and usuario.get("tipo_persona") == "moral":
                collection_docs = db.documentomoral

            collection_docs.update_one(
                {"usuario_id": ObjectId(usuario_id)},
                {"$set": {
                    "documentos.analisis_financiero": datos_ia, # <--- Aquí es donde el Dashboard lee
                    "last_updated": datetime.utcnow()
                }}
            )
            print(f"✅ Análisis guardado en 'documentos.analisis_financiero' para el Dashboard.")
            # -------------------------------------------------------------------------

            # 4. Obtener datos del cliente de la BD
            perfil_cliente = usuario or {} # Reutilizamos la consulta anterior

            datos_completos = {
                
                "monto_solicitado": float(perfil_cliente.get("monto_solicitado", 0)),
                "score_buro": int(perfil_cliente.get("score_buro", 0)),
                "estado": perfil_cliente.get("estado", ""),
                "ingresos_promedio": datos_ia["ingresos_promedio"],
                "giro": datos_ia["giro"]
            }

            # 5. Motor de Coincidencias (Match Engine)
            engine = MatchEngine()
            financieras = db.financieras.find({})
            matches = []

            for fin in financieras:
                try:
                    match = engine.evaluar_compatibilidad(datos_completos, fin)
                except:
                    continue

                if match["nivel"] in ["perfecto", "potencial"]:
                    matches.append(match)
                    if match["nivel"] == "perfecto":
                        notificar_financiera(match["aliado_email"], datos_completos, match["nombre"])

            # 6. Guardar Resultados de Matches
            db.matches.update_one(
                {"cliente_id": ObjectId(usuario_id)},
                {"$set": {
                    "resultados": matches,
                    "datos_analisis": datos_ia,
                    "fecha_analisis": datetime.utcnow(),
                    "status": "completado"
                }},
                upsert=True
            )

            if matches:
                matches.sort(key=lambda x: x["score"], reverse=True)
                notificar_usuario(
                    usuario_id,
                    "ANALISIS_COMPLETADO",
                    f"Análisis de {conteo_exitoso} meses completado. {len(matches)} opciones financieras encontradas.",
                    {"matches_count": len(matches)}
                )
            else:
                notificar_usuario(usuario_id, "ANALISIS_SIN_RESULTADOS", "Perfil analizado sin coincidencias financieras.")

        except Exception as e:
            print(traceback.format_exc())
            notificar_usuario(usuario_id, "ERROR_SISTEMA", "Error crítico en análisis masivo.")