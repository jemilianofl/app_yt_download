from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
import yt_dlp
import subprocess
import os
import random

app = Flask(__name__)
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
        cookie_path = 'cookies.txt' 

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # User Agents rotativos para engañar un poco a YT
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        ua = random.choice(user_agents)

        # Opciones preliminares para sacar el título
        # Usamos el cliente 'android' que suele saltarse el bloqueo 429 mejor
        ydl_opts_info = {
            'quiet': True, 
            'cookiefile': cookie_path,
            'user_agent': ua,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'], # Prioridad a Android
                }
            }
        }

        # PASO 1: Obtener título
        try:
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'audio_descargado')
                safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        except Exception as e:
            # Si falla Android, intentamos un fallback genérico
            safe_title = "audio_descarga_yt"
            print(f"Advertencia obteniendo titulo: {e}")

        # PASO 2: Streaming
        def generate():
            cmd = [
                'yt-dlp',
                '--quiet',
                '--no-warnings',
                '-f', 'bestaudio/best',
                '-o', '-',
                '--cookiefile', cookie_path,
                '--user-agent', ua,
                # TRUCOS ANTI-BLOQUEO:
                '--extractor-args', 'youtube:player_client=android', # Fingir ser Android
                '--sleep-requests', '1', # Esperar 1 seg entre peticiones internas
                url
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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