"""
Auth móvil — login y refresh para empleados via JWT.
Fase 2 agregará registro/login de clientes.
"""
import logging
import jwt as pyjwt

from flask import request, jsonify
from models.empleado_model import Usuario, RolPermisos
from services.security.password_service import PasswordService
from utils.jwt_utils import generate_tokens, decode_token
from utils.validators import is_valid_email, sanitize_str

logger = logging.getLogger(__name__)


class AuthMobileController:

    @staticmethod
    def login():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Se requiere body JSON"}), 400

        email = sanitize_str(data.get("email", "")).lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y contraseña son requeridos"}), 400

        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Formato de email inválido"}), 400

        if len(password) < 4 or len(password) > 128:
            return jsonify({"status": "error", "message": "Contraseña inválida"}), 400

        try:
            usuario_doc = Usuario.find_by_email(email)
        except Exception as e:
            logger.error("Error DB en login móvil: %s", e)
            return jsonify({"status": "error", "message": "Error de base de datos"}), 500

        if not usuario_doc:
            return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

        rol = str(usuario_doc.get("usuario_rol", ""))
        if rol not in ["1", "2", "3", "4"]:
            return jsonify({"status": "error", "message": "Sin permisos de acceso"}), 403

        stored = usuario_doc.get("usuario_clave", "")
        if stored.startswith("$2b$") or stored.startswith("$2a$"):
            password_ok = PasswordService.verify_password(password, stored)
        else:
            password_ok = stored == password

        if not password_ok:
            return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

        user_id = str(usuario_doc["_id"])
        tokens = generate_tokens(user_id, rol, tipo="empleado")

        return jsonify({
            "status": "success",
            "user": {
                "id": user_id,
                "nombre": usuario_doc.get("usuario_nombre", ""),
                "apellidos": usuario_doc.get("usuario_apellidos", ""),
                "email": email,
                "rol": rol,
                "rol_nombre": RolPermisos.get_nombre_rol(rol),
                "foto": usuario_doc.get("usuario_foto", ""),
            },
            **tokens,
        }), 200

    @staticmethod
    def refresh():
        data = request.get_json(silent=True)
        if not data or not data.get("refresh_token"):
            return jsonify({"status": "error", "message": "refresh_token requerido"}), 400

        try:
            payload = decode_token(data["refresh_token"])
            if payload.get("type") != "refresh":
                return jsonify({"status": "error", "message": "Token inválido"}), 401
        except pyjwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Refresh token expirado, inicia sesión nuevamente"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Token inválido"}), 401

        user_id = payload.get("sub")
        tipo = payload.get("tipo", "empleado")

        try:
            usuario_doc = Usuario.find_by_id(user_id)
        except Exception:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

        if not usuario_doc:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

        rol = str(usuario_doc.get("usuario_rol", ""))
        tokens = generate_tokens(user_id, rol, tipo=tipo)

        return jsonify({"status": "success", **tokens}), 200
