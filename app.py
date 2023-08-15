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

@app.route('/download_audio', methods=['GET', 'POST'])
def download_audio():
    if request.method == 'GET':
        # Handle GET request, return a form or instructions for audio download
        return "This endpoint supports both GET and POST methods for audio download."

    if request.method == 'POST':
        data = request.json
        link = data.get('link')
        quality = data.get('quality', 'bestaudio/best')

        try:
            ydl_opts = {
                'format': quality,
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(link, download=True)
                audio_filepath = f"downloads/{info_dict['title']}.mp3"

            return jsonify({"status": "success", "message": "Audio downloaded successfully", "audio_filepath": audio_filepath})

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

@app.route('/download_video', methods=['GET', 'POST'])
def download_video():
    if request.method == 'GET':
        # Handle GET request, return a form or instructions for video download
        return "This endpoint supports both GET and POST methods for video download."

    if request.method == 'POST':
        data = request.json
        link = data.get('link')
        quality = data.get('quality', 'best')

        try:
            ydl_opts = {
                'format': quality,
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(link, download=True)
                video_filepath = f"downloads/{info_dict['title']}.mp4"

            return jsonify({"status": "success", "message": "Video downloaded successfully", "video_filepath": video_filepath})

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

