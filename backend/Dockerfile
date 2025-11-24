# Cambiamos 3.9 por 3.11
FROM python:3.11-slim

# ... el resto del archivo sigue igual ...
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

WORKDIR /app
# Asegúrate de usar la solución que te di antes para el COPY requirements.txt
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "app:app"]