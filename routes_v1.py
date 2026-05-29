"""
API v1 — Blueprint para la app móvil.
Prefijo: /api/v1
Todos los endpoints aquí usan JWT (Bearer token), no sesiones de Flask.
"""
from flask import Blueprint, jsonify
from extensions import limiter

from controllers.api.v1.auth_mobile_controller import AuthMobileController

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


# ============================================================
# HEALTH CHECK
# ============================================================
@api_v1_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0"}), 200


# ============================================================
# AUTENTICACIÓN MÓVIL
# ============================================================
_mobile_login = limiter.limit("10 per minute")(AuthMobileController.login)

@api_v1_bp.route("/auth/login", methods=["POST"])
def mobile_login():
    """Login de empleado — devuelve JWT access + refresh token."""
    return _mobile_login()


@api_v1_bp.route("/auth/refresh", methods=["POST"])
def mobile_refresh():
    """Renueva el access token usando el refresh token."""
    return AuthMobileController.refresh()


# ============================================================
# FUTURAS RUTAS (se agregan en fases posteriores)
# ============================================================
# Fase 2: /auth/registro-cliente, /auth/login-cliente, /perfil
# Fase 3: /mesa/escanear, /menu, /pedido
# Fase 4: /cuenta, /pago, /dividir
# Fase 5: /historial, /puntos, /promociones
