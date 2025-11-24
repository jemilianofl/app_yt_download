# Usamos una imagen ligera de Python
FROM python:3.9-slim

# 1. Instalamos FFmpeg (necesario para convertir a MP3)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# 2. Configuramos el directorio de trabajo
WORKDIR /app

# 3. Copiamos los requisitos e instalamos librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos el resto del código
COPY . .

# 5. Comando para iniciar el servidor (usando Gunicorn para producción)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "app:app"]