# config/spark_config.py
from pyspark.sql import SparkSession
import os

# 1. Variable global para almacenar la única sesión.
_spark_session = None

def get_spark_session(app_name="gestor_pymes_app"):
    """
    Devuelve la SparkSession existente o crea una nueva si _spark_session es None.
    """
    global _spark_session
    
    if _spark_session is None:
        # Lógica de creación solo si no existe
        spark = (
            SparkSession.builder
            .appName(app_name)
            .config("spark.driver.memory", "2g")
            .config("spark.executor.memory", "2g")
            .config("spark.sql.shuffle.partitions", "4")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        _spark_session = spark  # Almacenar la instancia creada
        print(f"✅ PySpark iniciado/configurado con app_name = {app_name}")
        
    return _spark_session # Devolver la instancia única
    
def stop_spark_session():
    """Detiene la sesión de Spark de forma segura."""
    global _spark_session
    if _spark_session is not None:
        _spark_session.stop()
        _spark_session = None
        print("🛑 SparkSession detenida.")