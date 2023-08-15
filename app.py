import os
import sys
import hmac
import hashlib
from subprocess import run
import subprocess
from flask import Flask, request, jsonify, send_file, redirect, make_response
import requests
import yt_dlp as youtube_dl
import logging
import json
import html

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
    video_link = request.args.get('link')
    quality = request.args.get('quality', 'high')  # Default to 'high' if not provided

    ydl_opts = {
        'format': 'best',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_link, download=False)
        formats = info_dict.get('formats', [])
        
        # Filter formats based on the presence of both audio and video
        filtered_formats = [f for f in formats if (
            'acodec' in f and 'vcodec' in f and f['acodec'] != 'none' and f['vcodec'] != 'none'
        )]
        
        # Determine the desired format based on quality
        if quality == 'low':
            format_id = '134'  # 480p format
        elif quality == 'medium':
            format_id = '22'   # 720p format
        elif quality == 'high':
            format_id = '137'  # 1080p format
        else:
            return "Invalid quality parameter."

        # Find the closest available format to the desired format
        selected_format = next((f for f in filtered_formats if f['format_id'] == format_id), None)
        if not selected_format:
            selected_format = min(filtered_formats, key=lambda f: abs(int(f['format_id']) - int(format_id)), default=None)

        if not selected_format:
            return f"No available format for quality: {quality}."

        video_url = selected_format.get('url')

        if not video_url:
            return "No video URL found for the selected format."

    return redirect(video_url)

def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s


def extract_subtitles_by_time(subtitle_data, start_time, end_time):
    extracted_lines = []

    events = subtitle_data.get("events", [])

    for event in events:
        t_start_ms = event.get("tStartMs", 0)
        d_duration_ms = event.get("dDurationMs", 0)

        t_start_seconds = t_start_ms / 1000
        t_end_seconds = t_start_seconds + (d_duration_ms / 1000)

        if start_time <= t_start_seconds <= end_time or start_time <= t_end_seconds <= end_time:
            segs = event.get("segs", [])
            for seg in segs:
                utf8_text = seg.get("utf8", "")
                extracted_lines.append(utf8_text)

    return extracted_lines

@app.route('/download_subtitles', methods=['GET'])
def download_subtitles():
    video_link = request.args.get('link')
    start_time_str = request.args.get('start_time', '00:00:00')
    end_time_str = request.args.get('end_time', '99:59:59')
    
    start_time = time_to_seconds(start_time_str)
    end_time = time_to_seconds(end_time_str)

    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': 'en',
            'subtitlesformat': 'srv1',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_link, download=False)

        subtitles = info_dict.get('subtitles', {}).get('en')

        if subtitles:
            if isinstance(subtitles, list):
                subtitle_url = subtitles[0]['url']
            else:
                subtitle_url = subtitles

            subtitle_data = requests.get(subtitle_url).json()

            extracted_subtitles = extract_subtitles_by_time(subtitle_data, start_time, end_time)
            
            response = {
                "language": "en",
                "subtitles": extracted_subtitles
            }

            return jsonify(response)
        else:
            return "No English subtitles available for the provided link."

    except Exception as e:
        return f"Error downloading subtitles: {str(e)}", 500

        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

