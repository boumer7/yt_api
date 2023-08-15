import os
import hmac
import hashlib
from subprocess import run
from flask import Flask, request, jsonify
import yt_dlp

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Retrieve the secret token from the environment variable
SECRET_TOKEN = os.environ.get('SECRET_TOKEN')

@app.route('/webhook', methods=['POST'])
def webhook():
    # Validate the incoming request using the secret token
    signature = request.headers.get('X-Hub-Signature')
    if not is_valid_signature(request.data, signature, SECRET_TOKEN):
        return "Unauthorized", 401

    # Parse the payload JSON
    payload = request.json

    # Check if it's a push event
    if 'push' in payload.get('event', ''):
        # Run the deployment script
        run(["bash", "deploy.sh"])

        return "Webhook received and deployment triggered."

    return "Webhook received, but no action taken."

def is_valid_signature(data, signature, secret):
    calculated_signature = 'sha1=' + hmac.new(secret.encode(), data, hashlib.sha1).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)

@app.route('/download_audio', methods=['POST'])
def download_audio():
    data = request.json
    video_url = data.get('video_url')

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            audio_filepath = f"downloads/{info_dict['title']}.mp3"

        return jsonify({"status": "success", "message": "Audio downloaded successfully", "audio_filepath": audio_filepath})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_video', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('video_url')

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_filepath = f"downloads/{info_dict['title']}.mp4"

        return jsonify({"status": "success", "message": "Video downloaded successfully", "video_filepath": video_filepath})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

