"""
Controlador de Autenticación - Sistema Restaurante Callejón 9
Versión simplificada sin 2FA y sin bcrypt para desarrollo local
Roles:
1 = Admin
2 = Mesero
3 = Cocina
4 = Inventario
"""

from flask import (
    render_template, request, redirect,
    url_for, session, flash, jsonify
)
from models.empleado_model import Usuario, RolPermisos
from controllers.notificaciones.notificacion_controller import NotificacionSistemaController
from functools import wraps
import secrets
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)


class AuthController:

    # =====================================================
    # LOGIN
    # =====================================================
    @staticmethod
    def login():
        """Endpoint de login (JSON + HTML seguro para APIs)"""

        # -------------------------------
        # POST → autenticación
        # -------------------------------
        if request.method == "POST":

            try:
                data = request.get_json(force=True)
            except Exception:
                return jsonify({
                    "status": "error",
                    "message": "Formato de datos inválido"
                }), 400

            email = data.get("email", "").strip().lower()
            password = data.get("password", "")

            logging.info(f"🔐 Intento de login: {email}")

            # Validaciones básicas
            if not email or not password:
                return jsonify({
                    "status": "error",
                    "message": "Por favor completa todos los campos"
                }), 400

            # Buscar usuario
            try:
                usuario_doc = Usuario.find_by_email(email)
            except Exception as e:
                logging.error(f"❌ Error BD login: {e}")
                return jsonify({
                    "status": "error",
                    "message": "Error interno del servidor"
                }), 500

            if not usuario_doc:
                return jsonify({
                    "status": "error",
                    "message": "Credenciales incorrectas"
                }), 401

            rol = str(usuario_doc.get("usuario_rol", ""))

            if rol not in ["1", "2", "3", "4"]:
                return jsonify({
                    "status": "error",
                    "message": "Rol no autorizado"
                }), 403

            # Validar contraseña (DEV)
            if usuario_doc.get("usuario_clave") != password:
                return jsonify({
                    "status": "error",
                    "message": "Credenciales incorrectas"
                }), 401

            # -------------------------------
            # Crear sesión
            # -------------------------------
            token_session = secrets.token_urlsafe(32)
            user_id = str(usuario_doc["_id"])

            try:
                Usuario.update_session_token(user_id, token_session, 1)
            except Exception as e:
                logging.warning(f"⚠️ Token no actualizado: {e}")

            session.clear()
            session.update({
                "usuario_id": user_id,
                "usuario_nombre": usuario_doc.get("usuario_nombre", ""),
                "usuario_apellidos": usuario_doc.get("usuario_apellidos", ""),
                "usuario_email": usuario_doc.get("usuario_email", ""),
                "usuario_rol": rol,
                "usuario_foto": usuario_doc.get("usuario_foto", ""),
                "token_session": token_session,
                "theme": "light",
                "permisos": RolPermisos.get_permisos(rol)
            })

            # -------------------------------
            # Perfiles por rol
            # -------------------------------
            if rol == "2":  # Mesero
                perfil_mesero = Usuario.get_perfil_mesero(usuario_doc) or {}

                mesas = perfil_mesero.get("mesas_asignadas", [])
                if isinstance(mesas, list):
                    perfil_mesero["mesas_asignadas"] = [
                        int(m) for m in mesas if str(m).isdigit()
                    ]
                else:
                    perfil_mesero["mesas_asignadas"] = []

                session["perfil_mesero"] = perfil_mesero

            elif rol == "3":  # Cocina
                session["perfil_cocina"] = Usuario.get_perfil_cocina(usuario_doc) or {}

            # -------------------------------
            # Redirección por rol
            # -------------------------------
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

            logging.info(f"✅ Login exitoso: {email} | Rol {rol}")

            return jsonify({
                "status": "success",
                "dashboard": url_for(f"routes.{endpoint}"),
                "user": {
                    "nombre": usuario_doc.get("usuario_nombre"),
                    "rol": RolPermisos.get_nombre_rol(rol)
                }
            })

        # -------------------------------
        # GET → vista login
        # -------------------------------
        return render_template("login.html")

    # =====================================================
    # LOGOUT
    # =====================================================
    @staticmethod
    def logout():
        """Cierra sesión del usuario"""
        # Guardar datos antes de limpiar
        usuario_id = session.get("usuario_id")
        usuario_nombre = session.get("usuario_nombre")
        usuario_rol = session.get("usuario_rol")
        
        if usuario_id:
            try:
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

    # =====================================================
    # 2FA (DESHABILITADO)
    # =====================================================
    @staticmethod
    def verify_2fa():
        return jsonify({
            "status": "error",
            "message": "2FA no implementado"
        }), 400


# ==========================================
# DECORADORES PARA PROTEGER RUTAS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)
    return decorated


def rol_required(roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            rol_actual = session.get("usuario_rol")

            if not rol_actual:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "No autenticado"}), 401
                return redirect(url_for("routes.login"))

            if str(rol_actual) not in map(str, roles_permitidos):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "No autorizado"}), 403
                flash("No tienes permisos para acceder", "error")
                return redirect(url_for("routes.login"))

            return f(*args, **kwargs)
        return decorated
    return decorator


def permiso_required(permiso):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            rol_actual = session.get("usuario_rol")

            if not rol_actual or not RolPermisos.tiene_permiso(rol_actual, permiso):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Permiso denegado"}), 403
                flash("No tienes permisos", "error")
                return redirect(url_for("routes.login"))

            return f(*args, **kwargs)
        return decorated
    return decorator