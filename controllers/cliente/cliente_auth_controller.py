"""
Auth de clientes — registro, login, refresh y logout.
"""
import hashlib
import logging
import jwt as pyjwt

from flask import request, jsonify
from models.cliente_model import Cliente
from services.security.password_service import PasswordService
from utils.jwt_utils import generate_tokens, decode_token
from utils.validators import is_valid_email, sanitize_str

logger = logging.getLogger(__name__)

_CLIENT_ROL = "5"


def _hash_token(token: str) -> str:
    """SHA-256 del refresh token — nunca se guarda en claro."""
    return hashlib.sha256(token.encode()).hexdigest()


class ClienteAuthController:

    # ----------------------------------------------------------
    # REGISTRO
    # ----------------------------------------------------------
    @staticmethod
    def registro():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Se requiere body JSON"}), 400

        nombre    = sanitize_str(data.get("nombre", ""), 100)
        apellidos = sanitize_str(data.get("apellidos", ""), 100)
        email     = sanitize_str(data.get("email", "")).lower()
        password  = data.get("password", "")
        telefono  = sanitize_str(data.get("telefono", ""), 20)
        # Opcional: solo aplica en despliegues multi-tenant (ver models/cliente_model.py)
        tenant_id = sanitize_str(data.get("tenant_id", ""), 50) or None

        if not nombre:
            return jsonify({"status": "error", "message": "El nombre es requerido"}), 400
        if not email or not is_valid_email(email):
            return jsonify({"status": "error", "message": "Email inválido"}), 400
        if not password or len(password) < 6:
            return jsonify({"status": "error", "message": "La contraseña debe tener al menos 6 caracteres"}), 400
        if len(password) > 128:
            return jsonify({"status": "error", "message": "Contraseña demasiado larga"}), 400

        try:
            if Cliente.find_by_email(email):
                return jsonify({"status": "error", "message": "Este email ya está registrado"}), 409
        except Exception as e:
            logger.error("Error verificando email en registro: %s", e)
            return jsonify({"status": "error", "message": "Error de base de datos"}), 500

        try:
            password_hash = PasswordService.hash_password(password)
            cliente_id = Cliente.create(nombre, apellidos, email, password_hash, telefono, tenant_id=tenant_id)
        except Exception as e:
            logger.error("Error creando cliente: %s", e)
            return jsonify({"status": "error", "message": "Error al crear la cuenta"}), 500

        tokens = generate_tokens(cliente_id, rol=_CLIENT_ROL, tipo="cliente", tenant_id=tenant_id)

        try:
            Cliente.update_refresh_token(cliente_id, _hash_token(tokens["refresh_token"]))
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "message": "Cuenta creada exitosamente",
            "user": {
                "id": cliente_id,
                "nombre": nombre,
                "apellidos": apellidos,
                "email": email,
                "rol": "cliente",
                "puntos": 0,
            },
            **tokens,
        }), 201

    # ----------------------------------------------------------
    # LOGIN
    # ----------------------------------------------------------
    @staticmethod
    def login():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Se requiere body JSON"}), 400

        email    = sanitize_str(data.get("email", "")).lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y contraseña son requeridos"}), 400
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Formato de email inválido"}), 400

        try:
            cliente_doc = Cliente.find_by_email(email)
        except Exception as e:
            logger.error("Error DB en login cliente: %s", e)
            return jsonify({"status": "error", "message": "Error de base de datos"}), 500

        if not cliente_doc:
            return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

        if not cliente_doc.get("activo", True):
            return jsonify({"status": "error", "message": "Cuenta desactivada, contacta al restaurante"}), 403

        if not PasswordService.verify_password(password, cliente_doc.get("password", "")):
            return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

        cliente_id = str(cliente_doc["_id"])
        tokens = generate_tokens(cliente_id, rol=_CLIENT_ROL, tipo="cliente", tenant_id=cliente_doc.get("tenant_id"))

        try:
            Cliente.update_refresh_token(cliente_id, _hash_token(tokens["refresh_token"]))
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "user": Cliente.to_public(cliente_doc),
            **tokens,
        }), 200

    # ----------------------------------------------------------
    # REFRESH TOKEN
    # ----------------------------------------------------------
    @staticmethod
    def refresh():
        data = request.get_json(silent=True)
        if not data or not data.get("refresh_token"):
            return jsonify({"status": "error", "message": "refresh_token requerido"}), 400

        raw_token = data["refresh_token"]

        try:
            payload = decode_token(raw_token)
            if payload.get("type") != "refresh" or payload.get("tipo") != "cliente":
                return jsonify({"status": "error", "message": "Token inválido"}), 401
        except pyjwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Refresh token expirado, inicia sesión nuevamente"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Token inválido"}), 401

        cliente_id = payload["sub"]
        cliente_doc = Cliente.find_by_id(cliente_id)

        if not cliente_doc:
            return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404

        stored_hash = cliente_doc.get("refresh_token_hash")
        if stored_hash and stored_hash != _hash_token(raw_token):
            return jsonify({"status": "error", "message": "Refresh token ya utilizado o inválido"}), 401

        tokens = generate_tokens(cliente_id, rol=_CLIENT_ROL, tipo="cliente", tenant_id=cliente_doc.get("tenant_id"))

        try:
            Cliente.update_refresh_token(cliente_id, _hash_token(tokens["refresh_token"]))
        except Exception:
            pass

        return jsonify({"status": "success", **tokens}), 200

    # ----------------------------------------------------------
    # LOGOUT
    # ----------------------------------------------------------
    @staticmethod
    def logout():
        payload = getattr(request, "jwt_payload", {})
        cliente_id = payload.get("sub")
        if cliente_id:
            try:
                Cliente.update_refresh_token(cliente_id, None)
            except Exception:
                pass
        return jsonify({"status": "success", "message": "Sesión cerrada"}), 200