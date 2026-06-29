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
from flask import Flask, request, redirect, url_for, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
from flask_socketio import join_room
from extensions import socketio, limiter

# 3. Cargar variables de entorno
load_dotenv()

# ================================
# INICIALIZACIÓN DE LA APP
# ================================
app = Flask(__name__, template_folder="resources/views", static_folder="static")

# Clave secreta — requerida, sin fallback hardcodeado
_secret_key = os.getenv("SECRET_KEY")
if not _secret_key:
    raise RuntimeError("SECRET_KEY no está definida en las variables de entorno.")
app.secret_key = _secret_key

# Configuraciones base de Flask
app.config.update(
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=0
)

# ================================
# CONFIGURACIÓN DE SEGURIDAD (CORS)
# ================================
ALLOWED_ORIGINS = [
    origin for origin in [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        os.getenv("CORS_LOCAL_ORIGIN", ""),
    ]
    if origin
]
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
    # En producción (HTTPS) debe ser True. Controlado por entorno para no romper local.
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    SESSION_COOKIE_HTTPONLY=True,
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
# Importamos las rutas aquí para evitar importaciones circulares en el startup
from routes import routes_bp, register_reports_routes
from routes_v1 import api_v1_bp

app.register_blueprint(routes_bp)
app.register_blueprint(api_v1_bp)
register_reports_routes(app)

# Índices de colecciones nuevas
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
    """Inyecta la fecha y hora actual en todos los templates Jinja2."""
    return {"now": datetime.now}

@app.context_processor
def inject_tenant():
    """Expone el restaurante (tenant) actual a todos los templates (white-label)."""
    from models.restaurante_model import Restaurante
    tenant_id = session.get("tenant_id")
    tenant = None
    if tenant_id:
        try:
            tenant = Restaurante.find_by_id(tenant_id)
        except Exception:
            tenant = None
    return {"tenant": tenant or {}}

@app.before_request
def log_request():
    """Registra las peticiones entrantes ignorando los archivos estáticos."""
    if request.path.startswith("/static"):
        return
    print(f"\n[REQ] {request.method} {request.path}")
    print("[COOKIES]:", list(request.cookies.keys()))

# ================================
# CONTEXTO DE TENANT (MULTI-TENANCY)
# ================================
from utils.tenant_context import set_current_tenant

@app.before_request
def load_tenant_context():
    """Carga el tenant activo desde la sesion web. En peticiones con JWT, el
    decorador jwt_required lo sobreescribe desde el token (corre despues)."""
    set_current_tenant(session.get("tenant_id"))

@app.teardown_request
def clear_tenant_context(exc=None):
    """Limpia el tenant al terminar el request (evita fuga entre peticiones que
    reusan el mismo hilo)."""
    set_current_tenant(None)

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
    print(f"Auto-reload: {'Activado' if reloader_config else 'Desactivado (Previniendo fallos en Windows)'}")
    print("=" * 60 + "\n")
    
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    # Iniciar mediante SocketIO (Recomendado cuando se usan websockets)
    socketio.run(
        app,
        debug=debug_mode,
        use_reloader=reloader_config and debug_mode,
        host='0.0.0.0',
        port=5000
    )