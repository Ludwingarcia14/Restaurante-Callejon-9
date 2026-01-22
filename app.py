"""
Módulo Principal de la Aplicación Flask

Este archivo inicializa el servidor Flask, configura las integraciones clave como CORS,
Sesiones y PySpark, y define la lógica de depuración para las peticiones entrantes.
"""

from flask import Flask, request, session, jsonify
from flask_cors import CORS
from routes import routes_bp
import os
import sys
import datetime
import jwt
from flask_session import Session
from config.spark_config import get_spark_session

# --- 🔧 CONFIGURACIÓN DE ENTORNO ---
# Corregir error común "python3 not found" en entornos Windows
# Esto asegura que PySpark utilice el mismo intérprete de Python que está ejecutando Flask.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# Inicialización de la aplicación Flask
# Especificamos la carpeta 'resources/views' para plantillas (templates)
app = Flask(__name__, template_folder="resources/views")

# --- 🌐 CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing) ---
# Se define una lista de orígenes permitidos para acceder a la API.
# Esto es esencial para el desarrollo con frontends en diferentes puertos (ej. React)
# y para aceptar peticiones desde un servidor de producción o apps móviles.
lista_origenes = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",
    "https://127.0.0.1:5000",
    "http://potencialpyme.test",
    "http://potencialpyme.test/public/",
    "https://pyme-notificaciones.onrender.com/"
]

# Aplicamos la configuración de CORS
CORS(app, 
     # Aplicar a todas las rutas y restringir a la lista de orígenes
     resources={r"/*": {"origins": lista_origenes}}, 
     # Permitir que las cookies de sesión se envíen en peticiones entre dominios
     supports_credentials=True
)

# --- 🕵️‍♂️ DEPURACIÓN Y LOGGING DE PETICIONES ---
@app.before_request
def log_request_info():
    """
    Hook que se ejecuta antes de CADA petición.
    Imprime información útil de la petición y el estado de la sesión.
    """
    # Filtramos para evitar logs de archivos estáticos (CSS, JS, imágenes)
    if request.path.startswith("/static"):
        return

    origin = request.headers.get('Origin')
    print(f"\n📡 Petición recibida en: {request.path}")
    print(f"   📍 Desde Origin: {origin}")
    print(f"   🍪 Cookies recibidas: {list(request.cookies.keys())}")
    
    # Verificar si el usuario ha iniciado sesión
    if 'usuario_id' in session:
        print(f"   ✅ Usuario autenticado ID: {session['usuario_id']}")
    else:
        print(f"   ❌ Sesión vacía (El usuario debe hacer Login de nuevo)")
# ---------------------------------------------

# Registrar el Blueprint que contiene todas las rutas de la aplicación
app.register_blueprint(routes_bp)

# 🔑 CLAVE SECRETA FIJA
# Esencial para firmar las cookies de sesión y que las sesiones no mueran 
# al reiniciar el servidor en desarrollo.
app.secret_key = "22d6225b061b6b75979d7b4fd5bfb6993b32a66346c0d188fd6f3a37ac36698e"

# --- Configuración de Sesiones (Flask-Session) ---
# Aseguramos que la carpeta de almacenamiento de sesiones exista
session_dir = os.path.join(os.getcwd(), "flask_session")
if not os.path.exists(session_dir):
    os.makedirs(session_dir)

# Configurar el tipo de almacenamiento de la sesión
app.config["SESSION_TYPE"] = "filesystem" 
app.config["SESSION_FILE_DIR"] = session_dir
app.config["SESSION_PERMANENT"] = True    # Sesiones persistentes (no expiran al cerrar el navegador)
app.config["SESSION_USE_SIGNER"] = True   # Firmar el ID de sesión para prevenir manipulación

# --- 🚨 AJUSTES DE DEBUG (HTTP) 🚨 ---
# Desactivado: Para permitir la conexión sobre HTTP sin SSL
app.config["SESSION_COOKIE_SECURE"] = False 
# 'Lax' es usado en desarrollo local con HTTP (si fuera 'None', requeriría Secure=True)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax" 

# Inicializar la extensión de Sesiones con la configuración de la aplicación
Session(app)

# Inicializar PySpark
# Obtener una sesión de Spark con un nombre de aplicación
spark = get_spark_session("gestor_pymes_app")
# Almacenar el objeto Spark en la configuración de la aplicación para acceso global
app.config["spark"] = spark

# Reutilizar la clave secreta para firmar tokens JWT para la capa de sockets
app.config['SOCKET_JWT_SECRET'] = app.secret_key

# --- 🔒 Configuración SSL (Comentada para usar HTTP en debug) ---
# CERT_FILE = os.path.join('config', 'localhost+2.pem')
# KEY_FILE = os.path.join('config', 'localhost+2-key.pem')
# contexto_ssl = (CERT_FILE, KEY_FILE)

if __name__ == "__main__":
    # Obtener y mostrar la IP real de la máquina para acceso móvil/remoto
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"🚀 Iniciando servidor Flask (MODO HTTP)")
    print(f"   - Accesible en PC:     http://127.0.0.1:5000")
    print(f"   - Accesible en Móvil:  http://{local_ip}:5000 (o http://10.0.2.2:5000 en emulador)")
    
    # Iniciar el servidor
    app.run(
        debug=True, 
        use_reloader=True, 
        # ssl_context=contexto_ssl, # <--- COMENTADO PARA USAR HTTP
        # Cambiado a '0.0.0.0' para aceptar conexiones desde el exterior (móviles/LAN)
        host='0.0.0.0',
        port=5000
    )
