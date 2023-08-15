from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data['url']
    output_format = data.get('format', 'best')

    try:
        subprocess.run(['yt-dlp', '-f', output_format, '-o', 'output.%(ext)s', url], check=True)
        return jsonify({"status": "success", "message": "Download complete!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
