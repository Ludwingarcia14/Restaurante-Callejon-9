"""
Helpers de validación de inputs para la API móvil.
"""
import re
from functools import wraps
from flask import request, jsonify


def validate_json(*required_fields):
    """Decorador: verifica que el body sea JSON y que los campos requeridos existan."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True)
            if not data:
                return jsonify({"status": "error", "message": "Se requiere un body JSON"}), 400
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                return jsonify({
                    "status": "error",
                    "message": f"Campos requeridos: {', '.join(missing)}"
                }), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def sanitize_str(value, max_length: int = 255) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def is_valid_objectid(value: str) -> bool:
    return bool(re.match(r'^[a-f\d]{24}$', str(value), re.IGNORECASE))
