"""
config/settings.py - Configuración Central de la Aplicación
============================================================
Centraliza todas las constantes de configuración de la aplicación.
Las variables sensibles se leen desde el archivo .env mediante python-dotenv.

NOTA: Este módulo NO inicializa Spark ni ninguna conexión.
      La sesión de Spark se gestiona de forma lazy en config/spark_config.py.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (si no han sido cargadas ya)
load_dotenv()

# ─────────────────────────────────────────────
# BASE DE DATOS
# ─────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "callejon9")

# ─────────────────────────────────────────────
# FLASK / SESIONES
# ─────────────────────────────────────────────
SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "22d6225b061b6b75979d7b4fd5bfb6993b32a66346c0d188fd6f3a37ac36698e"
)
FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
DEBUG: bool = FLASK_ENV == "development"

SESSION_TYPE: str = "filesystem"
SESSION_PERMANENT: bool = True
SESSION_USE_SIGNER: bool = True
# En producción cambiar a True y configurar HTTPS
SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE_SAMESITE: str = "Lax"
SESSION_COOKIE_NAME: str = "callejon9_session"

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
CORS_ORIGINS: list = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",
    "http://localhost:5000",
]

# ─────────────────────────────────────────────
# NOTIFICACIONES
# ─────────────────────────────────────────────
USE_LOCAL_SOCKET: bool = os.getenv("USE_LOCAL_SOCKET", "true").lower() == "true"
NODE_NOTIFICATIONS_URL: str = os.getenv("NODE_NOTIFICATIONS_URL", "http://localhost:8000")

# ─────────────────────────────────────────────
# SEGURIDAD / 2FA
# ─────────────────────────────────────────────
EMERGENCY_2FA_KEY: str = os.getenv("EMERGENCY_2FA_KEY")

# ─────────────────────────────────────────────
# SERVIDOR
# ─────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "5000"))
