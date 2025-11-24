from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
import yt_dlp
import subprocess
import os

app = Flask(__name__)
# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    url = data.get('url')
    
    # Configuración de Cookies
    cookie_path = '/etc/secrets/cookies.txt'
    if not os.path.exists(cookie_path):
        cookie_path = 'cookies.txt' # Fallback para local

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # PASO 1: Obtener el título primero (Rápido, sin descargar el audio aun)
        with yt_dlp.YoutubeDL({'quiet': True, 'cookiefile': cookie_path}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'audio_descargado')
            # Limpiamos el título
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()

        # PASO 2: Función Generadora (Streaming)
        # Esto envía los datos al usuario a medida que llegan de YouTube
        def generate():
            # Comando para ejecutar yt-dlp y enviar el audio a la consola (stdout)
            cmd = [
                'yt-dlp',
                '--quiet',           # No mostrar logs basura
                '--no-warnings',
                '-f', 'bestaudio/best', # Mejor calidad de audio
                '-o', '-',           # <--- IMPORTANTE: '-' significa enviar a Salida Estándar (no archivo)
                '--cookiefile', cookie_path, # Usamos tus cookies
                url
            ]
            
            # Iniciamos el proceso
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Leemos en trozos de 4KB y los enviamos al navegador
            try:
                while True:
                    chunk = process.stdout.read(4096)
                    if not chunk:
                        break
                    yield chunk
                process.wait()
            except Exception as e:
                process.kill()
                print(f"Error en el stream: {e}")

        # PASO 3: Responder con el Stream
        # Nota: Usamos .webm o .m4a porque convertir a MP3 en tiempo real es inestable
        return Response(
            stream_with_context(generate()),
            headers={
                "Content-Disposition": f"attachment; filename={safe_title}.webm",
                "Content-Type": "audio/webm"
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)