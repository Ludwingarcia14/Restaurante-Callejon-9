from pyspark.sql import SparkSession
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

spark = SparkSession.builder \
    .appName("MongoSpark") \
    .config("spark.mongodb.input.uri", "MONGO_URI") \
    .config("spark.mongodb.output.uri", "MONGO_URI") \
    .getOrCreate()

# Leer colección
df = spark.read.format("mongo").load()

# Opcional: mostrar esquema
df.printSchema()

# Mostrar las primeras 10 filas
df.show(10)
