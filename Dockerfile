# 1. Base: Usamos una imagen slim de Python, que es más estable
# 'bullseye' es la distribución de Debian que viene con Python 3.11
FROM python:3.11-slim-bullseye

# 2. Instalar Java (OpenJDK 17) y herramientas del sistema operativo
# Java es esencial para PySpark. Las libs son necesarias para PDF/imagen (pdfplumber, pdf2image, etc.)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk openjdk-17-jre \
    python3-dev build-essential libfontconfig1 libsm6 libxext6 libxrender1 \
    tesseract-ocr tesseract-ocr-spa poppler-utils ghostscript && \
    rm -rf /var/lib/apt/lists/*

# 3. Configurar directorios
WORKDIR /app
# Crear la carpeta de sesiones de Flask, ya que app.py espera que exista
RUN mkdir -p flask_session

# 4. Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Configurar Variables de Entorno de PySpark (Apuntando a la instalación de Java)
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV PYSPARK_PYTHON=/usr/local/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python

# 6. Copiar el resto del código
COPY . .

# 7. Configurar el comando de inicio para el servidor de producción Gunicorn
EXPOSE 5000
# CMD en su Dockerfile
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
