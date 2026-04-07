FROM python:3.11-slim

# Instala libsqlite3 e dependências de sistema que o swisseph precisa
RUN apt-get update && apt-get install -y \
    libsqlite3-dev \
    sqlite3 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE $PORT

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
