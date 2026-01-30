import os
import json
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify
from bson import json_util
from config.db import db

class BackupController:
    @staticmethod
    def index():
        backup_dir = os.path.join('static', 'backup')
        if not os.path.exists(backup_dir): 
            os.makedirs(backup_dir)
        
        # Obtener archivos reales en la carpeta
        all_files = sorted(os.listdir(backup_dir), reverse=True)
        
        # --- LÓGICA DE PAGINACIÓN ---
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_files = len(all_files)
        total_pages = (total_files + per_page - 1) // per_page if total_files > 0 else 1
        
        start = (page - 1) * per_page
        end = start + per_page
        files = all_files[start:end]

        # Colecciones para el formulario
        collections = ["usuarios", "clientes", "prestamos", "pagos", "configuracion", "auditoria", "ia_logs", "notificaciones"]
        
        return render_template("admin/admin/backup.html", 
                               files=files, 
                               collections=collections,
                               page=page,
                               total_pages=total_pages,
                               total_files=total_files)

    @staticmethod
    def create():
        backup_dir = os.path.join('static', 'backup')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Captura de datos del formulario
        selected_collections = request.form.getlist('collections')
        time_range = request.form.get('time_range', 'all')
        file_format = request.form.get('format', 'json')
        custom_name = request.form.get('backup_name', 'respaldo').strip()
        
        if not custom_name: custom_name = "respaldo"
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{custom_name}_{timestamp}.{file_format}"
        full_path = os.path.join(backup_dir, filename)

        try:
            backup_data = {}
            date_filter = {}

            # Filtro por rango de tiempo
            if time_range != 'all':
                days = 1 if time_range == '24h' else 7
                limit_date = datetime.utcnow() - timedelta(days=days)
                date_filter = {"created_at": {"$gte": limit_date}}

            # Extracción de datos de MongoDB
            for col_name in selected_collections:
                data = list(db[col_name].find(date_filter))
                # Usamos json_util para manejar ObjectIds y Fechas de Mongo
                backup_data[col_name] = json.loads(json_util.dumps(data))

            # Guardado físico del archivo
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=4)
            
            flash(f"Respaldo '{filename}' generado con éxito.", "success")
        except Exception as e:
            flash(f"Error al generar respaldo: {str(e)}", "error")

        return redirect(url_for('routes.admin_backup_view'))

    @staticmethod
    def delete_file(filename):
        try:
            file_path = os.path.join('static', 'backup', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash(f"Archivo eliminado correctamente.", "success")
            else:
                flash("El archivo no existe.", "error")
        except Exception as e:
            flash(f"Error al eliminar: {str(e)}", "error")
        return redirect(url_for('routes.admin_backup_view'))

    @staticmethod
    def restore_view():
        backup_dir = os.path.join('static', 'backup')
        files = sorted([f for f in os.listdir(backup_dir) if f.endswith(('.json', '.sql'))], reverse=True) if os.path.exists(backup_dir) else []
        return render_template("admin/admin/restore.html", files=files)

    @staticmethod
    def restore():
        # Verificamos si es un archivo subido o uno del servidor
        server_file = request.form.get('server_file')
        file_to_restore = None

        try:
            if server_file:
                # Restaurar desde archivo local en el servidor
                file_path = os.path.join('static', 'backup', server_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif 'backup_file' in request.files:
                # Restaurar desde archivo subido por el usuario
                file = request.files['backup_file']
                if file.filename == '':
                    flash("No se seleccionó ningún archivo.", "error")
                    return redirect(url_for('routes.admin_backup_restore_view'))
                data = json.loads(file.read().decode('utf-8'))
            else:
                flash("No hay origen de datos para restaurar.", "error")
                return redirect(url_for('routes.admin_backup_restore_view'))

            # Proceso de restauración en MongoDB
            for col_name, documents in data.items():
                if documents:
                    # Convertir JSON a objetos BSON (ObjectIds, Dates)
                    bson_docs = json_util.loads(json.dumps(documents))
                    db[col_name].drop() # Limpia la colección actual
                    db[col_name].insert_many(bson_docs)
            
            flash("Sistema restaurado con éxito. La base de datos ha sido actualizada.", "success")
        except Exception as e:
            flash(f"Error en la restauración: {str(e)}", "error")
            
        return redirect(url_for('routes.admin_backup_restore_view'))