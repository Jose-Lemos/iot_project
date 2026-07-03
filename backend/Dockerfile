# Usamos una imagen de Python más reciente y robusta
FROM python:3.12-slim

# Evita que Python escriba archivos .pyc y almacene en caché
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos dependencias del sistema necesarias para compilar librerías
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Actualizamos pip antes de instalar nada
RUN pip install --upgrade pip

# Instalamos las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]