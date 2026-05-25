# 1. Base: Usamos una imagen slim de Python, que es más estable
# 'bullseye' es la distribución de Debian que viene con Python 3.11
FROM python:3.11-slim-bullseye

# 2. Instalar herramientas del sistema operativo
RUN apt-get update && \
    apt-get install -y python3-dev build-essential libfontconfig1 libsm6 libxext6 libxrender1 \
    tesseract-ocr tesseract-ocr-spa poppler-utils ghostscript && \
    rm -rf /var/lib/apt/lists/*

# 3. Configurar directorios
WORKDIR /app
# Crear la carpeta de sesiones de Flask, ya que app.py espera que exista
RUN mkdir -p flask_session

# 4. Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código
COPY . .

# 6. Configurar el comando de inicio — eventlet requerido para Flask-SocketIO
EXPOSE 5000
CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
