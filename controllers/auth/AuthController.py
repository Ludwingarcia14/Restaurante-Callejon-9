from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models.empleado_model import Usuario, RolPermisos
from controllers.notificaciones.notificacion_controller import NotificacionSistemaController
from services.security.two_factor_service import TwoFactorService
import secrets
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)


# Configuracion de roles y endpoints
ROLES_VALIDOS = ["1", "2", "3", "4"]

ROL_ENDPOINTS = {
    "1": ("dashboard_admin", "/dashboard/admin"),
    "2": ("dashboard_mesero", "/dashboard/mesero"),
    "3": ("dashboard_cocina", "/dashboard/cocina"),
    "4": ("dashboard_inventario", "/dashboard/inventario")
}

SESSION_CONFIG = {
    "token_length": 32,
    "theme_default": "light"
}

# Tipos de 2FA soportados
TIPO_2FA_APP = "app"
TIPO_2FA_SMS = "sms"
TIPO_2FA_EMAIL = "email"


# Decoradores para rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)
    return decorated_function


def rol_required(roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "usuario_id" not in session:
                return redirect(url_for("routes.login"))
            
            rol_actual = session.get("usuario_rol")
            if str(rol_actual) not in [str(r) for r in roles_permitidos]:
                flash("No tienes permisos para acceder a esta pagina", "error")
                return redirect(url_for("routes.login"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permiso_required(permiso):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "usuario_id" not in session:
                return redirect(url_for("routes.login"))
            
            rol_actual = session.get("usuario_rol")
            if not RolPermisos.tiene_permiso(rol_actual, permiso):
                flash("No tienes permisos para realizar esta accion", "error")
                return redirect(url_for("routes.login"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class AuthController:
    
    @staticmethod
    def login():
        if request.method == "POST":
            return AuthController._procesar_login()
        return render_template("login.html")
    
    @staticmethod
    def _procesar_login():
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        logging.info(f"Intento de login - Email: {email}")
        
        if not email or not password:
            return jsonify({
                "status": "error",
                "message": "Por favor completa todos los campos"
            })
        
        try:
            usuario_doc = Usuario.find_by_email(email)
        except Exception as e:
            logging.error(f"Error al buscar usuario: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error de base de datos: {str(e)}"
            })
        
        if not usuario_doc:
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas"
            })
        
        rol = str(usuario_doc.get("usuario_rol", ""))
        if rol not in ROLES_VALIDOS:
            return jsonify({
                "status": "error",
                "message": "No tienes permisos para acceder al sistema"
            })
        
        stored_password = usuario_doc.get("usuario_clave", "")
        if stored_password != password:
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas"
            })
        
        # Verificar estado de 2FA del usuario
        is_2fa_enabled = usuario_doc.get("2fa_enabled", False)
        logging.info(f"2FA status para {email}: enabled={is_2fa_enabled}")
        
        if is_2fa_enabled:
            return AuthController._iniciar_2fa(usuario_doc, rol)
        
        logging.info(f"Login sin 2FA para {email}")
        return AuthController._crear_sesion(usuario_doc, rol)
    
    @staticmethod
    def _iniciar_2fa(usuario_doc, rol):
        user_id = str(usuario_doc["_id"])
        tipo_2fa = usuario_doc.get("2fa_tipo", TIPO_2FA_APP)
        
        logging.info(f"_iniciar_2fa: user_id={user_id}, tipo_2fa={tipo_2fa}")
        
        if tipo_2fa in [TIPO_2FA_SMS, TIPO_2FA_EMAIL]:
            codigo_2fa = TwoFactorService.generar_codigo_sms()
            TwoFactorService.guardar_codigo_temporal(user_id, codigo_2fa)
            logging.info(f"Codigo 2FA generado para {tipo_2fa}: {codigo_2fa}")
        
        session["2fa_pending_user_id"] = user_id
        session["2fa_pending_rol"] = rol
        session["2fa_tipo"] = tipo_2fa
        
        return jsonify({
            "status": "success",
            "requires_2fa": True,
            "tipo": tipo_2fa,
            "secret": usuario_doc.get("2fa_secret") if tipo_2fa == TIPO_2FA_APP else None,
            "message": "Codigo de verificacion enviado" if tipo_2fa != TIPO_2FA_APP else "Ingresa el codigo de tu app"
        })
    
    @staticmethod
    def verify_2fa():
        if request.method != "POST":
            return jsonify({
                "status": "error",
                "message": "Metodo no permitido"
            }), 405
        
        data = request.get_json()
        codigo = data.get("otp_code", "").strip()
        
        user_id = session.get("2fa_pending_user_id")
        if not user_id:
            logging.warning("verify_2fa llamado sin session 2fa_pending_user_id")
            return jsonify({
                "status": "error",
                "message": "No hay verificacion 2FA pendiente"
            })
        
        logging.info(f"verify_2fa iniciado para user_id: {user_id}")
        
        try:
            usuario_doc = Usuario.find_by_id(user_id)
        except Exception as e:
            logging.error(f"Error al buscar usuario: {e}")
            return jsonify({
                "status": "error",
                "message": "Error al verificar usuario"
            })
        
        if not usuario_doc:
            return jsonify({
                "status": "error",
                "message": "Usuario no encontrado"
            })
        
        tipo_2fa = session.get("2fa_tipo")
        codigo_valido = False
        
        import os
        modo_desarrollo = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        if tipo_2fa == TIPO_2FA_APP:
            secret = usuario_doc.get("2fa_secret")
            if secret:
                logging.info(f"TOTP: Verificando codigo={codigo} con secret={secret[:10]}...")
                codigo_valido = TwoFactorService.verificar_totp(secret, codigo)
                logging.info(f"TOTP: Resultado={codigo_valido}")
                if modo_desarrollo and not codigo_valido:
                    logging.warning(f"Codigo incorrecto en desarrollo. Verifica que Google Authenticator muestre el mismo codigo.")
            else:
                logging.error(f"No hay secret configurado para el usuario")
        else:
            codigo_valido = TwoFactorService.verificar_codigo_temporal(user_id, codigo)
        
        if not codigo_valido:
            return jsonify({
                "status": "error",
                "message": "Codigo de verificacion incorrecto"
            })
        
        logging.info(f"2FA verificado exitosamente para usuario: {user_id}")
        
        session.pop("2fa_pending_user_id", None)
        session.pop("2fa_pending_rol", None)
        session.pop("2fa_tipo", None)
        
        rol = str(usuario_doc.get("usuario_rol", "1"))
        return AuthController._crear_sesion(usuario_doc, rol)
    
    @staticmethod
    def _crear_sesion(usuario_doc, rol):
        user_id = str(usuario_doc["_id"])
        token_session = secrets.token_urlsafe(SESSION_CONFIG["token_length"])
        
        try:
            Usuario.update_session_token(user_id, token_session, 1)
        except Exception as e:
            logging.warning(f"Error al actualizar token: {e}")
        
        session["usuario_id"] = user_id
        session["usuario_nombre"] = usuario_doc.get("usuario_nombre", "")
        session["usuario_apellidos"] = usuario_doc.get("usuario_apellidos", "")
        session["usuario_email"] = usuario_doc.get("usuario_email", "")
        session["usuario_rol"] = rol
        session["usuario_foto"] = usuario_doc.get("usuario_foto", "")
        session["token_session"] = token_session
        session["theme"] = SESSION_CONFIG["theme_default"]
        session["permisos"] = RolPermisos.get_permisos(rol)
        
        session["2fa_enabled"] = usuario_doc.get("2fa_enabled", False)
        session["2fa_verificado"] = True
        
        if rol == "2":
            session["perfil_mesero"] = Usuario.get_perfil_mesero(usuario_doc)
        elif rol == "3":
            session["perfil_cocina"] = Usuario.get_perfil_cocina(usuario_doc)
        
        endpoint_data = ROL_ENDPOINTS.get(rol)
        
        if endpoint_data:
            endpoint_name, dashboard_url = endpoint_data
            logging.info(f"Login exitoso: {session['usuario_email']} | Rol: {RolPermisos.get_nombre_rol(rol)}")
            
            AuthController._notificar_login(user_id, session["usuario_nombre"], rol)
            
            return jsonify({
                "status": "success",
                "dashboard": dashboard_url,
                "user": {
                    "nombre": session["usuario_nombre"],
                    "rol": RolPermisos.get_nombre_rol(rol)
                }
            })
        
        return jsonify({
            "status": "error",
            "message": "Rol no reconocido"
        })
    
    @staticmethod
    def _notificar_login(usuario_id, nombre_usuario, rol):
        try:
            NotificacionSistemaController.notificar_login(
                usuario_id=usuario_id,
                nombre_usuario=nombre_usuario,
                rol=rol
            )
        except Exception as e:
            logging.warning(f"No se pudo enviar notificacion de login: {e}")
    
    @staticmethod
    def logout():
        usuario_id = session.get("usuario_id")
        usuario_nombre = session.get("usuario_nombre")
        usuario_rol = session.get("usuario_rol")
        
        if usuario_id:
            try:
                Usuario.update_session_token(usuario_id, None, 0)
            except Exception as e:
                logging.error(f"Error al actualizar estado en logout: {e}")
            
            AuthController._notificar_logout(usuario_id, usuario_nombre, usuario_rol)
        
        session.clear()
        return redirect(url_for("routes.login"))
    
    @staticmethod
    def _notificar_logout(usuario_id, nombre_usuario, rol):
        try:
            NotificacionSistemaController.notificar_logout(
                usuario_id=usuario_id,
                nombre_usuario=nombre_usuario,
                rol=rol
            )
        except Exception as e:
            logging.warning(f"No se pudo enviar notificacion de logout: {e}")
    
    @staticmethod
    def verificar_sesion():
        if "usuario_id" not in session:
            return jsonify({
                "status": "error",
                "message": "No hay sesion activa"
            }), 401
        
        return jsonify({
            "status": "success",
            "user": {
                "id": session.get("usuario_id"),
                "nombre": session.get("usuario_nombre"),
                "email": session.get("usuario_email"),
                "rol": session.get("usuario_rol"),
                "rol_nombre": RolPermisos.get_nombre_rol(session.get("usuario_rol"))
            }
        })
    
    @staticmethod
    def refresh_token():
        if "usuario_id" not in session:
            return jsonify({
                "status": "error",
                "message": "No hay sesion activa"
            }), 401
        
        usuario_id = session.get("usuario_id")
        nuevo_token = secrets.token_urlsafe(SESSION_CONFIG["token_length"])
        
        try:
            Usuario.update_session_token(usuario_id, nuevo_token, 1)
            session["token_session"] = nuevo_token
            return jsonify({
                "status": "success",
                "token": nuevo_token
            })
        except Exception as e:
            logging.error(f"Error al renovar token: {e}")
            return jsonify({
                "status": "error",
                "message": "Error al renovar token"
            }), 500
    
    @staticmethod
    def emergency_disable_2fa(email):
        import os
        
        emergency_key = os.environ.get('EMERGENCY_2FA_KEY', 'callejon9-emergency-2024')
        provided_key = request.args.get('key', '')
        
        if provided_key != emergency_key:
            return jsonify({
                "status": "error",
                "message": "Clave de emergencia incorrecta"
            }), 403
        
        try:
            usuario_doc = Usuario.find_by_email(email)
            if not usuario_doc:
                return jsonify({
                    "status": "error",
                    "message": "Usuario no encontrado"
                }), 404
            
            user_id = str(usuario_doc["_id"])
            
            Usuario.update_2fa_status(
                user_id=user_id,
                is_enabled=False,
                tipo=None,
                secret=None,
                telefono=None
            )
            
            return jsonify({
                "status": "success",
                "message": "2FA deshabilitado correctamente"
            })
        except Exception as e:
            logging.error(f"Error al deshabilitar 2FA: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error al deshabilitar 2FA: {str(e)}"
            }), 500
