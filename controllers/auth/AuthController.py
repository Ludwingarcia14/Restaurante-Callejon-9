"""
Controlador de Autenticación - Sistema Restaurante Callejón 9
Versión simplificada sin 2FA y sin bcrypt para desarrollo local
Roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models.empleado_model import Usuario, RolPermisos
from controllers.notificaciones.notificacion_controller import NotificacionSistemaController
import secrets
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)

class AuthController:
    
    @staticmethod
    def login():
        """Endpoint de login simplificado para desarrollo local"""
        
        if request.method == "POST":
            data = request.get_json()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            
            print(f"\n🔐 Intento de login:")
            print(f"   Email: {email}")
            print(f"   Password: {'*' * len(password)}")
            
            # 1. Validaciones básicas
            if not email or not password:
                return jsonify({
                    "status": "error",
                    "message": "Por favor completa todos los campos"
                })
            
            # 2. Buscar usuario por email
            try:
                usuario_doc = Usuario.find_by_email(email)
                print(f"   Usuario encontrado: {usuario_doc is not None}")
                
                if usuario_doc:
                    print(f"   Rol del usuario: {usuario_doc.get('usuario_rol')}")
                    print(f"   Status: {usuario_doc.get('usuario_status')}")
                
            except Exception as e:
                print(f"   ❌ Error al buscar usuario: {e}")
                return jsonify({
                    "status": "error",
                    "message": f"Error de base de datos: {str(e)}"
                })
            
            if not usuario_doc:
                return jsonify({
                    "status": "error",
                    "message": "Credenciales incorrectas"
                })
            
            # 3. Validar que el usuario sea del restaurante (roles 1, 2, 3 o 4)
            rol = str(usuario_doc.get("usuario_rol", ""))
            if rol not in ["1", "2", "3", "4"]:
                return jsonify({
                    "status": "error",
                    "message": "No tienes permisos para acceder al sistema"
                })
            
            # 4. Validar contraseña (comparación directa sin bcrypt)
            stored_password = usuario_doc.get("usuario_clave", "")
            
            print(f"   Contraseña almacenada: {stored_password}")
            print(f"   Contraseña ingresada: {password}")
            print(f"   ¿Coinciden?: {stored_password == password}")
            
            if stored_password != password:
                return jsonify({
                    "status": "error",
                    "message": "Credenciales incorrectas"
                })
            
            # 5. Login exitoso - Generar sesión
            token_session = secrets.token_urlsafe(32)
            user_id = str(usuario_doc["_id"])
            
            # Actualizar token de sesión en BD
            try:
                Usuario.update_session_token(user_id, token_session, 1)
            except Exception as e:
                print(f"   ⚠️ Error al actualizar token: {e}")
            
            # 6. Poblar sesión de Flask
            session["usuario_id"] = user_id
            session["usuario_nombre"] = usuario_doc.get("usuario_nombre", "")
            session["usuario_apellidos"] = usuario_doc.get("usuario_apellidos", "")
            session["usuario_email"] = usuario_doc.get("usuario_email", "")
            session["usuario_rol"] = rol
            session["usuario_foto"] = usuario_doc.get("usuario_foto", "")
            session["token_session"] = token_session
            session["theme"] = "light"
            
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
            
            # 7. Determinar dashboard según rol
            rol_endpoints = {
                "1": "dashboard_admin",      # Administración
                "2": "dashboard_mesero",      # Mesero
                "3": "dashboard_cocina",      # Cocina
                "4": "dashboard_inventario"   # Inventario
            }
            
            endpoint = rol_endpoints.get(rol)
            
            if endpoint:
                logging.info(f"✅ Login exitoso: {email} | Rol: {RolPermisos.get_nombre_rol(rol)}")
                
                # ✨ NOTIFICAR LOGIN
                try:
                    NotificacionSistemaController.notificar_login(
                        usuario_id=user_id,
                        nombre_usuario=usuario_doc.get("usuario_nombre", ""),
                        rol=rol
                    )
                except Exception as e:
                    logging.warning(f"⚠️ No se pudo enviar notificación de login: {e}")
                
                return jsonify({
                    "status": "success",
                    "dashboard": url_for(f"routes.{endpoint}"),
                    "user": {
                        "nombre": usuario_doc.get("usuario_nombre"),
                        "rol": RolPermisos.get_nombre_rol(rol)
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
        # Guardar datos antes de limpiar
        usuario_id = session.get("usuario_id")
        usuario_nombre = session.get("usuario_nombre")
        usuario_rol = session.get("usuario_rol")
        
        if usuario_id:
            try:
                # Actualizar status a inactivo y limpiar token
                Usuario.update_session_token(usuario_id, None, 0)
            except Exception as e:
                logging.error(f"Error al actualizar estado en logout: {e}")
            
            # ✨ NOTIFICAR LOGOUT
            try:
                NotificacionSistemaController.notificar_logout(
                    usuario_id=usuario_id,
                    nombre_usuario=usuario_nombre,
                    rol=usuario_rol
                )
            except Exception as e:
                logging.warning(f"⚠️ No se pudo enviar notificación de logout: {e}")
        
        session.clear()
        return redirect(url_for("routes.login"))
    
    
    @staticmethod
    def verify_2fa():
        """Método deshabilitado - 2FA no implementado"""
        return jsonify({
            "status": "error",
            "message": "2FA no implementado en esta versión"
        }), 400


# ==========================================
# DECORADORES PARA PROTEGER RUTAS
# ==========================================

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