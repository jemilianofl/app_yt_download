from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
# Habilitar CORS para que Vercel pueda hablar con Render.
# En producción, cambia "*" por "https://tu-proyecto.vercel.app" para más seguridad.
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Generamos un nombre único para evitar choques entre usuarios
    temp_id = str(uuid.uuid4())
    temp_filename = f"download_{temp_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{temp_filename}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        # Importante: usar /tmp en entornos linux como Render
        'paths': {'home': '/tmp'} 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio')
            # Limpiamos el título de caracteres raros para la descarga
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()

        # La ruta del archivo generado (en /tmp)
        file_path = f"/tmp/{temp_filename}.mp3"

        # ESTO ES CRUCIAL: Programar el borrado del archivo después de enviarlo
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting file: {e}")
            return response

        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=f"{safe_title}.mp3",
            mimetype="audio/mpeg"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)