"""
Utilidades JWT para la API móvil.
Genera y valida tokens de acceso (1h) y refresh (30 días).
"""
import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

from utils.tenant_context import set_current_tenant

_JWT_SECRET = os.getenv("JWT_SECRET_KEY", "")
_ALGORITHM = "HS256"
_ACCESS_EXPIRE_MIN = 60
_REFRESH_EXPIRE_DAYS = 30


def _secret() -> str:
    if not _JWT_SECRET:
        raise RuntimeError("JWT_SECRET_KEY no está definida en las variables de entorno.")
    return _JWT_SECRET


def generate_tokens(user_id: str, rol: str, tipo: str = "empleado", tenant_id: str = None) -> dict:
    """Genera access_token + refresh_token para un usuario."""
    now = datetime.now(timezone.utc)
    access_payload = {
        "sub": user_id,
        "rol": rol,
        "tipo": tipo,
        "tenant_id": tenant_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=_ACCESS_EXPIRE_MIN),
    }
    refresh_payload = {
        "sub": user_id,
        "tipo": tipo,
        "tenant_id": tenant_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=_REFRESH_EXPIRE_DAYS),
    }
    return {
        "access_token": jwt.encode(access_payload, _secret(), algorithm=_ALGORITHM),
        "refresh_token": jwt.encode(refresh_payload, _secret(), algorithm=_ALGORITHM),
        "expires_in": _ACCESS_EXPIRE_MIN * 60,
        "token_type": "Bearer",
    }


def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret(), algorithms=[_ALGORITHM])


def jwt_required(f):
    """Decorador: requiere Authorization: Bearer <token> válido."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"status": "error", "message": "Token de acceso requerido"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                return jsonify({"status": "error", "message": "Token inválido"}), 401
            request.jwt_payload = payload
            set_current_tenant(payload.get("tenant_id"))
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token expirado, usa /api/v1/auth/refresh"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated


def jwt_rol_required(roles: list):
    """Decorador: requiere JWT válido + rol permitido."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"status": "error", "message": "Token de acceso requerido"}), 401
            token = auth.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token)
                if payload.get("type") != "access":
                    return jsonify({"status": "error", "message": "Token inválido"}), 401
                request.jwt_payload = payload
                set_current_tenant(payload.get("tenant_id"))
            except jwt.ExpiredSignatureError:
                return jsonify({"status": "error", "message": "Token expirado"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"status": "error", "message": "Token inválido"}), 401

            if str(payload.get("rol", "")) not in [str(r) for r in roles]:
                return jsonify({"status": "error", "message": "Sin permisos para esta acción"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
