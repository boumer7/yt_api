import os
import sys
import hmac
import hashlib
from subprocess import run
import subprocess
from flask import Flask, request, jsonify, send_file, redirect
import yt_dlp as youtube_dl
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
    quality = request.args.get('quality', 'bestaudio')  # Default to 'bestaudio' if not provided

    if quality == 'low':
        quality = 'worstaudio'
    elif quality == 'medium':
        quality = '140'
    elif quality == 'high':
        quality = 'bestaudio'
    
    ydl_opts = {
        'format': quality,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=False)
        audio_url = None
        
        # Find a direct audio URL (not .m3u8)
        for f in info_dict['formats']:
            if 'acodec' in f and f['acodec'] != 'none' and 'url' in f:
                audio_url = f['url']
                break
        
        if not audio_url:
            return "No playable audio format found."

    return redirect(audio_url)

@app.route('/download_video', methods=['GET'])
def download_video():
    link = request.args.get('link')
    quality = request.args.get('quality', 'high')  # Default to 'high' if not provided

    if quality == 'low':
        quality = '480'
    elif quality == 'medium':
        quality = '720'
    elif quality == 'high':
        quality = '1080'
    
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        '--embed-subs': True,  # Embed subtitles (include audio)
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=False)
        video_url = info_dict['url']

    return redirect(video_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

