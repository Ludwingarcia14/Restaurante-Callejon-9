### controllers/admin/adminController.py (Versión Completa CQRS y 2FA)

from flask import request, session, jsonify, current_app, render_template, redirect, url_for, flash
from bson.objectid import ObjectId 
from datetime import datetime
from cqrs.commands.admin.create_carousel_command import CreateCarouselCommand
from models.landing_model import LandingManager, PageManager
from models.user_model import Usuario
import re
from services.autentication.service import TwoFactorService 
from config.db import db # Necesario para la lógica original de 2FA y otras comprobaciones
from werkzeug.utils import secure_filename
import os
from werkzeug.utils import secure_filename

# 💡 IMPORTACIONES DE QUERIES (Consultas)
from cqrs.queryes.admin.get_admin_dashboard_stats_query import GetAdminDashboardStatsQuery
from cqrs.queryes.admin.get_calendar_events_query import GetCalendarEventsQuery
from cqrs.queryes.admin.get_roles_for_creation_query import GetRolesForCreationQuery
from cqrs.queryes.admin.get_users_data_query import GetUsersDataQuery
from cqrs.queryes.admin.get_user_details_query import GetUserDetailsQuery
from cqrs.queryes.admin.get_financieras_data_query import GetFinancierasDataQuery
from cqrs.queryes.admin.get_financiera_details_query import GetFinancieraDetailsQuery

# 💥 IMPORTACIONES DE COMMANDS (Acciones de escritura)
from cqrs.commands.admin.create_admin_command import CreateAdminCommand
from cqrs.commands.admin.update_user_command import UpdateUserCommand
from cqrs.commands.admin.delete_usuario_command import DeleteUserCommand
from cqrs.commands.admin.create_financiera_command import CreateFinancieraCommand
from cqrs.commands.admin.update_financiera_command import UpdateFinancieraCommand
from cqrs.commands.admin.delete_financiera_command import DeleteFinancieraCommand
from cqrs.commands.admin.create_client_command import CreateClientCommand


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

class adminController:
# =========================================================================
    # 🏠 VISTAS Y QUERIES DE DASHBOARD / ESTADÍSTICAS
    # =========================================================================

    @staticmethod
    def dashboard():
        if "usuario_id" not in session:
            return "No autorizado", 401
        return render_template("admin/dashboard.html")

    @staticmethod
    def dashboard_stats():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # 💡 QUERY
        data, error = GetAdminDashboardStatsQuery.execute()
        
        if error:
            current_app.logger.error(f"Error en dashboard_stats: {error}")
            return jsonify({"error": "Error al cargar estadísticas."}), 500
            
        return jsonify(data)
    
    # =========================================================================
    # ⚙️ GESTIÓN DE SEGURIDAD (SETTINGS / 2FA) - Lógica Original
    # =========================================================================
    
    @staticmethod
    def settings():
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))

        user_id = session["usuario_id"]
        # QUERY directa al Modelo
        user = Usuario.find_by_id(user_id)
        
        if not user:
            return "Usuario no encontrado", 404
            
        return render_template(
            "admin/config/config.html", 
            is_2fa_active=user.two_factor_enabled if hasattr(user, 'two_factor_enabled') else False
        )
        
    @staticmethod
    def generate_2fa_setup():
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 401
        
        user_id = session["usuario_id"]
        user = Usuario.find_by_id(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'Usuario no encontrado'}), 404
            
        tipo = request.json.get('tipo', 'app')
        print(f"Generando 2FA para tipo: {tipo}")

        if tipo == 'app':
            secret_key = TwoFactorService.generate_secret_key()
            username = user.get('usuario_email')
            if not username:
                return jsonify({'status': 'error', 'message': 'Email no disponible.'}), 400

            provisioning_uri = TwoFactorService.get_provisioning_uri(username, secret_key)
            qr_base64 = TwoFactorService.generate_qr_code(provisioning_uri)
            
            session['temp_2fa_secret'] = secret_key
            session['temp_2fa_tipo'] = 'app'
            
            return jsonify({
                'status': 'success',
                'secret_key': secret_key,
                'qr_image': f"data:image/png;base64,{qr_base64}", 
                'tipo': 'app'
            })
        elif tipo == 'sms':
            telefono = user.get('usuario_telefono') 
            if not telefono:
                return jsonify({'status': 'error', 'message': 'Número de teléfono requerido.'}), 400

            sms_code = TwoFactorService.generate_email_code()
            
            session['temp_2fa_secret'] = sms_code
            session['temp_2fa_tipo'] = 'sms'
            session['temp_2fa_telefono'] = telefono
            
            print(f"DEBUG: Enviando código SMS {sms_code} al número: {telefono}")
            
            return jsonify({
                'status': 'success',
                'message': 'Código de verificación enviado por SMS.',
                'tipo': 'sms'
            })
        elif tipo == 'email':
            email_destino = user.get('usuario_email')
            if not email_destino:
                return jsonify({'status': 'error', 'message': 'El correo electrónico no está disponible.'}), 400

            email_code = TwoFactorService.generate_email_code()
            
            session['temp_2fa_secret'] = email_code
            session['temp_2fa_tipo'] = 'email'
            session['temp_2fa_email'] = email_destino

            print(f"DEBUG: Enviando código de email {email_code} al correo: {email_destino}")
            
            return jsonify({
                'status': 'success',
                'message': f'Código de verificación enviado a {email_destino}.',
                'tipo': 'email'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Tipo de 2FA no válido.'}), 400

    @staticmethod
    def verify_and_enable_2fa():
        # --- Función auxiliar interna para limpiar datos de Mongo ---
        def preparar_respuesta(doc):
            if not doc: return None
            doc_limpio = doc.copy()
            for key, value in doc_limpio.items():
                if isinstance(value, ObjectId):
                    doc_limpio[key] = str(value)
                elif isinstance(value, datetime):
                    doc_limpio[key] = value.isoformat()
            return doc_limpio
        # ------------------------------------------------------------

        if "usuario_id" not in session:
              return jsonify({'status': 'error', 'message': 'Sesión no válida.'}), 401

        user_id = session["usuario_id"]
        data = request.json or {}
        
        otp_code = data.get('otp_code') or data.get('code')
        secret_key = session.get('temp_2fa_secret') or data.get('temp_2fa_secret')
        tipo = session.get('temp_2fa_tipo') or data.get('temp_2fa_tipo')
        telefono_to_save = session.get('temp_2fa_telefono')
        Metodo = data.get('metodo')
        email = data.get('email')

        if not secret_key or not otp_code or not tipo:
            return jsonify({'status': 'error', 'message': 'Datos faltantes.'}), 400

        is_valid = False
        secret_to_save = None
        telefono_final = None

        if tipo == 'app':
            is_valid = TwoFactorService.verify_code(secret_key, otp_code)
            if is_valid: secret_to_save = secret_key
        elif tipo == 'sms' or tipo == 'email':
            is_valid = (str(otp_code) == str(secret_key))
            if is_valid and tipo == 'sms': telefono_final = telefono_to_save

        if not is_valid:
              return jsonify({'status': 'error', 'message': 'Código inválido.'}), 401
              
        # Lógica Movil (Utiliza db directamente)
        if Metodo == "movil":
            user_data = db.usuarios.find_one({"usuario_email": email})
            if user_data:
                result = Usuario.update_2fa_status(
                     user_id=user_id, is_enabled=True, tipo=tipo, 
                     secret=secret_to_save, telefono=telefono_final
                )
                session.pop('temp_2fa_secret', None); session.pop('temp_2fa_tipo', None); session.pop('temp_2fa_telefono', None)
                if result and result.modified_count == 1:
                    data_final = preparar_respuesta(user_data)
                    return jsonify({'status': 'success', 'message': '2FA activado.', "data": data_final})
            else:
                client_data = db.clientes.find_one({"usuario_email": email})
                if client_data:
                    result = Usuario.update_2fa_status(
                         user_id=user_id, is_enabled=True, tipo=tipo, 
                         secret=secret_to_save, telefono=telefono_final
                    )
                    session.pop('temp_2fa_secret', None); session.pop('temp_2fa_tipo', None); session.pop('temp_2fa_telefono', None)
                    if result and result.modified_count == 1:
                         data_final = preparar_respuesta(client_data)
                         return jsonify({'status': 'success', 'message': '2FA activado.', "data": data_final})
                
            return jsonify({'status': 'error', 'message': 'Error DB o usuario no encontrado.'}), 500
        
        else: # Caso Web normal
            result = Usuario.update_2fa_status(
                 user_id=user_id, is_enabled=True, tipo=tipo, 
                 secret=secret_to_save, telefono=telefono_final
            )
            session.pop('temp_2fa_secret', None); session.pop('temp_2fa_tipo', None); session.pop('temp_2fa_telefono', None)
            if result and result.modified_count == 1:
                 return jsonify({'status': 'success', 'message': '2FA activado.'})
            else:
                 return jsonify({'status': 'error', 'message': 'Error DB.'}), 500

    @staticmethod
    def disable_2fa():
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

        user_id = session["usuario_id"]
        
        result = Usuario.update_2fa_status(
             user_id=user_id, is_enabled=False, tipo=None, secret=None, telefono=None
        )
        
        if result and result.modified_count == 1:
            return jsonify({'status': 'success', 'message': '2FA desactivado correctamente.'})
        else:
            return jsonify({'status': 'error', 'message': 'Error de base de datos al desactivar 2FA.'}), 500


    # =========================================================================
    # 📆 CALENDARIO (QUERY)
    # =========================================================================

    @staticmethod
    def calendar():
        if "usuario_id" not in session:
            return "No autorizado", 401
        return render_template("admin/calendario.html")

    @staticmethod
    def eventos_calendar():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        # 💡 QUERY
        eventos, error = GetCalendarEventsQuery.execute()
        
        if error:
            current_app.logger.error(f"Error al cargar eventos: {error}")
            return jsonify({"error": "Error al cargar eventos."}), 500
            
        return jsonify(eventos)


    # =========================================================================
    # 👥 GESTIÓN DE ADMINISTRADORES (USUARIOS DE PLATAFORMA)
    # =========================================================================

    @staticmethod
    def viewsAdmin():
        if "usuario_id" not in session:
            return render_template("errors/401.html"), 401
        return render_template("admin/admin/lista.html")

    @staticmethod
    def get_usuarios_data():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")
        
        # 💡 QUERY
        data_tables_response, error = GetUsersDataQuery.execute(draw, start, length, search_value)

        if error:
            current_app.logger.error(f"Error al obtener datos de usuarios: {error}")
            return jsonify({"error": "Error al cargar datos de usuarios."}), 500

        return jsonify(data_tables_response)

    @staticmethod
    def create_admin():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # 💡 QUERY
        roles, error = GetRolesForCreationQuery.execute()

        if error:
            flash(f"Error al cargar roles: {error}", "error")
            roles = [] 

        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return render_template(
            "admin/admin/administradores.html",
            roles=roles,
            current_date=current_date
        )
        
    @staticmethod
    def create_admin_post():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # 💥 COMMAND
        command = CreateAdminCommand(data)
        success, response = command.execute()
        
        if success:
            return jsonify(response), 200
        else:
            status_code = 400 if "obligatorio" in response or "válido" in response else 500
            return jsonify({"error": response}), status_code

    @staticmethod
    def view_usuario(usuario_id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        # 💡 QUERY
        usuario, error = GetUserDetailsQuery.execute(usuario_id)
        
        if error == "ID de usuario inválido." or error == "Usuario no encontrado.":
            return jsonify({"error": error}), 404
        elif error:
            current_app.logger.error(f"Error al ver usuario: {error}")
            return jsonify({"error": "Error de base de datos."}), 500

        return jsonify(usuario)

    @staticmethod
    def edit_usuario(usuario_id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
            
        data = request.json
        
        # 💥 COMMAND
        command = UpdateUserCommand(usuario_id, data)
        success, error = command.execute()
        
        if success:
            return jsonify({"success": True})
        else:
            status_code = 400 if "inválido" in error or "no encontrado" in error else 500
            return jsonify({"error": error}), status_code

    @staticmethod
    def delete_usuario(usuario_id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        # 💥 COMMAND
        command = DeleteUserCommand([usuario_id])
        success, deleted_count, error = command.execute_single()
        
        if success:
            return jsonify({"success": True, "deleted_count": deleted_count})
        else:
            status_code = 400 if "inválido" in error else 500
            return jsonify({"error": error}), status_code

    @staticmethod
    def delete_usuarios_batch():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        ids = request.json.get("ids", [])
        
        # 💥 COMMAND
        command = DeleteUserCommand(ids)
        success, deleted_count, error = command.execute_batch()
        
        if success:
            return jsonify({"success": True, "deleted_count": deleted_count})
        else:
            status_code = 400 if "inválido" in error else 500
            return jsonify({"error": error}), status_code


    # =========================================================================
    # 🏦 GESTIÓN DE FINANCIERAS
    # =========================================================================
    
    @staticmethod
    def createViewFinanciera():
        if "usuario_id" not in session:
            return "No autorizado", 401
        return render_template("admin/financieras/financieras.html")

    @staticmethod
    def financieras_store():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        data = request.form.to_dict()

        # 💥 COMMAND
        command = CreateFinancieraCommand(data)
        success, response, error = command.execute()

        if success:
            return jsonify(response), 201
        else:
            status_code = 400 if "obligatorio" in error or "existe" in error else 500
            return jsonify({"success": False, "error": error}), status_code

    @staticmethod
    def financieras_data():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")
        
        # 💡 QUERY
        data_tables_response, error = GetFinancierasDataQuery.execute(draw, start, length, search_value)

        if error:
            current_app.logger.error(f"Error al obtener datos de financieras: {error}")
            return jsonify({"error": "Error al cargar datos de financieras."}), 500

        return jsonify(data_tables_response)

    @staticmethod
    def financieras_view_list():
        if "usuario_id" not in session:
            return "No autorizado", 401
        return render_template("admin/financieras/lista.html")
    
    @staticmethod
    def financieras_view(id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        # 💡 QUERY
        financiera, error = GetFinancieraDetailsQuery.execute(id)
        
        if error == "ID de financiera inválido." or error == "Financiera no encontrada.":
            return jsonify({"error": error}), 404
        elif error:
            current_app.logger.error(f"Error al ver financiera: {error}")
            return jsonify({"error": "Error de base de datos."}), 500
            
        return jsonify(financiera)

    @staticmethod
    def financieras_edit(id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
            
        data = request.get_json()
        
        # 💥 COMMAND
        command = UpdateFinancieraCommand(id, data)
        success, error = command.execute()
        
        if success:
            return jsonify({"success": True, "message": "Financiera actualizada"})
        else:
            status_code = 400 if "inválido" in error or "no encontrado" in error else 500
            return jsonify({"error": error}), status_code

    @staticmethod
    def financieras_delete(id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        
        # 💥 COMMAND
        command = DeleteFinancieraCommand([id])
        success, deleted_count, error = command.execute_single()
        
        if success:
            return jsonify({"success": True, "message": "Financiera eliminada"})
        else:
            status_code = 400 if "inválido" in error else 500
            return jsonify({"error": error}), status_code

    @staticmethod
    def financieras_delete_batch():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
            
        ids = request.json.get("ids", [])
        
        # 💥 COMMAND
        command = DeleteFinancieraCommand(ids)
        success, deleted_count, error = command.execute_batch()
        
        if success:
            return jsonify({"success": True, "message": "Financieras eliminadas"})
        else:
            status_code = 400 if "inválido" in error else 500
            return jsonify({"error": error}), status_code

    # =========================================================================
    # 🤖 VISTAS DE IA
    # =========================================================================

    @staticmethod
    def view_chat_ia():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "1":
            return render_template("admin/ia/chat_ia.html")
        return redirect(url_for("routes.login"))

    @staticmethod
    def view_estados_cuenta_ia():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "1":
            return render_template("admin/ia/estados_cuenta.html")
        return redirect(url_for("routes.login"))

    # =========================================================================
    # 👤 GESTIÓN DE CLIENTES (Desde Admin)
    # =========================================================================

    @staticmethod
    def crear_cliente():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # 💡 QUERY
        roles, error = GetRolesForCreationQuery.execute()
        
        if error:
            flash(f"Error al cargar roles: {error}", "error")
            roles = []
            
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return render_template(
            "admin/client/clientes.html",
            roles=roles,
            current_date=current_date
        )

    @staticmethod
    def dashboardA_client_list():
        if "usuario_id" not in session:
            return "No autorizado", 401
        return render_template("admin/client/lista.html")


    @staticmethod
    def create_client_saved():
        """
        Ruta para crear un cliente (POST /dashboard/client/create).
        Delega la lógica de validación y persistencia al CreateClientCommand.
        """
        # 1. Verificar sesión
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # 2. Obtener datos del formulario (soporta form-data y JSON)
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # 💥 COMMAND
        # Invoca el Command. Toda la lógica de validación, UUID y guardado está aquí.
        command = CreateClientCommand(data)
        success, response = command.execute() 
        
        if success:
            # response contiene {success: True, cliente_id: ...}
            return jsonify(response), 201
        else:
            # response contiene el mensaje de error de validación/DB
            status_code = 400 if "obligatorio" in response or "válido" in response or "existe" in response else 500
            return jsonify({"error": response}), status_code

    @staticmethod
    def viewCreateCarousel():
        if "usuario_id" not in session:
            return "No autorizado", 401
        return render_template("admin/web/carusel/carousel.html")
    
    @staticmethod
    def carousel_create():
        try:
            # 1. Recoger datos del formulario
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion')
            btn_texto = request.form.get('btn_texto')
            btn_link = request.form.get('btn_link') # La URL generada: /landing/expo/titulo
            tipo = request.form.get('tipo') # expo, caravana o publicacion

            # 2. Manejo de la Imagen
            file = request.files.get('imagen')
            if not file:
                return jsonify({"success": False, "error": "La imagen es obligatoria"}), 400

            filename = secure_filename(file.filename)
            # Ruta donde guardas las imágenes del carrusel
            upload_path = os.path.join('static', 'uploads', 'carousel', filename)
            
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            file.save(upload_path)

            # 3. Preparar objeto para MongoDB
            new_entry = {
                "titulo": titulo,
                "descripcion": descripcion,
                "btn_texto": btn_texto,
                "btn_link": btn_link,
                "tipo": tipo,
                "imagen_url": f"/static/uploads/carousel/{filename}",
                "activo": True
            }

            # 4. Guardar en BD
            LandingManager.create_publication(new_entry)

            return jsonify({"success": True, "message": "Publicación creada correctamente"}), 201

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        
    @staticmethod
    def viewlistcarousel():
        # 🔐 Seguridad: validar sesión
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))

        try:
            # 📦 Obtener registros del carrusel
            carouseles = LandingManager.get_all()

            return render_template(
                "admin/web/carusel/lista_carusel.html",
                carouseles=carouseles
            )

        except Exception as e:
            print(f"Error al cargar carrusel: {e}")
            return render_template(
                "admin/web/carusel/lista_carusel.html",
                carouseles=[]
            )
    
    @staticmethod
    def carousel_show(id):
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
            
        try:
            # Obtener el documento de MongoDB
            carousel = LandingManager.get_by_id(id)
            if not carousel:
                return jsonify({"success": False, "error": "No encontrado"}), 404
            
            # Preparar datos para JSON (convertir ObjectId y Datetime a string)
            data = {
                "id": str(carousel["_id"]),
                "titulo": carousel.get("titulo", "Sin título"),
                "descripcion": carousel.get("descripcion", ""),
                "tipo": carousel.get("tipo", "general"),
                "imagen": carousel.get("imagen_url", ""),
                "btn_texto": carousel.get("btn_texto", ""),
                "btn_link": carousel.get("btn_link", "#"),
                "activo": carousel.get("activo", False)
            }
            return jsonify({"success": True, "data": data})

        except Exception as e:
            print(f"Error JSON Carousel: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @staticmethod
    def carousel_edit(id):
        # 🔐 Seguridad: validar sesión
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))

        try:
            # 📦 Obtener registro por ID
            carousel = LandingManager.get_by_id(id)
            if not carousel:
                return "Carrusel no encontrado", 404

            return render_template(
                "admin/web/carusel/edit_carusel.html",
                carousel=carousel
            )

        except Exception as e:
            print(f"Error al cargar carrusel para edición: {e}")
            return "Error al cargar carrusel", 500
    
    @staticmethod
    def carousel_deleted(carousel_id):
        # 🔐 Seguridad: validar sesión
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))

        try:
            # 📦 Eliminar registro por ID
            result = LandingManager.delete(carousel_id)
            if result.deleted_count == 0:
                return jsonify({"success": False, "error": "Carrusel no encontrado"}), 404

            return jsonify({"success": True, "message": "Carrusel eliminado correctamente"}), 200

        except Exception as e:
            print(f"Error al eliminar carrusel: {e}")
            return jsonify({"success": False, "error": "Error al eliminar carrusel"}), 500
        
    @staticmethod
    def index():
        """Muestra la lista de todas las páginas creadas"""
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))
            
        paginas = PageManager.get_all()
        return render_template("admin/web/pages_list.html", paginas=paginas)

    @staticmethod
    def create_initial():
        """
        Crea el registro inicial (esqueleto) en la BD.
        Recibe JSON: { "titulo": "...", "tipo": "..." }
        Retorna: { "success": True, "redirect_url": "..." } para ir al editor.
        """
        if "usuario_id" not in session:
            return jsonify({"success": False, "error": "No autorizado"}), 401

        try:
            data = request.get_json() if request.is_json else request.form
            
            titulo = data.get('titulo')
            tipo = data.get('tipo') # expo, caravana, noticia

            if not titulo:
                return jsonify({"success": False, "error": "El título es obligatorio"}), 400

            # Creamos el documento base en Mongo
            result = PageManager.create_skeleton({
                "titulo": titulo, 
                "tipo": tipo,
                # Puedes agregar descripción si viene en el form
                "descripcion": data.get('descripcion', '') 
            })
            
            new_id = str(result.inserted_id)

            # Generamos la URL del editor para que el JS redirija allí
            return jsonify({
                "success": True, 
                "message": "Página creada, redirigiendo al editor...",
                "redirect_url": url_for('routes.admin_page_editor', page_id=new_id)
            }), 201

        except Exception as e:
            print(f"Error creating page: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # =========================================================================
    # 🎨 EDITOR DRAG & DROP (Paso 2)
    # =========================================================================


    @staticmethod
    def editor_view(page_id=None):
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))

        page = None

        # CASO 1: Búsqueda por ID directo
        if page_id:
            page = PageManager.get_by_id(page_id)

        # CASO 2: Búsqueda inteligente por Slug/Link
        elif request.args.get('slug') and request.args.get('tipo'):
            raw_slug = request.args.get('slug')
            tipo = request.args.get('tipo')
            slug = raw_slug 

            # A) Verificar coincidencia con Carruseles existentes
            carruseles = LandingManager.get_all()
            encontrado_en_bd = False

            for item in carruseles:
                btn_link = item.get('btn_link')
                if btn_link and btn_link == raw_slug:
                    # Descomponer URL (ej: /landing/expo/mi-evento -> mi-evento)
                    if '/' in btn_link:
                        parts = btn_link.strip().rstrip('/').split('/')
                        # Tomamos el 4to segmento (índice 3) o el último disponible
                        if len(parts) >= 4:
                            slug = parts[3]
                        elif len(parts) > 0:
                            slug = parts[-1]
                        encontrado_en_bd = True
                        break 

            # B) Fallback: Si no está en BD, limpiar la URL manualmente
            if not encontrado_en_bd and raw_slug and '/' in raw_slug:
                parts = raw_slug.strip().rstrip('/').split('/')
                if len(parts) >= 4:
                    slug = parts[3]
                elif len(parts) > 0:
                    slug = parts[-1]

            # C) Buscar la página en Mongo
            page = PageManager.collection.find_one({"tipo": tipo, "slug": slug})

            # D) AUTO-CREACIÓN: Si no existe, la creamos al vuelo
            if not page:
                titulo_provisional = slug.replace("-", " ").title()
                new_data = {
                    "titulo": titulo_provisional,
                    "tipo": tipo,
                    "slug": slug
                }
                # Usamos create_skeleton para insertar
                result = PageManager.create_skeleton(new_data)
                
                # Preparamos el objeto para la vista
                new_data["_id"] = result.inserted_id
                new_data["contenido"] = []
                page = new_data

        if not page:
            return "Error: No se pudo cargar el editor.", 404
            
        return render_template("admin/web/builder/page_builder.html", page=page)

    # =========================================================================
    # 💾 GUARDAR DISEÑO (POST)
    # =========================================================================
    @staticmethod
    def save_design(page_id):
        if "usuario_id" not in session:
            return jsonify({"success": False, "error": "No autorizado"}), 401

        try:
            data = request.get_json()
            
            # GrapesJS nos enviará estos datos desde el frontend
            update_data = {
                # 'gjs-assets', 'gjs-components', 'gjs-styles' vienen dentro de projectData
                "gjs_data": data.get('projectData'), 
                "html_content": data.get('html'),
                "css_content": data.get('css'),
                "activo": True,
                "updated_at": datetime.utcnow()
            }
            
            PageManager.collection.update_one(
                {"_id": ObjectId(page_id)},
                {"$set": update_data}
            )
            
            return jsonify({"success": True, "message": "Diseño guardado exitosamente"})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        
    @staticmethod
    def update(carousel_id):
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))
            
        try:
            # 1. Recoger datos del formulario
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion')
            btn_texto = request.form.get('btn_texto')
            btn_link = request.form.get('btn_link')
            tipo = request.form.get('tipo')
            # Checkbox: si está marcado viene como 'on', si no, None
            activo = True if request.form.get('activo') else False

            data = {
                "titulo": titulo,
                "descripcion": descripcion,
                "btn_texto": btn_texto,
                "btn_link": btn_link,
                "tipo": tipo,
                "activo": activo
            }

            # 2. Manejo de Imagen (Solo si se sube una nueva)
            file = request.files.get('imagen')
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Guardamos en static/uploads/carousel/
                upload_path = os.path.join('static', 'uploads', 'carousel', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                
                # Guardamos la ruta relativa para usarla con url_for('static', filename=...)
                data["imagen"] = f"uploads/carousel/{filename}"

            # 3. Llamada al Modelo (Método que acabamos de crear)
            LandingManager.update(carousel_id, data)

            flash("Publicación actualizada correctamente", "success")
            return redirect(url_for('routes.viewlistcarousel'))

        except Exception as e:
            current_app.logger.error(f"Error al actualizar carrusel: {e}")
            flash(f"Error al actualizar: {str(e)}", "error")
            return redirect(url_for('routes.carousel_edit', id=carousel_id))