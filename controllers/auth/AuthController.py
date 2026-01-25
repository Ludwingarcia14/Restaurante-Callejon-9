"""
Controlador de Autenticación - Sistema Restaurante
Adaptado a la estructura actual de la BD
"""
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models.empleado_model import Usuario, RolPermisos
import bcrypt, secrets, logging, os
from dotenv import load_dotenv

load_dotenv()

SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

logging.basicConfig(level=logging.INFO)

class AuthController:
    
    @staticmethod
    def login():
        """Endpoint de login unificado para todos los roles"""
        errors = []
        
        if request.method == "POST":
            data = request.get_json()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            
            # 1. Buscar usuario por email
            usuario_doc = Usuario.find_by_email(email)
            
            if not usuario_doc:
                errors.append("Credenciales incorrectas")
                return jsonify({"status": "error", "message": errors[0]})
            
            # 2. Validar que la cuenta esté activa
            if usuario_doc.get("usuario_status") != 1:
                errors.append("Cuenta inactiva. Contacta al administrador.")
                return jsonify({"status": "error", "message": errors[0]})
            
            # 3. Validar contraseña
            stored_hash = usuario_doc.get("usuario_clave")
            if not stored_hash:
                errors.append("Usuario sin contraseña configurada")
                return jsonify({"status": "error", "message": errors[0]})
            
            try:
                stored_hash_bytes = stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash
                password_bytes = password.encode("utf-8")
                
                if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
                    errors.append("Credenciales incorrectas")
                    return jsonify({"status": "error", "message": errors[0]})
            except Exception as e:
                logging.exception(f"Error al verificar contraseña: {e}")
                errors.append("Error interno de autenticación")
                return jsonify({"status": "error", "message": errors[0]})
            
            # 4. Login exitoso - Generar sesión
            token_session = secrets.token_urlsafe(32)
            user_id = usuario_doc["_id"]
            rol = usuario_doc.get("usuario_rol")
            
            # Actualizar token de sesión
            Usuario.update_session_token(user_id, token_session, 1)
            
            # 5. Poblar sesión de Flask
            session["usuario_id"] = str(user_id)
            session["usuario_nombre"] = usuario_doc.get("usuario_nombre")
            session["usuario_apellidos"] = usuario_doc.get("usuario_apellidos")
            session["usuario_email"] = usuario_doc.get("usuario_email")
            session["usuario_rol"] = rol
            session["usuario_foto"] = usuario_doc.get("usuario_foto", "")
            session["token_session"] = token_session
            session["theme"] = "light"
            
            # Datos de 2FA
            session["2fa_enabled"] = usuario_doc.get("2fa_enabled", False)
            session["2fa_tipo"] = usuario_doc.get("2fa_tipo")
            session["2fa_secret"] = usuario_doc.get("2fa_secret")
            session["2fa_telefono"] = usuario_doc.get("2fa_telefono")
            
            # Permisos del rol
            permisos = RolPermisos.get_permisos(rol)
            session["permisos"] = permisos
            
            # Perfil específico según rol
            if rol == "2":  # Mesero
                perfil_mesero = Usuario.get_perfil_mesero(usuario_doc)
                session["perfil_mesero"] = perfil_mesero
            elif rol == "3":  # Cocina
                perfil_cocina = Usuario.get_perfil_cocina(usuario_doc)
                session["perfil_cocina"] = perfil_cocina
            
            # 6. Determinar dashboard según rol
            rol_endpoints = {
                "1": "dashboard_admin",
                "2": "dashboard_mesero",
                "3": "dashboard_cocina"
            }
            
            endpoint = rol_endpoints.get(rol)
            
            if endpoint:
                logging.info(f"Login exitoso: {email} | Rol: {RolPermisos.get_nombre_rol(rol)}")
                
                return jsonify({
                    "status": "success",
                    "dashboard": url_for(f"routes.{endpoint}"),
                    "user": {
                        "tipo": usuario_doc.get("2fa_tipo"),
                        "secret": usuario_doc.get("2fa_secret"),
                        "requires_2fa": usuario_doc.get("2fa_enabled", False)
                    }
                })
            else:
                flash("Rol no reconocido", "error")
                return jsonify({"status": "error", "message": "Rol no reconocido"})
        
        # GET request - Mostrar formulario de login
        return render_template("login.html", site_key=SITE_KEY)
    
    
    @staticmethod
    def logout():
        """Cierra sesión del usuario"""
        usuario_id = session.get("usuario_id")
        
        if usuario_id:
            try:
                # Actualizar status a inactivo y limpiar token
                Usuario.update_session_token(usuario_id, None, 0)
            except Exception as e:
                logging.error(f"Error al actualizar estado en logout: {e}")
        
        session.clear()
        return redirect(url_for("routes.login"))
    
    
    @staticmethod
    def verify_2fa():
        """Verifica el código 2FA después del login inicial"""
        if request.method == "POST":
            data = request.get_json()
            otp_code = data.get("otp_code")
            temp_secret = session.get("2fa_secret")
            
            if not temp_secret:
                return jsonify({"status": "error", "message": "Sesión expirada"}), 400
            
            # Importar el servicio de 2FA
            from services.autentication.service import TwoFactorService
            
            if TwoFactorService.verify_code(temp_secret, otp_code):
                # 2FA exitoso, ya puede acceder
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "error", "message": "Código inválido"}), 400
        
        return jsonify({"status": "error", "message": "Método no permitido"}), 405


# ==========================================
# DECORADORES PARA PROTEGER RUTAS
# ==========================================

from functools import wraps

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)
    return decorated_function


def rol_required(roles_permitidos):
    """
    Decorador para requerir roles específicos
    Uso: @rol_required(['1', '2'])  # Admin y Mesero
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "usuario_id" not in session:
                return redirect(url_for("routes.login"))
            
            rol_actual = session.get("usuario_rol")
            if str(rol_actual) not in [str(r) for r in roles_permitidos]:
                flash("No tienes permisos para acceder a esta página", "error")
                return redirect(url_for("routes.login"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permiso_required(permiso):
    """
    Decorador para verificar un permiso específico
    Uso: @permiso_required('puede_editar')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "usuario_id" not in session:
                return redirect(url_for("routes.login"))
            
            rol_actual = session.get("usuario_rol")
            if not RolPermisos.tiene_permiso(rol_actual, permiso):
                flash("No tienes permisos para realizar esta acción", "error")
                return redirect(url_for("routes.login"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator