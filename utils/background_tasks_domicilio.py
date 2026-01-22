# utils/background_tasks_domicilio.py

import logging
from flask import Flask
from bson.objectid import ObjectId

# 🔥 IMPORTANTE: usar el analizador de PDF, NO el extractor de texto
from services.ai_engine.domicilio_analyzer import analizar_pdf_comprobante
from models.documentofisica_model import DocumentoFisica

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def procesar_domicilio_async(app: Flask, usuario_id: str, file_path: str):
    """
    Tarea en segundo plano para analizar el comprobante de domicilio y actualizar la DB.
    """
    with app.app_context():
        try:
            logging.info(
                f"Iniciando análisis de Comprobante Domicilio para usuario: {usuario_id}"
            )

            # 🔥 1️⃣ ANALIZAR DIRECTAMENTE EL PDF
            analysis_result = analizar_pdf_comprobante(file_path)

            if not analysis_result or "error" in analysis_result:
                logging.error(
                    f"Error en análisis de domicilio para {usuario_id}: {analysis_result}"
                )
                return

            logging.info(f"Resultado análisis: {analysis_result}")

            # 🔥 2️⃣ Preparar datos para BD
            update_data = {
                "comprobante_domicilio_vigencia": analysis_result.get("vigencia"),
                "comprobante_domicilio_fecha_emision": analysis_result.get("fecha_emision"),
                "domicilio_extraido": analysis_result.get("direccion_del_domicilio")
            }

            # 🔥 3️⃣ Actualizar base de datos
            DocumentoFisica.update_document_analysis(
                usuario_id=ObjectId(usuario_id),
                document_type="comprobante_domicilio",
                analysis_data=update_data
            )

            logging.info(
                f"Análisis de Domicilio completado para {usuario_id}. "
                f"Vigencia: {analysis_result.get('vigencia')}"
            )

        except Exception as e:
            logging.error(
                f"Error fatal en procesar_domicilio_async para {usuario_id}: {e}",
                exc_info=True
            )
