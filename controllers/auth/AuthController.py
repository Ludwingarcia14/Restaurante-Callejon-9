"""
Controlador de Autenticación - Sistema Restaurante Callejón 9
Roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models.empleado_model import Usuario, RolPermisos
import bcrypt
import secrets
import logging

logging.basicConfig(level=logging.INFO)

class AuthController:
    
    @staticmethod
    def login():
        """Endpoint de login unificado para todos los roles del restaurante"""
        errors = []
        
        if request.method == "POST":
            data = request.get_json()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            
            # 1. Validaciones básicas
            if not email or not password:
                return jsonify({
                    "status": "error",
                    "message": "Por favor completa todos los campos"
                })
            
            # 2. Buscar usuario por email
            usuario_doc = Usuario.find_by_email(email)
            
            if not usuario_doc:
                return jsonify({
                    "status": "error",
                    "message": "Credenciales incorrectas"
                })
            
            # 3. Validar que el usuario sea del restaurante (roles 1, 2 o 3)
            rol = usuario_doc.get("usuario_rol")
            if str(rol) not in ["1", "2", "3"]:
                return jsonify({
                    "status": "error",
                    "message": "No tienes permisos para acceder al sistema"
                })
            
            # 4. Validar que la cuenta esté activa
            if usuario_doc.get("usuario_status") != 1:
                return jsonify({
                    "status": "error",
                    "message": "Cuenta inactiva. Contacta al administrador."
                })
            
            # 5. Validar contraseña
            stored_hash = usuario_doc.get("usuario_clave")
            if not stored_hash:
                return jsonify({
                    "status": "error",
                    "message": "Usuario sin contraseña configurada"
                })
            
            try:
                stored_hash_bytes = stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash
                password_bytes = password.encode("utf-8")
                
                if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
                    return jsonify({
                        "status": "error",
                        "message": "Credenciales incorrectas"
                    })
            except Exception as e:
                logging.exception(f"Error al verificar contraseña: {e}")
                return jsonify({
                    "status": "error",
                    "message": "Error interno de autenticación"
                })
            
            # 6. Login exitoso - Generar sesión
            token_session = secrets.token_urlsafe(32)
            user_id = usuario_doc["_id"]
            
            # Actualizar token de sesión en BD
            Usuario.update_session_token(user_id, token_session, 1)
            
            # 7. Poblar sesión de Flask
            session["usuario_id"] = str(user_id)
            session["usuario_nombre"] = usuario_doc.get("usuario_nombre")
            session["usuario_apellidos"] = usuario_doc.get("usuario_apellidos")
            session["usuario_email"] = usuario_doc.get("usuario_email")
            session["usuario_rol"] = rol
            session["usuario_foto"] = usuario_doc.get("usuario_foto", "")
            session["token_session"] = token_session
            session["theme"] = "light"
            
            # Datos de 2FA (si aplica)
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
            
            # 8. Determinar dashboard según rol
            rol_endpoints = {
                "1": "dashboard_admin",   # Administración
                "2": "dashboard_mesero",   # Mesero
                "3": "dashboard_cocina"    # Cocina
            }
            
            endpoint = rol_endpoints.get(str(rol))
            
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
                return jsonify({
                    "status": "error",
                    "message": "Rol no reconocido"
                })
        
        # GET request - Mostrar formulario de login
        return render_template("login.html")
    
    
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
                return jsonify({
                    "status": "error",
                    "message": "Sesión expirada"
                }), 400
            
            # Importar el servicio de 2FA
            from services.autentication.service import TwoFactorService
            
            if TwoFactorService.verify_code(temp_secret, otp_code):
                # 2FA exitoso, ya puede acceder
                return jsonify({"status": "success"})
            else:
                return jsonify({
                    "status": "error",
                    "message": "Código inválido"
                }), 400
        
        return jsonify({
            "status": "error",
            "message": "Método no permitido"
        }), 405


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