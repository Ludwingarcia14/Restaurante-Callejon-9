import os
import logging
from flask import request, jsonify, session # ✅ Agregamos session
from werkzeug.utils import secure_filename
from datetime import datetime # ✅ Para fechas
from bson.objectid import ObjectId # ✅ Para IDs de Mongo

# ✅ Importamos la conexión a BD
from config.db import db

# ====================================================================
# 🚨 IMPORTACIONES CQRS (Desde la carpeta 'ia') 🚨
# ====================================================================

# Queries
from cqrs.queryes.ia.models.analyze_doc_query import AnalyzeDocumentQuery
from cqrs.queryes.ia.handlers.document_analyzer_handler import DocumentAnalyzerHandler

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directorio para guardar archivos temporales
UPLOAD_FOLDER = 'static/temp_uploads'

class iaController:
    """Controlador para la lógica de análisis de documentos por IA (Adaptador HTTP)."""

    # ----------------------------------------------------
    # Método para análisis genérico (DELEGADO + GUARDADO BD)
    # ----------------------------------------------------
    @staticmethod
    def analyze():
        """Recibe el PDF, analiza y SI hay usuario logueado, guarda en BD."""

        # 1. Validaciones básicas
        if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
            return jsonify({'error': 'No se encontró el archivo "pdf_file" o nombre vacío'}), 400

        file = request.files['pdf_file']
        print(f"🚀 Iniciando análisis SAT desde iaController para: {file.filename}")

        # 2. Crear Query DTO
        query = AnalyzeDocumentQuery(uploaded_file=file, upload_folder=UPLOAD_FOLDER)

        # 3. Ejecutar Query Handler (Tu lógica de extracción)
        result = DocumentAnalyzerHandler.handle_generic_analysis(query)

        # 4. Verificar resultado y Guardar en BD si corresponde
        if result['status'] == 'success':
            datos_analisis = result['analysis']

            # ✅ LÓGICA DE GUARDADO EN BASE DE DATOS
            # Verificamos si hay un usuario logueado para asociar los datos
            if 'usuario_id' in session:
                try:
                    usuario_id = session['usuario_id']
                    tipo_persona = session.get('tipo_persona', 'fisica').lower() # Default fisica

                    print(f"💾 Guardando resultados SAT para usuario {usuario_id} ({tipo_persona})...")

                    # A) Actualizar datos clave en la colección de Clientes (Perfil)
                    # Solo si se encontró un RFC válido para evitar ensuciar la BD con nulos
                    if datos_analisis.get("rfc"):
                        db.clientes.update_one(
                            {"_id": ObjectId(usuario_id)},
                            {"$set": {
                                "rfc": datos_analisis.get("rfc"),
                                "regimen_fiscal_principal": datos_analisis.get("regimen_fiscal"),
                                "giro_fiscal": datos_analisis.get("giro"),
                                "status_sat": datos_analisis.get("vigente"),
                                "fecha_ultima_validacion_sat": datetime.utcnow()
                            }}
                        )

                    # B) Guardar el análisis COMPLETO en la colección de Documentos
                    # Elegimos la colección según el tipo de persona
                    collection_docs = db.documentomoral if tipo_persona == "moral" else db.documentofisica

                    collection_docs.update_one(
                        {"usuario_id": ObjectId(usuario_id)},
                        {"$set": {
                            "documentos.datos_fiscales": datos_analisis, # <--- ¡AQUÍ SE GUARDA TODO!
                            "documentos.fecha_analisis_sat": datetime.utcnow(),
                            "last_updated": datetime.utcnow()
                        }},
                        upsert=True # Crea el documento si no existe
                    )

                    print("✅ Datos guardados correctamente en MongoDB.")

                except Exception as e:
                    logging.error(f"❌ Error al guardar en BD: {e}")
                    # No detenemos la respuesta HTTP si falla el guardado, pero lo logueamos
            else:
                print("⚠️ Análisis realizado sin sesión de usuario. No se guardó en BD.")

            # 5. Responder al Frontend con el JSON del análisis
            return jsonify({'analysis': datos_analisis}), 200

        else:
            # Devuelve el error de validación o del servicio
            return jsonify({'error': result['message']}), 400


    # ---------------------------------------------------------
    # MÉTODO FINAL para extracción y análisis de Estados de Cuenta (DELEGADO)
    # ---------------------------------------------------------

    @staticmethod
    def analyze_estados_cuenta():
        """Delega el flujo de análisis de Estados de Cuenta al Query Handler."""

        if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
            return jsonify({'error': 'No se encontró el archivo "pdf_file" o nombre vacío'}), 400

        file = request.files['pdf_file']
        
        # 1. Crear Query DTO
        query = AnalyzeDocumentQuery(uploaded_file=file, upload_folder=UPLOAD_FOLDER)

        # 2. Ejecutar Query Handler
        result = DocumentAnalyzerHandler.handle_bank_statement_analysis(query)

        # 3. Mapear resultado a respuesta HTTP
        if result['status'] == 'success':
            return jsonify({'analysis': result['analysis']}), 200
        else:
            # Devuelve el error de validación o del servicio
            return jsonify({'error': result['message']}), 400
            
    # El método 'extract_tables_from_pdf' original ha sido eliminado o movido, 
    # ya que no es utilizado por el flujo principal de análisis delegado.

    @staticmethod
    def analyze_estados_cuenta():
        """Delega el flujo de análisis de Estados de Cuenta al Query Handler."""

        # CAMBIO 1: Verificar si hay archivos, usando getlist para ver si la lista no está vacía
        if 'pdf_file' not in request.files or not request.files.getlist('pdf_file'):
            return jsonify({'error': 'No se encontraron archivos "pdf_file"'}), 400

        # CAMBIO 2: Obtener la lista completa de archivos
        files = request.files.getlist('pdf_file')
        
        # 1. Crear Query DTO (Debes adaptar tu Query para aceptar 'uploaded_files' en plural)
        # Asegúrate de modificar AnalyzeDocumentQuery para recibir una lista
        query = AnalyzeDocumentQuery(uploaded_files=files, upload_folder=UPLOAD_FOLDER)

        # 2. Ejecutar Query Handler
        # Tu handler deberá guardar todos los PDFs y pasar la LISTA de rutas al orquestador
        result = DocumentAnalyzerHandler.handle_bank_statement_analysis(query)

        if result['status'] == 'success':
            return jsonify({'analysis': result['analysis']}), 200
        else:
            return jsonify({'error': result['message']}), 400