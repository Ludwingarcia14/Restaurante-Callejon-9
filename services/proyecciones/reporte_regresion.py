# ==========================================
# DASHBOARD DE REGRESIÓN LINEAL DE LIQUIDACIONES
# ==========================================

import streamlit as st
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import RegressionEvaluator
# (Has quitado CrossValidator, lo cual es más simple y rápido)
from datetime import datetime, timedelta
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# ============================
# 🔧 CONFIGURACIÓN INICIAL
# ============================
st.set_page_config(page_title="Regresión de Liquidaciones", layout="wide")

st.title("📈 Análisis de Regresión Lineal - Liquidaciones")
st.markdown("Explora la tendencia de los montos liquidados usando regresión lineal.")

# ============================
# ⚙️ CONEXIÓN A MONGODB
# ============================
# Cargar variables de entorno desde el archivo .env
load_dotenv() 

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION = "prestamos"

@st.cache_data(ttl=300)
def cargar_datos():
    # Esta función ahora usará automáticamente las variables cargadas de .env
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    data = list(db[COLLECTION].find({
        "prestamo_estado": "Pagado"  # O "Liquidado", asegúrate que este sea el estado correcto
    }))
    client.close()
    return pd.DataFrame(data)

df = cargar_datos()

if df.empty:
    st.warning("No hay préstamos pagados registrados en MongoDB.")
    st.stop()

# ============================
# 🧹 LIMPIEZA Y PREPROCESAMIENTO
# ============================
df["prestamo_fecha_vencimiento"] = pd.to_datetime(df["prestamo_fecha_vencimiento"])
df["prestamo_monto"] = df["prestamo_monto"].astype(float)

# Rango de fechas dinámico
min_fecha = df["prestamo_fecha_vencimiento"].min()
max_fecha = df["prestamo_fecha_vencimiento"].max()

col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input("📅 Desde", min_fecha)
with col2:
    fecha_fin = st.date_input("📅 Hasta", max_fecha)

# Filtrar por rango
df_filtrado = df[(df["prestamo_fecha_vencimiento"] >= pd.to_datetime(fecha_inicio)) &
                 (df["prestamo_fecha_vencimiento"] <= pd.to_datetime(fecha_fin))]

if df_filtrado.empty:
    st.warning("No hay registros en el rango de fechas seleccionado.")
    st.stop()

# ============================
# 🧮 ENTRENAMIENTO REGRESIÓN LINEAL (PySpark)
# ============================
spark = SparkSession.builder \
    .appName("RegresionLiquidaciones") \
    .config("spark.python.worker.reuse", "true") \
    .config("spark.network.timeout", "600s") \
    .config("spark.executor.heartbeatInterval", "60s") \
    .getOrCreate()

if len(df_filtrado) < 2:
    st.warning("No hay suficientes datos para entrenar la regresión (mínimo 2 registros).")
    spark.stop()
    st.stop()

# Crear DataFrame de Spark
fecha_base = df_filtrado["prestamo_fecha_vencimiento"].min()

# --- INICIO DE LA MODIFICACIÓN ---
# Corregido para evitar el "SettingWithCopyWarning"
df_filtrado.loc[:, "dias"] = (df_filtrado["prestamo_fecha_vencimiento"] - fecha_base).dt.days
# --- FIN DE LA MODIFICACIÓN ---

sdf = spark.createDataFrame(df_filtrado[["dias", "prestamo_monto"]])

# VectorAssembler
assembler = VectorAssembler(inputCols=["dias"], outputCol="features")
sdf = assembler.transform(sdf).select("features", "prestamo_monto")

# Entrenar modelo simple
lr = LinearRegression(featuresCol="features", labelCol="prestamo_monto")
model = lr.fit(sdf)

# ============================
# 📊 RESULTADOS DEL MODELO
# ============================
predicciones_spark = model.transform(sdf)
predicciones = predicciones_spark.toPandas()
predicciones["fecha"] = df_filtrado["prestamo_fecha_vencimiento"].values

evaluator = RegressionEvaluator(labelCol="prestamo_monto", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predicciones_spark)
r2 = model.summary.r2

st.subheader("📏 Resultados del Modelo")
col1, col2 = st.columns(2)
col1.metric("RMSE (Error Cuadrático Medio)", f"{rmse:,.2f}")
col2.metric("R² (Coeficiente de Determinación)", f"{r2:.3f}")

# ============================
# 🔮 PROYECCIÓN FUTURA
# ============================
st.subheader("🔮 Proyección de Tendencia")

dias_proy = st.slider("Extender proyección (días):", 0, 180, 60)
dias_futuro = list(range(df_filtrado["dias"].max(), df_filtrado["dias"].max() + dias_proy))
sdf_futuro = spark.createDataFrame(pd.DataFrame({"dias": dias_futuro}))
sdf_futuro = assembler.transform(sdf_futuro)

pred_futuro = model.transform(sdf_futuro).toPandas()
pred_futuro["fecha"] = [fecha_base + timedelta(days=int(d)) for d in dias_futuro]

# ============================
# 📉 VISUALIZACIONES
# ============================
st.subheader("📈 Tendencia Histórica y Proyección")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=predicciones["fecha"], y=predicciones["prestamo_monto"],
    mode="markers", name="Datos Reales", marker=dict(color="skyblue", size=8)
))
fig.add_trace(go.Scatter(
    x=predicciones["fecha"], y=predicciones["prediction"],
    mode="lines", name="Tendencia Actual", line=dict(color="blue", width=2)
))
fig.add_trace(go.Scatter(
    x=pred_futuro["fecha"], y=pred_futuro["prediction"],
    mode="lines", name="Proyección Futura", line=dict(color="red", dash="dot", width=2)
))

fig.update_layout(
    xaxis_title="Fecha de Liquidación",
    yaxis_title="Monto Liquidado (MXN)",
    template="plotly_white",
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# ============================
# 📋 Tabla Detallada
# ============================
st.subheader("📋 Detalle de Liquidaciones")
st.dataframe(df_filtrado[["datbasicos_clave", "prestamo_monto", "prestamo_fecha_vencimiento", "prestamo_estado"]])

# ============================
# 🧠 Cierre
# ============================
st.success("✅ Modelo de regresión ejecutado correctamente.")
spark.stop()