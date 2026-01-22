# cqrs/queries/ia/handlers/document_analyzer_handler.py

import os
import logging
from werkzeug.utils import secure_filename
from ..models.analyze_doc_query import AnalyzeDocumentQuery
from typing import Dict, Any

# ⚠️ Importaciones de Servicios de IA (Deben ser accesibles desde aquí)
# Ajusta estas rutas según dónde estén tus archivos 'services'
from services.ai_engine.text_extractor import extract_text_from_pdf
from services.ai_engine.analyzer import analyze_pdf_text
from services.ai_engine.bank_statement_analyzer import extract_and_analyze_pdf 


class DocumentAnalyzerHandler:
    @staticmethod
    def handle_generic_analysis(query: AnalyzeDocumentQuery) -> Dict[str, Any]:
        """Orquesta el análisis genérico (ej. Constancia SAT)."""
        
        # 1. Preparar rutas y guardar archivo temporal
        filename = secure_filename(query.uploaded_file.filename)
        query.file_path = os.path.join(query.upload_folder, filename)
        
        try:
            os.makedirs(query.upload_folder, exist_ok=True)
            query.uploaded_file.save(query.file_path)
            
            # 2. Extraer y Analizar
            pdf_text = extract_text_from_pdf(query.file_path)
            if not pdf_text.strip():
                raise ValueError('No se pudo extraer texto del PDF.')

            analysis_result = analyze_pdf_text(pdf_text)
            
            logging.info("✅ Análisis genérico completado.")
            return {'analysis': analysis_result, 'status': 'success'}

        except ValueError as e:
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            logging.error(f"Error en el análisis genérico del PDF: {e}")
            return {'status': 'error', 'message': f"Error interno del servidor: {str(e)}"}
        finally:
            # 3. Limpiar archivo temporal
            if query.file_path and os.path.exists(query.file_path):
                os.remove(query.file_path)


    @staticmethod
    def handle_bank_statement_analysis(query: AnalyzeDocumentQuery) -> Dict[str, Any]:
        """Orquesta el análisis específico de Estados de Cuenta."""
        
        # 1. Preparar rutas y guardar archivo temporal
        filename = secure_filename(query.uploaded_file.filename)
        query.file_path = os.path.join(query.upload_folder, filename)

        try:
            os.makedirs(query.upload_folder, exist_ok=True)
            query.uploaded_file.save(query.file_path)
            
            # 2. LLAMADA A LA FUNCIÓN DE EXTRACCIÓN Y ANÁLISIS
            analysis_result = extract_and_analyze_pdf(query.file_path)
            
            # 3. Manejo de error retornado por el servicio
            if analysis_result.get('status') == 'error':
                 logging.error(f"Error en la extracción/análisis: {analysis_result.get('message')}")
                 raise ValueError(analysis_result.get('message'))

            logging.info(f"✅ Análisis de Estado de Cuenta completado para: {analysis_result.get('file')}")
            return {'analysis': analysis_result, 'status': 'success'}

        except ValueError as e:
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            logging.error(f"Error en la extracción/análisis de Estado de Cuenta: {e}")
            return {'status': 'error', 'message': f"Error interno del servidor: {str(e)}"}
        finally:
            # 4. Limpiar archivo temporal
            if query.file_path and os.path.exists(query.file_path):
                os.remove(query.file_path)