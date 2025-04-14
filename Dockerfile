FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para algunas bibliotecas Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de requisitos primero para aprovechar la caché de capas de Docker
COPY pyproject.toml ./

# Instalar dependencias
RUN pip install --no-cache-dir uv && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir redis

# Copiar el código del bot
COPY . .

# Crear un usuario no root para ejecutar el bot
RUN useradd -m botuser
USER botuser

# Comando para ejecutar el bot
CMD ["python", "main.py"]
