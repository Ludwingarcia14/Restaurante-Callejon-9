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
from flask import Flask, request, redirect, url_for
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
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
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
    SESSION_COOKIE_SECURE=False,  # Cambiar a True si configuras HTTPS
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

app.register_blueprint(routes_bp)
register_reports_routes(app)

# ================================
# MIDDLEWARE Y CONTEXTO
# ================================
@app.context_processor
def inject_now():
    """Inyecta la fecha y hora actual en todos los templates Jinja2."""
    return {"now": datetime.now}

@app.before_request
def log_request():
    """Registra las peticiones entrantes ignorando los archivos estáticos."""
    if request.path.startswith("/static"):
        return
    print(f"\n[REQ] {request.method} {request.path}")
    print("[COOKIES]:", list(request.cookies.keys()))

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

# ================================
# MANEJO DE ERRORES GLOBALES
# ================================
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("routes.login"))

@app.errorhandler(403)
def forbidden(e):
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
        host='127.0.0.1',
        port=5000
    )