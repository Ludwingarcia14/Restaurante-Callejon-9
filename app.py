"""
Módulo Principal de la Aplicación Flask - Restaurante Callejón 9
"""
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
from flask_socketio import emit, join_room
from extensions import socketio
from datetime import datetime
import os
import sys

from routes import routes_bp

# ================================
# CONFIG PYSPARK (si lo usas)
# ================================
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


app = Flask(__name__, template_folder="resources/views", static_folder="static")
from bson import ObjectId
from flask.json.provider import DefaultJSONProvider
from datetime import datetime

class MongoJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_provider_class = MongoJSONProvider
app.json = MongoJSONProvider(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Configuración de CORS
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
_origenes_env = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
lista_origenes = list(set(_origenes_base + _origenes_env))

CORS(app, supports_credentials=True, resources={
    r"/*": {"origins": lista_origenes},
})

# ================================
# SOCKET.IO
# ================================
socketio.init_app(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    manage_session=False
)

# Registrar Blueprint de rutas (SOLO UNA VEZ)
app.register_blueprint(routes_bp)

# Registrar rutas de reportes
from routes import register_reports_routes
register_reports_routes(app)

# CLAVE SECRETA
app.secret_key = os.getenv("SECRET_KEY", "22d6225b061b6b75979d7b4fd5bfb6993b32a66346c0d188fd6f3a37ac36698e")

session_dir = os.path.join(os.getcwd(), "flask_session")
os.makedirs(session_dir, exist_ok=True)

# Limpiar sesiones antiguas al iniciar (más de 24 horas)
import time
try:
    for archivo in os.listdir(session_dir):
        filepath = os.path.join(session_dir, archivo)
        if os.path.isfile(filepath):
            # Eliminar archivos de sesión mayores a 24 horas
            if os.path.getmtime(filepath) < time.time() - 86400:
                os.remove(filepath)
                print(f"🗑️  Sesión antigua eliminada: {archivo}")
except Exception as e:
    print(f"⚠️  Error limpiando sesiones: {e}")

# Limpiar sesiones antiguas al iniciar
import time
try:
    for archivo in os.listdir(session_dir):
        filepath = os.path.join(session_dir, archivo)
        if os.path.isfile(filepath):
            # Eliminar archivos de sesión mayores a 24 horas
            if os.path.getmtime(filepath) < time.time() - 86400:
                os.remove(filepath)
                print(f"🗑️  Sesión antigua eliminada: {archivo}")
except Exception as e:
    print(f"⚠️  Error limpiando sesiones: {e}")

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = session_dir
app.config["SESSION_PERMANENT"] = False  
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # True en producción con HTTPS
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_NAME"] = "callejon9_session"
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

# Inicializar extensión de sesiones
Session(app)

# ================================
# CONTEXT
# ================================
@app.context_processor
def inject_now():
    return {"now": datetime.now}

# ================================
# LOG REQUEST
# ================================
@app.before_request
def log_request():
    if request.path.startswith("/static"):
        return
    print(f"\n[REQ] {request.method} {request.path}")
    print("[COOKIES]:", request.cookies.keys())

# ================================
# SOCKET EVENTS
# ================================
@socketio.on("connect")
def socket_connect(auth):
    print("[SOCKET] Conectado")
    print("Auth:", auth)

@socketio.on("disconnect")
def socket_disconnect():
    print("[SOCKET] Desconectado")

@socketio.on("join_room")
def on_join_room(room):
    join_room(room)
    print(f"📥 Cliente unido a sala: {room}")

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
# ERRORES
# ================================
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("routes.login"))

@app.errorhandler(403)
def forbidden(e):
    return redirect(url_for("routes.login"))

# ================================
# RUN
# ================================
if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    import platform
    is_windows = platform.system() == "Windows"
    
    print("=" * 60)
    print("🍽️ CALLEJÓN 9 - SOCKET.IO ACTIVO")
    print(f"📍 http://127.0.0.1:5000")
    print(f"📍 http://{local_ip}:5000")
    print("=" * 60)
    reloader_config = not is_windows  
    
    print(f" Auto-reload: {'Activado' if reloader_config else 'Desactivado (Windows)'}")
    print("=" * 60 + "\n")
    
    socketio.run(
        app,
        debug=True,
        use_reloader=reloader_config,
        host='0.0.0.0',
        port=5000
    )