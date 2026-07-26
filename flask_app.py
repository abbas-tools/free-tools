from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import re
import time
import logging
import tempfile
from urllib.parse import urlparse

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# HTML Template with proper routes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Badass Tools Hub</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background-color: var(--tg-theme-bg-color, #1f2125);
            color: var(--tg-theme-text-color, #ffffff);
            text-align: center;
            padding: 20px 15px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 450px;
            width: 100%;
            margin: auto;
        }
        .logo {
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 14px;
            opacity: 0.7;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            padding: 25px 20px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .input-wrapper {
            position: relative;
            margin-bottom: 15px;
        }
        input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            font-size: 15px;
            transition: all 0.3s ease;
        }
        input[type="text"]:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
        }
        input[type="text"]::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 5px;
        }
        .btn {
            padding: 14px 10px;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #fff;
        }
        .btn:active {
            transform: scale(0.95);
        }
        .btn-video {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .btn-audio {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        #result {
            margin-top: 20px;
            min-height: 60px;
        }
        .loader {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 0.8s linear infinite;
            margin: 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .video-info {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
        }
        .video-info img {
            max-width: 100%;
            border-radius: 8px;
            margin: 8px 0;
            max-height: 200px;
            object-fit: cover;
            width: 100%;
        }
        .video-title {
            font-weight: 600;
            font-size: 15px;
            margin: 8px 0;
        }
        .video-meta {
            font-size: 12px;
            opacity: 0.6;
            margin: 5px 0;
        }
        .btn-download {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: #000;
            padding: 14px;
            border-radius: 12px;
            border: none;
            font-weight: 700;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: block;
            text-align: center;
        }
        .btn-download:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 25px rgba(67, 233, 123, 0.3);
        }
        .error-box {
            background: rgba(232, 65, 24, 0.15);
            color: #ff6b6b;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(232, 65, 24, 0.3);
            font-size: 14px;
        }
        .supported {
            margin-top: 20px;
            font-size: 11px;
            opacity: 0.4;
            letter-spacing: 0.5px;
        }
        .status-text {
            font-size: 14px;
            opacity: 0.8;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">⚡ Badass Tools Hub</div>
        <div class="subtitle">🎥 Social Media Video & Audio Downloader</div>

        <div class="card">
            <div class="input-wrapper">
                <input type="text" id="videoUrl" placeholder="Paste video link here..." value="https://youtu.be/aMWuGj0FCYg">
            </div>
            
            <div class="btn-group">
                <button class="btn btn-video" onclick="fetchMedia('video')">🎬 Video</button>
                <button class="btn btn-audio" onclick="fetchMedia('audio')">🎵 Audio</button>
            </div>
            <div id="result"></div>
        </div>

        <div class="supported">Supported: YouTube, Instagram, Facebook, Twitter, TikTok & more</div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        if (tg) tg.expand();

        function fetchMedia(type) {
            let url = document.getElementById('videoUrl').value.trim();
            let resultDiv = document.getElementById('result');

            if (!url) {
                resultDiv.innerHTML = `<div class="error-box">⚠️ Please paste a valid video link first!</div>`;
                if (tg) tg.showAlert("Please paste a valid video link!");
                return;
            }

            resultDiv.innerHTML = `
                <div class="loader"></div>
                <div class="status-text">⏳ Processing your ${type === 'video' ? 'video' : 'audio'}...</div>
            `;

            // Try both endpoints
            let endpoint = '/process-media';
            
            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, type: type })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    let html = `<div class="video-info">`;
                    
                    if (data.thumbnail) {
                        html += `<img src="${data.thumbnail}" alt="Thumbnail" onerror="this.style.display='none'">`;
                    }
                    
                    html += `<div class="video-title">${data.title || 'Media'}</div>`;
                    
                    if (data.duration) {
                        let minutes = Math.floor(data.duration / 60);
                        let seconds = data.duration % 60;
                        html += `<div class="video-meta">⏱️ ${minutes}:${seconds.toString().padStart(2, '0')}</div>`;
                    }
                    
                    if (data.file_size) {
                        let size = data.file_size;
                        if (size > 1024 * 1024) {
                            size = (size / (1024 * 1024)).toFixed(2) + ' MB';
                        } else if (size > 1024) {
                            size = (size / 1024).toFixed(2) + ' KB';
                        } else {
                            size = size + ' bytes';
                        }
                        html += `<div class="video-meta">📊 ${size}</div>`;
                    }
                    
                    if (data.platform) {
                        html += `<div class="video-meta">📱 ${data.platform}</div>`;
                    }
                    
                    html += `</div>`;
                    
                    html += `<a href="${data.download_link}" class="btn-download" target="_blank">⬇️ Download ${type === 'video' ? 'Video' : 'Audio'}</a>`;
                    
                    resultDiv.innerHTML = html;
                    
                    if (tg) tg.showAlert("✅ Ready to download!");
                } else {
                    resultDiv.innerHTML = `<div class="error-box">❌ ${data.message || 'Failed to process'}</div>`;
                    if (tg) tg.showAlert("❌ Error: " + data.message);
                }
            })
            .catch(err => {
                console.error('Error:', err);
                resultDiv.innerHTML = `<div class="error-box">❌ Error: ${err.message}</div>`;
                if (tg) tg.showAlert("❌ Error occurred!");
            });
        }

        // Auto-focus on input
        document.getElementById('videoUrl').focus();
        
        // Enter key support
        document.getElementById('videoUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                fetchMedia('video');
            }
        });
    </script>
</body>
</html>
"""

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

def detect_platform(url):
    """Detect platform from URL"""
    platforms = {
        'youtube.com': 'YouTube',
        'youtu.be': 'YouTube',
        'instagram.com': 'Instagram',
        'tiktok.com': 'TikTok',
        'facebook.com': 'Facebook',
        'fb.watch': 'Facebook',
        'twitter.com': 'Twitter',
        'x.com': 'Twitter',
        'vimeo.com': 'Vimeo',
        'dailymotion.com': 'Dailymotion',
    }
    
    parsed = urlparse(url)
    for domain, platform in platforms.items():
        if domain in parsed.netloc:
            return platform
    return 'Unknown'

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process-media', methods=['POST', 'GET'])
def process_media():
    """Process media with robust error handling"""
    if request.method == 'GET':
        return jsonify({'success': False, 'message': 'Please use POST method'}), 405
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400
        
        video_url = data.get('url', '').strip()
        media_type = data.get('type', 'video')
        
        if not video_url:
            return jsonify({'success': False, 'message': 'URL is required'}), 400
        
        if not video_url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': 'Invalid URL format'}), 400
        
        logger.info(f"Processing {media_type}: {video_url}")
        
        # Configure yt-dlp options
        if media_type == 'audio':
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'format': 'bestaudio/best',
                'http_headers': get_headers(),
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                }
            }
        else:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'format': 'best[ext=mp4]/best',
                'http_headers': get_headers(),
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                }
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if not info:
                return jsonify({'success': False, 'message': 'Could not extract video information'}), 500
            
            # Get download URL
            download_url = None
            
            if info.get('url'):
                download_url = info['url']
            elif info.get('formats'):
                if media_type == 'audio':
                    # Get best audio format
                    for f in info['formats']:
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            download_url = f.get('url')
                            break
                    if not download_url:
                        download_url = info['formats'][-1].get('url')
                else:
                    # Get best video format
                    best_format = None
                    for f in info['formats']:
                        if f.get('ext') == 'mp4' and f.get('height'):
                            if not best_format or f['height'] > best_format.get('height', 0):
                                best_format = f
                    if best_format:
                        download_url = best_format.get('url')
                    if not download_url and info['formats']:
                        download_url = info['formats'][-1].get('url')
            
            if not download_url:
                return jsonify({'success': False, 'message': 'Could not get download URL'}), 500
            
            # Get title
            title = info.get('title', 'Media')
            
            return jsonify({
                'success': True,
                'title': title,
                'download_link': download_url,
                'platform': detect_platform(video_url),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'file_size': info.get('filesize', 0) or info.get('filesize_approx', 0),
                'type': media_type
            })
            
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        return jsonify({'success': False, 'message': f'Download error: {str(e)[:100]}'}), 500
    except yt_dlp.utils.ExtractorError as e:
        logger.error(f"Extractor error: {e}")
        return jsonify({'success': False, 'message': f'URL error: {str(e)[:100]}'}), 400
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)[:100]}'}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)