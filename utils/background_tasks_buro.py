# services/ai_engine/buro_async_task.py

from flask import Flask
from bson.objectid import ObjectId 
from datetime import datetime       
from config.db import db            
# Asumo que estas clases están definidas y disponibles:
from services.ai_engine.buro_credito_analyzer import BuroCreditoProcessor 
from services.ai_engine.text_extractor import extract_text_from_pdf 


def _determinar_coleccion_y_campo(usuario_id):
    """Determina si el usuario es física o moral y el nombre del campo Buró en la DB."""
    user_obj_id = ObjectId(usuario_id)
    
    # 1. Buscar en la colección de persona física
    if db.documentofisica.find_one({"usuario_id": user_obj_id}):
        return db.documentofisica, "buro_credito_fisica"
        
    # 2. Buscar en la colección de persona moral
    elif db.documentomoral.find_one({"usuario_id": user_obj_id}):
        return db.documentomoral, "buro_credito_moral"
        
    return None, None # Retorna None si no se encuentra el usuario en ninguna colección


def procesar_buro_async(app: Flask, usuario_id: str, buro_file_path: str):
    """
    Función wrapper que ejecuta el análisis del Buró de Crédito y guarda los resultados.
    """
    with app.app_context(): 
        try:
            app.logger.info(f"▶️ Iniciando procesamiento asíncrono de Buró para {usuario_id}...")
            
            # === 1. EXTRACCIÓN DE TEXTO ===
            raw_text = extract_text_from_pdf(buro_file_path) 
            
            if not raw_text:
                app.logger.warning(f"⚠️ Buró Crédito: Texto vacío o no extraíble para {usuario_id}. No se puede analizar.")
                return

            # === 2. ANÁLISIS DE DATOS ===
            processor = BuroCreditoProcessor(raw_text) 
            final_analysis_report = processor.run_full_analysis()
            
            # === 3. PERSISTENCIA DE RESULTADOS EN MONGODB ===
            collection, buro_field_name = _determinar_coleccion_y_campo(usuario_id)

            # CORRECCIÓN CLAVE: Usar comparación explícita con None
            if collection is not None and buro_field_name:
                user_obj_id = ObjectId(usuario_id)
                
                update_fields = {
                    # Guarda el JSON de resultados completo en el sub-documento de Buró
                    f"documentos.{buro_field_name}.analisis_buro": final_analysis_report,
                    # Registra la fecha de finalización del análisis
                    f"documentos.{buro_field_name}.fecha_analisis": datetime.utcnow()
                }
                
                # Opcional: Marcar riesgo a nivel superior para fácil consulta
                if final_analysis_report.get("METRICAS_CLAVE", {}).get("mop_alto_riesgo_detectado"):
                     update_fields[f"documentos.{buro_field_name}.riesgo_detectado"] = True
                
                collection.update_one(
                    {"usuario_id": user_obj_id},
                    {"$set": update_fields}
                )
                app.logger.info(f"✅ Análisis de Buró guardado en {collection.name} para {usuario_id}.")
            else:
                app.logger.error(f"⚠️ No se encontró la colección del usuario para guardar análisis de Buró para {usuario_id}.")

        except Exception as e:
            app.logger.error(f"🔥 Error en el análisis de Buró (procesar_buro_async): {e}", exc_info=True)
            raise