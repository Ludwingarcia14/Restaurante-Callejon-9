import os
import json
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from bson import json_util
from config.db import db
from controllers.notificaciones.notificacion_controller import NotificacionSistemaController
import zipfile
import threading
import schedule
import time
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class BackupController:
    
    _backup_thread = None
    _backup_running = False
    
    @staticmethod
    def _validate_admin_password(password):
        """Validar contraseña de administrador para operaciones sensibles"""
        admin_password = os.environ.get('ADMIN_RESTORE_PASSWORD')
        if not admin_password:
            return True
        return password == admin_password
    
    @staticmethod
    def index():
        """Vista principal del módulo de backup con paginación"""
        backup_dir = os.path.join('static', 'backup')
        if not os.path.exists(backup_dir): 
            os.makedirs(backup_dir)
        
        all_files = []
        try:
            files_in_dir = os.listdir(backup_dir)
            all_files = sorted(
                [f for f in files_in_dir if os.path.isfile(os.path.join(backup_dir, f))],
                key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
                reverse=True
            )
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            all_files = []
        
        # --- LÓGICA DE PAGINACIÓN ---
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_files = len(all_files)
        total_pages = (total_files + per_page - 1) // per_page if total_files > 0 else 1
        
        start = (page - 1) * per_page
        end = start + per_page
        files = all_files[start:end]

        # Colecciones para el formulario
        collections = [
            "usuarios", 
            "clientes", 
            "mesas", 
            "comandas", 
            "ventas", 
            "platillos", 
            "actividad_reciente", 
            "estadisticas_diarias",
            "prestamos", 
            "pagos", 
            "configuracion", 
            "auditoria", 
            "ia_logs", 
            "notificaciones"
        ]
        
        # Obtener configuración de auto-backup
        auto_backup_config = db.configuracion.find_one({"tipo": "auto_backup"}) or {}
        
        if auto_backup_config.get('enabled'):
            BackupController._schedule_auto_backups(
                auto_backup_config.get('frequency', 'daily'),
                auto_backup_config.get('hour', '02:00')
            )
        
        return render_template(
            "admin/admin/backup.html", 
            files=files,
            collections=collections,
            page=page,
            total_pages=total_pages,
            total_files=total_files,
            auto_backup_config=auto_backup_config
        )

    @staticmethod
    def create():
        """Crear respaldo manual"""
        admin_password = request.form.get('admin_password')
        if not admin_password:
            flash("Se requiere contraseña de administrador para crear un respaldo", "error")
            return redirect(url_for('routes.admin_backup_view'))
        
        if not BackupController._validate_admin_password(admin_password):
            flash("Contraseña de administrador incorrecta", "error")
            return redirect(url_for('routes.admin_backup_view'))
        
        backup_dir = os.path.join('static', 'backup')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Captura de datos del formulario
        selected_collections = request.form.getlist('collections')
        time_range = request.form.get('time_range', 'all')
        file_format = request.form.get('format', 'json')
        custom_name = request.form.get('backup_name', 'respaldo').strip()
        
        if not custom_name: 
            custom_name = "respaldo"
        
        # Validar que se haya seleccionado al menos una colección
        if not selected_collections:
            flash("Debes seleccionar al menos una colección para respaldar", "error")
            return redirect(url_for('routes.admin_backup_view'))
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{custom_name}_{timestamp}.{file_format}"
        full_path = os.path.join(backup_dir, filename)

        try:
            backup_data = {}
            date_filter = {}

            # Filtro por rango de tiempo
            if time_range != 'all':
                days = 1 if time_range == '24h' else 7 if time_range == '7d' else 30
                limit_date = datetime.utcnow() - timedelta(days=days)
                date_filter = {"created_at": {"$gte": limit_date}}

            # Extracción de datos de MongoDB
            for col_name in selected_collections:
                try:
                    data = list(db[col_name].find(date_filter))
                    # Usamos json_util para manejar ObjectIds y Fechas de Mongo
                    backup_data[col_name] = json.loads(json_util.dumps(data))
                except Exception as col_error:
                    print(f"⚠️ Error al respaldar colección {col_name}: {col_error}")
                    backup_data[col_name] = []

            # Guardado físico del archivo
            if file_format == 'json':
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=4)
            elif file_format == 'zip':
                # Crear archivo temporal JSON
                temp_json = full_path.replace('.zip', '.json')
                with open(temp_json, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=4)
                
                # Comprimir a ZIP
                with zipfile.ZipFile(full_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(temp_json, os.path.basename(temp_json))
                
                # Eliminar temporal
                os.remove(temp_json)
            
            flash(f"Respaldo '{filename}' generado con éxito. Total de colecciones: {len(selected_collections)}", "success")
            
            try:
                NotificacionSistemaController.notificar_backup_creado(
                    usuario_id=session.get("usuario_id"),
                    nombre_archivo=filename
                )
            except Exception as notif_error:
                print(f"⚠️ Error al notificar backup: {notif_error}")
            
        except Exception as e:
            logger.error(f"❌ Error al generar respaldo: {str(e)}")
            flash("❌ Error al generar respaldo", "error")
            
            # NOTIFICAR ERROR
            try:
                NotificacionSistemaController.notificar_error(
                    usuario_id=session.get("usuario_id"),
                    tipo_error="BACKUP_ERROR",
                    descripcion="Error al generar respaldo"
                )
            except Exception as notif_error:
                print(f"⚠️ Error al notificar error: {notif_error}")

        return redirect(url_for('routes.admin_backup_view'))

    @staticmethod
    def delete_file(filename):
        """Eliminar archivo de respaldo"""
        try:
            file_path = os.path.join('static', 'backup', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash(f"✅ Archivo '{filename}' eliminado correctamente.", "success")
            else:
                flash("❌ El archivo no existe.", "error")
        except Exception as e:
            logger.error(f"Error al eliminar: {str(e)}")
            flash("❌ Error al eliminar", "error")
        return redirect(url_for('routes.admin_backup_view'))
    
    @staticmethod
    def delete_file_with_auth():
        """Eliminar archivo de respaldo con validación de contraseña"""
        # Obtener el nombre del archivo de la URL
        filename = request.view_args.get('filename', '')
        
        # Validar contraseña
        try:
            data = request.get_json()
            admin_password = data.get('admin_password') if data else None
        except:
            admin_password = None
        
        if not admin_password:
            return jsonify({
                "success": False,
                "message": "Se requiere contraseña de administrador"
            })
        
        if not BackupController._validate_admin_password(admin_password):
            return jsonify({
                "success": False,
                "message": "Contraseña de administrador incorrecta"
            })
        
        # Validar que el archivo existe
        file_path = os.path.join('static', 'backup', filename)
        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "message": "El archivo no existe"
            })
        
        try:
            os.remove(file_path)
            return jsonify({
                "success": True,
                "message": f"Archivo '{filename}' eliminado correctamente"
            })
        except Exception as e:
            logger.error(f"Error al eliminar: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            })
    
    @staticmethod
    def download_with_auth():
        """Validar contraseña antes de descargar archivo"""
        # Obtener el nombre del archivo de la URL
        filename = request.view_args.get('filename', '')
        
        # Validar contraseña
        try:
            data = request.get_json()
            admin_password = data.get('admin_password') if data else None
        except:
            admin_password = None
        
        if not admin_password:
            return jsonify({
                "success": False,
                "message": "Se requiere contraseña de administrador"
            })
        
        if not BackupController._validate_admin_password(admin_password):
            return jsonify({
                "success": False,
                "message": "Contraseña de administrador incorrecta"
            })
        
        # Validar que el archivo existe
        file_path = os.path.join('static', 'backup', filename)
        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "message": "El archivo no existe"
            })
        
        return jsonify({
            "success": True,
            "message": "Descarga autorizada"
        })

    @staticmethod
    def restore():
        """Ejecutar restauración de base de datos"""
        # Validar contraseña de administrador
        admin_password = request.form.get('admin_password')
        if not admin_password:
            flash("❌ Se requiere contraseña de administrador para restaurar un respaldo", "error")
            return redirect(url_for('routes.admin_backup_view'))
        
        if not BackupController._validate_admin_password(admin_password):
            flash("❌ Contraseña de administrador incorrecta", "error")
            return redirect(url_for('routes.admin_backup_view'))
        
        server_file = request.form.get('server_file')
        file_to_restore = None

        try:
            if server_file:
                # Restaurar desde archivo local en el servidor
                file_path = os.path.join('static', 'backup', server_file)
                
                # Si es ZIP, extraer primero
                if server_file.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        # Extraer a carpeta temporal
                        temp_dir = os.path.join('static', 'backup', 'temp')
                        os.makedirs(temp_dir, exist_ok=True)
                        zip_ref.extractall(temp_dir)
                        
                        # Buscar el archivo JSON extraído
                        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
                        if json_files:
                            json_path = os.path.join(temp_dir, json_files[0])
                            with open(json_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        else:
                            raise Exception("No se encontró archivo JSON en el ZIP")
                        
                        # Limpiar carpeta temporal
                        import shutil
                        shutil.rmtree(temp_dir)
                else:
                    # Archivo JSON directo
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
            elif 'backup_file' in request.files:
                # Restaurar desde archivo subido por el usuario
                file = request.files['backup_file']
                if file.filename == '':
                    flash("❌ No se seleccionó ningún archivo.", "error")
                    return redirect(url_for('routes.admin_backup_view'))
                
                # Leer archivo
                if file.filename.endswith('.zip'):
                    # Procesar ZIP
                    temp_dir = os.path.join('static', 'backup', 'temp_upload')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    zip_path = os.path.join(temp_dir, file.filename)
                    file.save(zip_path)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
                    if json_files:
                        with open(os.path.join(temp_dir, json_files[0]), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        raise Exception("No se encontró JSON en el ZIP")
                    
                    import shutil
                    shutil.rmtree(temp_dir)
                else:
                    # JSON directo
                    data = json.loads(file.read().decode('utf-8'))
            else:
                flash("❌ No hay origen de datos para restaurar.", "error")
                return redirect(url_for('routes.admin_backup_view'))

            # Proceso de restauración en MongoDB
            restored_collections = 0
            for col_name, documents in data.items():
                if documents:
                    try:
                        # Convertir JSON a objetos BSON (ObjectIds, Dates)
                        bson_docs = json_util.loads(json.dumps(documents))
                        db[col_name].drop()  # Limpia la colección actual
                        db[col_name].insert_many(bson_docs)
                        restored_collections += 1
                    except Exception as col_error:
                        print(f"⚠️ Error restaurando {col_name}: {col_error}")
            
            flash(f"✅ Sistema restaurado con éxito. {restored_collections} colecciones restauradas.", "success")
            
        except Exception as e:
            logger.error(f"❌ Error en la restauración: {str(e)}")
            flash("❌ Error en la restauración", "error")
            
        return redirect(url_for('routes.admin_backup_view'))
    
    @staticmethod
    def configure_auto_backup():
        """Configurar respaldos automáticos"""
        try:
            enabled = request.json.get('enabled', False)
            frequency = request.json.get('frequency', 'daily')
            hour = request.json.get('hour', '02:00')
            retention_days = request.json.get('retention_days', 30)
            
            # Guardar configuración en MongoDB
            config = {
                "tipo": "auto_backup",
                "enabled": enabled,
                "frequency": frequency,
                "hour": hour,
                "retention_days": retention_days,
                "updated_at": datetime.utcnow()
            }
            
            db.configuracion.update_one(
                {"tipo": "auto_backup"},
                {"$set": config},
                upsert=True
            )
            
            # Iniciar o detener el scheduler
            if enabled:
                BackupController._schedule_auto_backups(frequency, hour)
                message = "✅ Respaldos automáticos activados correctamente"
            else:
                BackupController._backup_running = False
                message = "✅ Respaldos automáticos desactivados"
            
            return jsonify({
                "success": True,
                "message": message
            })
            
        except Exception as e:
            logger.error(f"Error al configurar auto-backup: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def _schedule_auto_backups(frequency, hour):
        """Programar respaldos automáticos"""
        if BackupController._backup_running:
            return  # Ya está corriendo
        
        BackupController._backup_running = True
        
        def run_scheduler():
            # Limpiar trabajos anteriores
            schedule.clear()
            
            # Programar según frecuencia
            if frequency == 'daily':
                schedule.every().day.at(hour).do(BackupController._ejecutar_respaldo_automatico)
            elif frequency == 'weekly':
                schedule.every().monday.at(hour).do(BackupController._ejecutar_respaldo_automatico)
            elif frequency == 'monthly':
                schedule.every(30).days.at(hour).do(BackupController._ejecutar_respaldo_automatico)
            
            print(f"📅 Auto-backup programado: {frequency} a las {hour}")
            
            # Loop del scheduler
            while BackupController._backup_running:
                schedule.run_pending()
                time.sleep(60)  # Revisar cada minuto
        
        # Crear thread daemon
        if BackupController._backup_thread is None or not BackupController._backup_thread.is_alive():
            BackupController._backup_thread = threading.Thread(target=run_scheduler, daemon=True)
            BackupController._backup_thread.start()
            print("🤖 Thread de auto-backup iniciado")
    
    @staticmethod
    def _ejecutar_respaldo_automatico():
        """Ejecutar respaldo automático programado"""
        try:
            print("🤖 Ejecutando respaldo automático...")
            
            backup_dir = os.path.join('static', 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Obtener todas las colecciones
            collections = db.list_collection_names()
            
            # Crear respaldo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"auto_backup_{timestamp}.json"
            full_path = os.path.join(backup_dir, filename)
            
            backup_data = {}
            for col_name in collections:
                if col_name != 'configuracion':  # Excluir configuración
                    try:
                        data = list(db[col_name].find())
                        backup_data[col_name] = json.loads(json_util.dumps(data))
                    except Exception as e:
                        print(f"⚠️ Error al respaldar {col_name}: {e}")
                        backup_data[col_name] = []
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=4)
            
            print(f"✅ Respaldo automático creado: {filename}")
            
            # Limpiar respaldos antiguos
            BackupController._limpiar_respaldos_antiguos()
            
        except Exception as e:
            print(f"❌ Error en respaldo automático: {e}")
    
    @staticmethod
    def _limpiar_respaldos_antiguos():
        """Eliminar respaldos antiguos según la retención configurada"""
        try:
            config = db.configuracion.find_one({"tipo": "auto_backup"})
            if not config:
                return
            
            retention_days = config.get('retention_days', 30)
            backup_dir = os.path.join('static', 'backup')
            
            if not os.path.exists(backup_dir):
                return
            
            now = datetime.now()
            deleted_count = 0
            
            for filename in os.listdir(backup_dir):
                if filename.startswith('auto_backup_'):
                    file_path = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if (now - file_time).days > retention_days:
                        os.remove(file_path)
                        deleted_count += 1
            
            if deleted_count > 0:
                print(f"🗑️ Eliminados {deleted_count} respaldos antiguos")
                
        except Exception as e:
            print(f"Error al limpiar respaldos antiguos: {e}")