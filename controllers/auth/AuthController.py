from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models.user_model import Usuario
import bcrypt, secrets
from models.clienteModel import Cliente
import logging, os, secrets
from dotenv import load_dotenv
from config.db import db
import os, requests

# ===================================================================
# 🚨 AJUSTE DE IMPORTACIONES CQRS (RUTAS NUEVAS) 🚨
# Las importaciones son relativas al punto de ejecución o absolutas desde la raíz si __init__.py existe.
# Asumimos que la carpeta 'api' es reconocida y se puede importar 'cqrs' desde ahí.
# ===================================================================

# Queries/Services
from cqrs.queryes.auth.handlers.auth_query_handler import AuthQueryHandler
from cqrs.commands.services.recaptcha_service import RecaptchaService # Usamos el servicio del módulo commands

# Commands
from cqrs.commands.auth.models.register_client_command import RegisterClientCommand
from cqrs.commands.auth.handlers.register_client_handler import RegisterClientCommandHandler
from cqrs.commands.auth.handlers.login_status_handler import LoginStatusHandler
from cqrs.commands.auth.handlers.logout_status_handler import LogoutStatusHandler

# ===================================================================

SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("pymongo").setLevel(logging.WARNING)

class AuthController:
    
    # --- QUERY & COMMAND: LOGIN ---
    @staticmethod
    def login():
        errors = []
        if request.method == "POST":
            data = request.get_json()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            recaptcha_response = data.get("g_recaptcha_response")

            # 1. Validar reCAPTCHA v3 (Sin cambios)
            if not recaptcha_response:
                errors.append("Por favor completa la verificación de seguridad")
            else:
                payload = {
                    "secret": SECRET_KEY,
                    "response": recaptcha_response,
                    "remoteip": request.remote_addr
                }
                try:
                    response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
                    result = response.json()
                    success = result.get("success", False)
                    score = result.get("score", 0)

                    if not success or score < 0.5:
                        errors.append("No se pasó la verificación de seguridad")
                except Exception as e:
                    logging.exception(f"Error al verificar reCAPTCHA: {e}")
                    errors.append("Error interno al verificar la verificación de seguridad")

            # Si hay errores de reCAPTCHA, salir temprano
            if errors:
                return jsonify({
                    "status": "error",
                    "message": errors[0] # Devolver el primer error
                })

            # 2. Buscar al usuario en ambas colecciones
            authenticated_user = None
            user_type = None
            
            user_doc = Usuario.find_by_email(email)
            if user_doc:
                authenticated_user = user_doc
                user_type = "usuario"
            else:
                cliente_doc = Cliente.find_by_email(email)
                if cliente_doc:
                    authenticated_user = cliente_doc
                    user_type = "cliente"

            # 3. Validar credenciales (ahora de forma genérica)
            if not authenticated_user:
                errors.append("Credenciales incorrectas")
            else:
                # Determinar los nombres de campo correctos según el tipo
                if user_type == "usuario":
                    status_field = "usuario_status"
                    clave_field = "usuario_clave"
                    rol_field = "usuario_rol"
                else: # user_type == "cliente"
                    status_field = "cliente_status"
                    clave_field = "cliente_clave"
                    rol_field = "cliente_rol"

                # Validar status
                if str(authenticated_user.get(status_field)) == "1":
                    errors.append("La cuenta está siendo usada actualmente. Cierra la sesión anterior antes de ingresar.")
                else:
                    # Validar contraseña
                    stored_hash = authenticated_user.get(clave_field)
                    if not stored_hash:
                        errors.append("Este usuario no tiene contraseña configurada")
                    else:
                        try:
                            stored_hash_bytes = stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash
                            password_bytes = password.encode("utf-8")
                            if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
                                errors.append("Credenciales incorrectas")
                        except Exception as e:
                            logging.exception(f"Error al verificar contraseña: {e}")
                            errors.append("Error interno al verificar la contraseña")

            # 4. Si hay errores (de credenciales o status), retornarlos
            if errors:
                for err in errors:
                    flash(err, "error") # flash sigue siendo útil si recargas la página
                return jsonify({
                    "status": "error",
                    "message": errors[0] # Devolver el primer error
                })

            # 5. ✅ Todo válido, generar sesión (Lógica separada)
            token_session = secrets.token_urlsafe(32)
            user_id = authenticated_user["_id"]
            
            # Datos para la respuesta JSON
            json_user_data = {}
            
            if user_type == "usuario":
                # --- Lógica para USUARIO ---
                Usuario.update(user_id, {
                    "usuario_tokensession": token_session, 
                    "usuario_status": 1
                })
                
                # Poblar la sesión
                session["user_type"] = "usuario"
                session["usuario_id"] = str(user_id)
                session["usuario_nombre"] = authenticated_user["usuario_nombre"]
                session["usuario_apellidos"] = authenticated_user["usuario_apellidos"]
                session["usuario_rol"] = authenticated_user["usuario_rol"]
                session["usuario_foto"] = authenticated_user["usuario_foto"]
                session["usuario_tokensession"] = token_session 
                session["usuario_idFinanciera"] = authenticated_user["usuario_idFinanciera"]
                #session["tipo_persona"] = authenticated_user["usuario_idFinanciera"]
                session["theme"] = 'light'
                
                # 2FA (Solo para Usuario)
                session["2fa_tipo"] = authenticated_user.get("2fa_tipo")
                session["2fa_secret"] = authenticated_user.get("2fa_secret")
                session["2fa_enabled"] = authenticated_user.get("2fa_enabled", False)
                session["2fa_telefono"] = authenticated_user.get("2fa_telefono")

                # Datos 2FA para la respuesta JSON
                json_user_data = {
                    "tipo": authenticated_user.get("2fa_tipo"),
                    "secret": authenticated_user.get("2fa_secret"),
                    "requires_2fa": authenticated_user.get("2fa_enabled", False),
                    "telefono": authenticated_user.get("2fa_telefono")
                }

            else:
                # --- Lógica para CLIENTE ---
                Cliente.update(user_id, {
                    "cliente_tokensession": token_session, 
                    "cliente_status": 1
                })
                
                # Poblar la sesión (mapeando a los mismos nombres de clave)
                session["user_type"] = "cliente"
                session["usuario_id"] = str(user_id)
                session["usuario_nombre"] = authenticated_user["cliente_nombre"]
                session["usuario_apellidos"] = authenticated_user["cliente_apellidos"]
                session["usuario_rol"] = authenticated_user["cliente_rol"]
                session["usuario_foto"] = authenticated_user.get("cliente_url") # Usar 'cliente_url' o 'None'
                session["usuario_tokensession"] = token_session 
                session["usuario_idFinanciera"] = authenticated_user["cliente_idFinanciera"]
                session["theme"] = 'light'
                
                # 2FA (Clientes no tienen, poner defaults)
                session["2fa_tipo"] = None
                session["2fa_secret"] = None
                session["2fa_enabled"] = False
                session["2fa_telefono"] = None

                # Datos 2FA para la respuesta JSON (default)
                json_user_data = {
                    "tipo": None,
                    "secret": None,
                    "requires_2fa": False,
                    "telefono": None
                }

            # 6. Mapear rol → endpoint (Ahora usa 'authenticated_user' y 'rol_field')
            rol_endpoints = {
                "1": "dashboard_Sadmin",
                "2": "dashboard_admin",
                "3": "dashboard_asesor",
                "4": "dashboard_client",
                "5": "dashboard_financiera",
                "6": "dashboard_soporte"
            }

            user_rol = str(authenticated_user.get(rol_field))
            endpoint = rol_endpoints.get(user_rol)
            
            if endpoint:
                print(f"[DEBUG] Redirigiendo al endpoint: {endpoint} (Tipo: {user_type})")
                logging.debug(f"Redirigiendo al endpoint: {endpoint} (Tipo: {user_type})")
                
                return jsonify({
                    "dashboard": url_for(f"routes.{endpoint}"),
                    "status": "success",
                    "user": json_user_data # Usamos los datos 2FA que preparamos
                })
            else:
                flash("Rol no reconocido", "error")
                return jsonify({
                    "status": "error",
                    "message": "Rol no reconocido"
                })

        # Si no es POST (esto es por si tienes un render_template para GET)
        # Si esta función es solo para API, puedes eliminar este 'else'
        else:
            return jsonify({"status": "error", "message": "Método no permitido"}), 405 

    # --- COMMAND: LOGOUT ---
    @staticmethod
    def logout():
        user_id = session.get("usuario_id")
        user_type = session.get("user_type") 

        if user_id and user_type:
            try:
                # Actualizar status a OFFLINE (COMMAND)
                LogoutStatusHandler.handle(user_id, user_type, Usuario, Cliente)
            except Exception as e:
                logging.error(f"Error al actualizar estado en logout: {e}")

        session.clear() 
        return render_template("login.html")

    # --- COMMAND: ENABLE 2FA ---
    @staticmethod
    def enable_2fa():
        if session.get("user_type") != "usuario" or not session.get("usuario_id"):
            return jsonify({"status": "error", "message": "No autorizado para esta acción"}), 403
        
        # TEMPORAL: Esto debe delegarse a Enable2FAHandler
        return jsonify({"status": "success", "message": "2FA logic handled by controller (TEMP)"}) 


    # --- COMMAND: REGISTRO DE CLIENTE ---
    @staticmethod
    def register_client_saved():
        if request.method == 'GET':
            # Muestra la plantilla de registro
            return render_template('auth/register_client.html', site_key=SITE_KEY)
        
        # ----------------------------------------------------------------------
        # 1. RECUPERAR DATOS Y ASESOR_ID DEL FORMULARIO (POST)
        # ----------------------------------------------------------------------
        # Captura el asesorID enviado por el campo oculto del formulario.
        # Si el campo no existe o está vacío, asesor_id será None (o "")
        asesor_id = request.form.get('asesorID', "").strip()
        
        # Imprime logs de depuración unificados
        print("[DEBUG] Iniciando registro de cliente vía CQRS...")
        print(f"[DEBUG] Datos recibidos: {request.form}")
        if asesor_id:
            print(f"[DEBUG] Registro referido por asesorID: {asesor_id}")
        else:
            print("[DEBUG] Registro sin asesorID de referencia.")
        
        # ----------------------------------------------------------------------
        # 2. CREAR EL OBJETO COMMAND (DTO) DE MANERA UNIFICADA
        # ----------------------------------------------------------------------
        try:
            command = RegisterClientCommand(
                nombre=request.form.get('cliente_nombre', "").strip(),
                apellidos=request.form.get('cliente_apellidos', "").strip(),
                email=request.form.get('cliente_email', "").strip().lower(),
                telefono=request.form.get('cliente_telefono', "").strip(),
                fecha_nac=request.form.get('cliente_fechaN', "").strip(),
                password=request.form.get('cliente_clave', ""),
                password_confirm=request.form.get('cliente_clave_confirm', ""),
                recaptcha_response=request.form.get("g-recaptcha-response"),
                remote_addr=request.remote_addr,
                cliente_idFinanciera=0, # Valor por defecto

                # ¡CRUCIAL! Pasar el ID del asesor al Command (aunque sea vacío o None)
                asesor_id=asesor_id 
            )
        except Exception as e:
            # Esto captura errores si la clase RegisterClientCommand falla en la inicialización
            return jsonify({"success": False, "errors": [f"Error al crear el comando: {str(e)}"]}), 400

        # ----------------------------------------------------------------------
        # 3. EJECUTAR EL COMMAND HANDLER
        # ----------------------------------------------------------------------
        try:
            # Pasa db y Cliente al Handler, junto con el asesor_id. 
            # El Handler manejará la lógica de balanceo si asesor_id es inválido/vacío.
            RegisterClientCommandHandler.handle(command, db, Cliente, asesor_id=asesor_id)
            
            # Respuesta exitosa
            return jsonify({
                "success": True, 
                "message": "¡Registro completado! Tu cuenta ha sido creada.",
                "redirect_url": url_for('routes.login_client') 
            }), 200

        except ValueError as e:
            # Errores de validación capturados desde el Handler (ej. contraseñas, email existente)
            errors = [str(e)]
            return jsonify({"success": False, "errors": errors}), 400
            
        except Exception as e:
            # Errores fatales (conexión a DB, errores inesperados)
            logging.exception(f"Error fatal en registro: {e}")
            return jsonify({"success": False, "errors": ["Error interno al registrar. Intenta más tarde."]})