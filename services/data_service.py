# services/data_service.py
from pyspark.sql import SparkSession
# Importa la configuración del archivo de configuración
from config.settings import MONGO_URI
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window

# --- Inicialización Única ---

SPARK = SparkSession.builder \
    .appName("UsuariosAdmin") \
    .config("spark.mongodb.input.uri", MONGO_URI) \
    .getOrCreate()

# Cargar y Cachear el DataFrame
USUARIOS_DF = SPARK.read.format("mongo").load().cache()
# ... (Aquí va la selección de columnas y el .cache() como en la respuesta anterior) ...

# --- Lógica de la API (función que llama routes.py) ---

def get_paginated_admin_data(search_value, start, length):
    # Aquí se aplica el filtro, conteo, y paginación sobre USUARIOS_DF
    # ... (Tu lógica de filtrado y paginación con Spark) ...
    
    # IMPORTANTE: Aquí se realiza el .collect()
    data = [row.asDict() for row in df_page.collect()]
    return total_records, total_filtered, data