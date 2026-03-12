FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar salida stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema operativo y Node.js para el Bridge de WhatsApp
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    curl \
    procps \
    psmisc \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt /app/

# Instalar el stack de dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias de Node.js
COPY skills/sales-assistant/scripts/package.json /app/skills/sales-assistant/scripts/
RUN cd /app/skills/sales-assistant/scripts && npm install

# Copiar el codigo fuente
COPY . /app/

# Puerto FastAPI por defecto del Core
EXPOSE 8001
# Puerto del Dashboard
EXPOSE 5001

# Ejecutar el orquestador principal
CMD ["python", "start_zodit.py"]
