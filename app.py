"""
Módulo Principal de la Aplicación Flask - Restaurante Callejón 9
Arquitectura: MVC / Monolito Orientado a Servicios
"""
# 1. Librerías Nativas
import os
import sys
import time
import socket
import platform
from datetime import datetime

# 2. Librerías de Terceros
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, jsonify, send_from_directory
from flask_cors import CORS
from flask_session import Session
from flask_socketio import join_room
from extensions import socketio, limiter
from bson import ObjectId
from flask.json.provider import DefaultJSONProvider

# 3. Cargar variables de entorno
load_dotenv()

# ================================
# INICIALIZACIÓN DE LA APP
# ================================
app = Flask(__name__, template_folder="resources/views", static_folder="static")

# Serialización de tipos MongoDB en JSON
class MongoJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = MongoJSONProvider
app.json = MongoJSONProvider(app)

# Clave secreta — requerida, sin fallback hardcodeado
_secret_key = os.getenv("SECRET_KEY")
if not _secret_key:
    raise RuntimeError("SECRET_KEY no está definida en las variables de entorno.")
app.secret_key = _secret_key

app.config.update(
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=0
)

# ================================
# CONFIGURACIÓN DE SEGURIDAD (CORS)
# ================================
_origenes_base = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "https://restaurante-callejon-9-production.up.railway.app",
]
_origenes_env = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
ALLOWED_ORIGINS = list(set(_origenes_base + _origenes_env))

CORS(app, supports_credentials=True, resources={r"/*": {"origins": ALLOWED_ORIGINS}})

# ================================
# WEBSOCKETS (Socket.IO)
# ================================
socketio.init_app(
    app,
    cors_allowed_origins=ALLOWED_ORIGINS,
    async_mode="threading",
    manage_session=False
)

# ================================
# GESTIÓN DE SESIONES (Filesystem)
# ================================
SESSION_DIR = os.path.join(os.getcwd(), "flask_session")
os.makedirs(SESSION_DIR, exist_ok=True)

app.config.update(
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=SESSION_DIR,
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_NAME="callejon9_session",
    SESSION_REFRESH_EACH_REQUEST=True
)

Session(app)
limiter.init_app(app)

def clean_old_sessions():
    """Elimina archivos de sesión con más de 24 horas de antigüedad."""
    try:
        now = time.time()
        for filename in os.listdir(SESSION_DIR):
            filepath = os.path.join(SESSION_DIR, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < now - 86400:
                os.remove(filepath)
                print(f"[SESION] Limpiada: {filename}")
    except Exception as e:
        print(f"[WARN] No se pudieron limpiar las sesiones antiguas: {e}")

clean_old_sessions()

# ================================
# REGISTRO DE RUTAS (Blueprints)
# ================================
from routes import routes_bp, register_reports_routes
from routes_v1 import api_v1_bp

app.register_blueprint(routes_bp)
app.register_blueprint(api_v1_bp)
register_reports_routes(app)

# Índices de colecciones nuevas (móvil)
from models.cliente_model import Cliente
from models.pedido_movil_model import PedidoMovil as _PedidoMovil
from models.pago_movil_model import PagoMovil as _PagoMovil
Cliente.ensure_indexes()
_PedidoMovil.ensure_indexes()
_PagoMovil.ensure_indexes()

# ================================
# MIDDLEWARE Y CONTEXTO
# ================================
@app.context_processor
def inject_now():
    return {"now": datetime.now}

@app.before_request
def log_request():
    if request.path.startswith("/static"):
        return
    print(f"\n[REQ] {request.method} {request.path}")
    print("[COOKIES]:", list(request.cookies.keys()))

# ================================
# APP MÓVIL REACT (servir desde /app/)
# ================================
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), 'frontend_dist')

@app.route('/app/', defaults={'path': ''})
@app.route('/app/<path:path>')
def serve_react_app(path):
    """Sirve la app móvil React compilada. Rutas desconocidas → index.html (React Router)."""
    full = os.path.join(_FRONTEND_DIST, path)
    if path and os.path.isfile(full):
        return send_from_directory(_FRONTEND_DIST, path)
    return send_from_directory(_FRONTEND_DIST, 'index.html')

# ================================
# EVENTOS DE SOCKET.IO
# ================================
@socketio.on("connect")
def socket_connect(auth):
    print("[SOCKET] Nuevo cliente conectado")

@socketio.on("disconnect")
def socket_disconnect():
    print("[SOCKET] Cliente desconectado")

@socketio.on("join_room")
def on_join_room(room):
    join_room(room)
    print(f"[SALA] Cliente unido a la sala: {room}")

@socketio.on("join_cliente")
def on_join_cliente(data):
    """App móvil se une a su sala personal para recibir updates de pedidos."""
    cliente_id = data.get("cliente_id") if isinstance(data, dict) else str(data)
    if cliente_id:
        sala = f"cliente_{cliente_id}"
        join_room(sala)
        print(f"[SALA] Cliente unido a sala personal: {sala}")

# ================================
# API DOCS
# ================================
@app.route('/api/docs')
def api_docs():
    return """<!DOCTYPE html>
<html>
<head>
  <title>Callejón 9 — API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({
  url: "/static/swagger.yaml",
  dom_id: "#swagger-ui",
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  layout: "BaseLayout",
  deepLinking: true
});
</script>
</body>
</html>"""

# ================================
# MANEJO DE ERRORES GLOBALES
# ================================
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Recurso no encontrado"}), 404
    return redirect(url_for("routes.login"))

@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Sin permisos"}), 403
    return redirect(url_for("routes.login"))

@app.errorhandler(400)
def bad_request(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Solicitud inválida"}), 400
    return redirect(url_for("routes.login"))

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"status": "error", "message": "No autorizado"}), 401

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"status": "error", "message": "Demasiados intentos, intenta más tarde"}), 429

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500
    return redirect(url_for("routes.login"))

# ================================
# INICIO DEL SERVIDOR
# ================================
if __name__ == "__main__":
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    is_windows = platform.system() == "Windows"

    print("=" * 60)
    print("CALLEJON 9 - SERVIDOR INICIADO")
    print(f"http://127.0.0.1:5000")
    print(f"http://{local_ip}:5000")
    print("=" * 60)

    reloader_config = not is_windows
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"Auto-reload: {'Activado' if reloader_config and debug_mode else 'Desactivado'}")
    print("=" * 60 + "\n")

    socketio.run(
        app,
        debug=debug_mode,
        use_reloader=reloader_config and debug_mode,
        host='0.0.0.0',
        port=5000
    )
