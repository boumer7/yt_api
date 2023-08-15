import os
import sys
import hmac
import hashlib
from subprocess import run
import subprocess
from flask import Flask, request, jsonify
import yt_dlp
import logging

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Retrieve the secret token from the environment variable
SECRET_TOKEN = os.environ.get('SECRET_TOKEN')

def is_valid_signature(data, signature, secret):
    calculated_signature = 'sha1=' + hmac.new(secret.encode(), data, hashlib.sha1).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)

app.logger.setLevel(logging.DEBUG)

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature')
    event_type = request.headers.get('X-GitHub-Event')
    
    print("Signature:", signature)
    print("Event Type:", event_type)
    
    if not is_valid_signature(request.data, signature, SECRET_TOKEN):
        return "Unauthorized", 401

    if event_type == 'push':
        try:
            env = os.environ.copy()
            env['PATH'] = '/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

            # Get the absolute path to the deploy.sh script
            script_path = os.path.join(os.path.dirname(__file__), 'deploy.sh')

            subprocess.call(['sh', script_path], shell=True, env=env)

            return "Webhook received and deployment triggered."
        except subprocess.CalledProcessError as e:
            return f"Error triggering deployment: {str(e)}", 500
    
    return "Webhook received, but no action taken."

@app.route('/download_audio', methods=['GET'])
def download_audio():
    link = request.args.get('link')
    quality = request.args.get('quality', 'high')

    try:
        ydl_opts = {
            'format': f'bestaudio/{quality}',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_filename = f"downloads/{info_dict['title']}.mp3"

        return send_file(audio_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_video', methods=['GET'])
def download_video():
    link = request.args.get('link')
    quality = request.args.get('quality', 'high')

    try:
        ydl_opts = {
            'format': quality,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_filename = f"downloads/{info_dict['title']}.mp4"

        return send_file(video_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

