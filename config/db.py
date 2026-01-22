import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if not MONGO_URI:
    raise ValueError("Error: la variable MONGO_URI no está definida en el archivo .env")

if not MONGO_DB_NAME:
    raise ValueError("Error: la variable MONGO_DB_NAME no está definida en el archivo .env")

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    print(f"[MongoDB] Conectado correctamente a la base '{MONGO_DB_NAME}'")
except Exception as e:
    print("[MongoDB] Error de conexión:", str(e))
    raise e
