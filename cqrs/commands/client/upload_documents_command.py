from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

class UploadDocumentsCommand:

    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

    def __init__(self, usuario_id: str, files: dict):
        self.usuario_id = usuario_id
        self.usuario_obj = ObjectId(usuario_id)
        self.files = files

        self.campos_fisica = [
            "ine_fisica", "domicilio_fisica", "situacion_fiscal_fisica",
            "buro_credito_fisica", "estados_cuenta_fisica",
            "declaracion_anual_fisica", "estados_financieros_fisica"
        ]

        self.campos_moral = [
            "ine_moral", "domicilio_moral", "situacion_fiscal_moral",
            "buro_credito_moral", "acta_constitutiva_moral",
            "poderes_notariales_moral", "declaracion_anual_moral",
            "estados_financieros_moral", "estados_cuenta_moral"
        ]

    def _allowed(self, filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def _delete_previous_file(self, ruta_relativa):
        if not ruta_relativa: return
        ruta_absoluta = os.path.join(current_app.root_path, ruta_relativa)
        if os.path.exists(ruta_absoluta):
            try: os.remove(ruta_absoluta)
            except: pass

    def execute(self):
        lista_estados_cuenta = []
        ine_archivos_para_analisis = {}
        buro_archivo_para_analisis = None
        domicilio_archivo_para_analisis = None

        # --- 1. Detección de Tipo ---
        tiene_archivos_moral = any(any(f.filename for f in self.files.getlist(k)) for k in self.campos_moral)
        tiene_archivos_fisica = any(any(f.filename for f in self.files.getlist(k)) for k in self.campos_fisica)

        if tiene_archivos_moral:
            tipo = "moral"
            lista_campos = self.campos_moral
            collection = db.documentomoral
        elif tiene_archivos_fisica:
            tipo = "fisica"
            lista_campos = self.campos_fisica
            collection = db.documentofisica
        else:
            raise ValueError("No se seleccionaron archivos nuevos.")

        # --- 2. Preparación ---
        doc_actual = collection.find_one({"usuario_id": self.usuario_obj}) or {}
        
        # CARPETA CON ID DE USUARIO (Tu requerimiento anterior)
        upload_folder = os.path.join(current_app.root_path, "static", "uploads", tipo, str(self.usuario_id))
        os.makedirs(upload_folder, exist_ok=True)

        update_fields = {}
        has_files = False

        # --- 3. Procesamiento ---
        for campo in lista_campos:
            archivos = self.files.getlist(campo)
            archivos_validos = [f for f in archivos if f and f.filename]

            if not archivos_validos:
                continue

            has_files = True
            
            # DETECTAR SI ES MULTI-ARCHIVO (Estados de Cuenta)
            es_multi_archivo = campo in ["estados_cuenta_fisica", "estados_cuenta_moral"]
            
            lista_archivos_db = []
            
            if es_multi_archivo:
                # Si es múltiple, recuperamos lo que ya existe para NO borrarlo
                datos_actuales = doc_actual.get("documentos", {}).get(campo)
                
                # Migración: Si antes era un solo objeto (dict), lo convertimos a lista
                if isinstance(datos_actuales, dict) and datos_actuales:
                    lista_archivos_db = [datos_actuales]
                elif isinstance(datos_actuales, list):
                    lista_archivos_db = datos_actuales
                else:
                    lista_archivos_db = []
            else:
                # Si es único, borramos el anterior físico y limpiamos referencia
                ruta_prev = doc_actual.get("documentos", {}).get(campo, {}).get("ruta")
                if ruta_prev:
                    self._delete_previous_file(ruta_prev)

            # Guardar nuevos archivos
            for archivo in archivos_validos:
                if not self._allowed(archivo.filename):
                    raise ValueError(f"Extensión no permitida en {archivo.filename}")

                filename = secure_filename(f"{uuid.uuid4()}_{archivo.filename}")
                ruta_absoluta = os.path.join(upload_folder, filename)
                archivo.save(ruta_absoluta)

                ruta_relativa = f"static/uploads/{tipo}/{self.usuario_id}/{filename}"
                
                metadata_archivo = {
                    "ruta": ruta_relativa,
                    "nombre_original": archivo.filename,
                    "fecha_subida": datetime.utcnow()
                }

                if es_multi_archivo:
                    # Agregamos a la lista acumulada
                    lista_archivos_db.append(metadata_archivo)
                    # Para la IA (analizar solo los nuevos)
                    lista_estados_cuenta.append(ruta_absoluta)
                else:
                    # Sobreescribimos el campo directo
                    update_fields[f"documentos.{campo}"] = metadata_archivo
                    
                    # Variables de retorno IA
                    if campo in ["ine_fisica", "ine_moral"]:
                        ine_archivos_para_analisis[campo] = ruta_absoluta
                    elif campo in ["buro_credito_fisica", "buro_credito_moral"]:
                        buro_archivo_para_analisis = ruta_absoluta
                    elif campo in ["domicilio_fisica", "domicilio_moral"]:
                        domicilio_archivo_para_analisis = ruta_absoluta

            # Si es multi-archivo, actualizamos el campo completo con la nueva lista
            if es_multi_archivo:
                update_fields[f"documentos.{campo}"] = lista_archivos_db

        if not has_files:
            raise ValueError("No se procesó ningún archivo válido.")

        # --- 4. Actualización en BD ---
        update_fields["tipo_persona"] = tipo
        update_fields["last_updated"] = datetime.utcnow()

        collection.update_one(
            {"usuario_id": self.usuario_obj},
            {"$set": update_fields, "$setOnInsert": {"usuario_id": self.usuario_obj, "created_at": datetime.utcnow()}},
            upsert=True
        )

        return {
            "success": True,
            "archivo_para_analisis": lista_estados_cuenta,
            "ine_archivos": ine_archivos_para_analisis,
            "buro_archivos": buro_archivo_para_analisis,
            "domicilio_path": domicilio_archivo_para_analisis
        }