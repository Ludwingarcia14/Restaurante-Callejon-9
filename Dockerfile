FROM python:3.11-slim-bullseye

RUN apt-get update && \
    apt-get install -y build-essential libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p flask_session

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD gunicorn --workers 1 --worker-class gthread --threads 4 --bind 0.0.0.0:$PORT app:app
