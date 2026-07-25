import os
import re
import requests
import telebot
import yt_dlp
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file
import tempfile
import uuid
from urllib.parse import urlparse, quote
import mimetypes

# --- CONFIGURATION ---
TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Directory for storing uploaded cricket videos
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory database simulation for Cricket Profiles & Videos
CRICKET_DATABASE = {
    "babar-azam": {
        "name": "Babar Azam 👑",
        "bio": "Master class cover drives and match-winning knocks.",
        "videos": [
            {"title": "Babar Azam Best Cover Drives 2026", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        ]
    },
    "virat-kohli": {
        "name": "Virat Kohli 🔥",
        "bio": "The Run Machine and chase master highlights.",
        "videos": [
            {"title": "Kohli Epic Chase Masterclass", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        ]
    },
    "shaheen-afridi": {
        "name": "Shaheen Afridi ⚡",
        "bio": "First-over lethal swinging yorkers.",
        "videos": [
            {"title": "Shaheen Afridi First Over Wickets", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        ]
    }
}

# --- MAIN WEB APP HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Badass Tools Hub & Cricket Arena</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: var(--tg-theme-bg-color, #121418);
            --text-color: var(--tg-theme-text-color, #ffffff);
            --card-bg: rgba(255, 255, 255, 0.04);
            --btn-color: var(--tg-theme-button-color, #ff4b2b);
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: var(--text-color);
            text-align: center;
            padding: 10px;
            margin: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        .container {
            max-width: 420px;
            margin: auto;
            padding: 10px;
            width: 100%;
            box-sizing: border-box;
        }
        h2 {
            margin-bottom: 2px;
            font-size: 24px;
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            font-size: 12px;
            opacity: 0.7;
            margin-bottom: 15px;
        }
        .nav-tabs {
            display: flex;
            justify-content: space-around;
            background: rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 5px;
            margin-bottom: 15px;
        }
        .nav-tab {
            padding: 8px 15px;
            font-size: 13px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
            border-radius: 8px;
            transition: 0.2s;
        }
        .nav-tab.active {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: #fff;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .card {
            background-color: var(--card-bg);
            padding: 18px;
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 15px;
            text-align: left;
        }
        input[type="text"], select, input[type="file"] {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 14px;
            margin-bottom: 12px;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus, select:focus {
            border-color: #ff4b2b;
        }
        select option {
            background: #1e1b4b;
            color: #fff;
        }
        .btn {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: #ffffff;
            border: none;
            padding: 12px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
            transition: transform 0.1s;
        }
        .btn:active {
            transform: scale(0.98);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        #result {
            margin-top: 15px;
            font-size: 14px;
            word-break: break-all;
            text-align: center;
        }
        .loader {
            border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid #ff4b2b;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .cricket-profile {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
            text-align: left;
        }
        .cricket-profile h4 {
            margin: 0 0 5px 0;
            color: #ff4b2b;
        }
        .cricket-profile p {
            margin: 0 0 10px 0;
            font-size: 12px;
            opacity: 0.8;
        }
        .video-item {
            font-size: 12px;
            background: rgba(0,0,0,0.2);
            padding: 6px 10px;
            border-radius: 6px;
            margin-top: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .video-item a {
            color: #00a8ff;
            text-decoration: none;
            font-weight: bold;
        }
        .video-item a:hover {
            text-decoration: underline;
        }
        .banner-ad {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            min-height: 50px;
            overflow: hidden;
            border-radius: 8px;
        }
        .success-box {
            background: rgba(0,255,0,0.1);
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
            border: 1px solid rgba(0,255,0,0.2);
        }
        .error-box {
            background: rgba(255,0,0,0.1);
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
            border: 1px solid rgba(255,0,0,0.2);
            color: #e84118;
        }
        .download-btn {
            background: #00a8ff;
            color: white;
            padding: 8px 15px;
            text-decoration: none;
            border-radius: 6px;
            display: inline-block;
            font-weight: bold;
            font-size: 13px;
            margin-top: 5px;
        }
        .download-btn:hover {
            background: #0097e6;
        }
        .subscribe-box {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
            margin-top: 12px;
            font-size: 13px;
        }
        .subscribe-box a {
            color: #ff4b2b;
            text-decoration: none;
            font-weight: bold;
        }
        .subscribe-box a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Badass Tools Hub ⚡</h2>
        <div class="subtitle">Ultimate Media Downloader & Cricket Vault</div>

        <div class="banner-ad">
            <script type="text/javascript">
                atOptions = {
                    'key' : '03b4a64917d99a52eb71ea7bea6414d6',
                    'format' : 'iframe',
                    'height' : 50,
                    'width' : 320,
                    'params' : {}
                };
            </script>
            <script type="text/javascript" src="//www.highperformanceformat.com/03b4a64917d99a52eb71ea7bea6414d6/invoke.js"></script>
        </div>

        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="switchTab('downloader')">Downloader</div>
            <div class="nav-tab" onclick="switchTab('cricket')">Cricket Vault</div>
            <div class="nav-tab" onclick="switchTab('upload')">Upload Video</div>
        </div>

        <!-- Tab 1: Downloader -->
        <div id="downloader-tab" class="tab-content active">
            <div class="card">
                <input type="text" id="videoUrl" placeholder="Paste video link here (YouTube, Facebook, etc.)...">
                <select id="qualitySelect">
                    <option value="best">🎬 Best Quality (Video)</option>
                    <option value="480">📱 480p (Medium)</option>
                    <option value="720">💻 720p (HD)</option>
                    <option value="1080">🖥️ 1080p (Full HD)</option>
                    <option value="audio">🎵 Audio Only (MP3/M4A)</option>
                </select>
                <button class="btn" id="downloadBtn" onclick="processDownload()">Download Now 🚀</button>
                <div id="result"></div>
            </div>
        </div>

        <!-- Tab 2: Cricket Vault Profiles -->
        <div id="cricket-tab" class="tab-content">
            <div class="card" style="max-height: 350px; overflow-y: auto;">
                <h3 style="margin-top:0; font-size:16px; color:#ff4b2b;">🏏 Cricketers Profiles</h3>
                {% for key, profile in cricketers.items() %}
                <div class="cricket-profile">
                    <h4>{{ profile.name }}</h4>
                    <p>{{ profile.bio }}</p>
                    <div style="font-size:11px; font-weight:bold; opacity:0.7;">Featured Videos:</div>
                    {% for vid in profile.videos %}
                    <div class="video-item">
                        <span>{{ vid.title }}</span>
                        <a href="{{ vid.url }}" target="_blank">Watch 🎬</a>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Tab 3: Admin Upload Panel -->
        <div id="upload-tab" class="tab-content">
            <div class="card">
                <h3 style="margin-top:0; font-size:16px; color:#ff4b2b;">📤 Upload Cricket Video</h3>
                <form action="/upload-video" method="POST" enctype="multipart/form-data">
                    <select name="cricketer_key" required>
                        <option value="">Select Cricketer Profile</option>
                        {% for key, profile in cricketers.items() %}
                        <option value="{{ key }}">{{ profile.name }}</option>
                        {% endfor %}
                    </select>
                    <input type="text" name="video_title" placeholder="Enter Video Title..." required>
                    <input type="file" name="video_file" accept="video/*" required>
                    <button type="submit" class="btn">Upload to Vault 🚀</button>
                </form>
            </div>
        </div>

        <div class="subscribe-box">
            🎬 Subscribe Our Channel: <br>
            <a href="https://www.youtube.com/@BadassToonsOfficial" target="_blank">Badass Toons Official ❤️</a>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        function switchTab(tabName) {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            if(tabName === 'downloader') {
                document.querySelectorAll('.nav-tab')[0].classList.add('active');
                document.getElementById('downloader-tab').classList.add('active');
            } else if(tabName === 'cricket') {
                document.querySelectorAll('.nav-tab')[1].classList.add('active');
                document.getElementById('cricket-tab').classList.add('active');
            } else if(tabName === 'upload') {
                document.querySelectorAll('.nav-tab')[2].classList.add('active');
                document.getElementById('upload-tab').classList.add('active');
            }
        }

        function processDownload() {
            let url = document.getElementById('videoUrl').value.trim();
            let quality = document.getElementById('qualitySelect').value;
            let resultDiv = document.getElementById('result');
            let downloadBtn = document.getElementById('downloadBtn');

            if (!url) {
                tg.showAlert("Please paste a valid video link!");
                resultDiv.innerHTML = '<div class="error-box">⚠️ Please paste a valid video link!</div>';
                return;
            }

            // Validate URL
            try {
                new URL(url);
            } catch (e) {
                tg.showAlert("Invalid URL format!");
                resultDiv.innerHTML = '<div class="error-box">⚠️ Invalid URL format! Please check the link.</div>';
                return;
            }

            // Disable button and show loading
            downloadBtn.disabled = true;
            downloadBtn.textContent = 'Processing...';
            resultDiv.innerHTML = '<div class="loader"></div><span style="font-size:12px; opacity:0.8;">Fetching media stream...</span>';

            fetch('/process-media', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, quality: quality })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    let safeTitle = encodeURIComponent(data.title.replace(/[^a-zA-Z0-9]/g, '_'));
                    let proxyLink = `/proxy-download?url=${encodeURIComponent(data.download_link)}&title=${safeTitle}&type=${data.type || 'video'}`;
                    
                    resultDiv.innerHTML = `
                        <div class="success-box">
                            <b style="color: #4cd137; font-size: 13px; display:block; margin-bottom:5px;">✅ ${data.title}</b>
                            <div style="font-size: 11px; color: #aaa; margin-bottom: 8px;">Quality: ${data.resolution || 'Best'} | Size: ${data.size || 'Unknown'}</div>
                            <a href="${proxyLink}" class="download-btn" onclick="this.textContent='Downloading...'">Click to Save File 🚀</a>
                        </div>`;
                } else {
                    resultDiv.innerHTML = `<div class="error-box">❌ Error: ${data.message}</div>`;
                    tg.showAlert("Download failed: " + data.message);
                }
            })
            .catch(err => {
                resultDiv.innerHTML = `<div class="error-box">❌ Network connection error! Please try again.</div>`;
                tg.showAlert("Network error! Please check your connection.");
            })
            .finally(() => {
                // Re-enable button
                downloadBtn.disabled = false;
                downloadBtn.textContent = 'Download Now 🚀';
            });
        }

        // Auto-detect URLs from clipboard
        document.getElementById('videoUrl').addEventListener('paste', function(e) {
            setTimeout(() => {
                let url = this.value.trim();
                if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
                    // Optional: Auto-process
                }
            }, 100);
        });
    </script>
</body>
</html>
"""

# --- HELPER FUNCTIONS ---
def is_valid_url(url):
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sanitize_filename(filename):
    """Sanitize filename for safe download"""
    # Remove invalid characters
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.strip()

# --- WEB APP ROUTES ---
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, cricketers=CRICKET_DATABASE)

@app.route('/upload-video', methods=['POST'])
def upload_video():
    try:
        cricketer_key = request.form.get('cricketer_key')
        video_title = request.form.get('video_title')
        video_file = request.files.get('video_file')

        if not cricketer_key or not video_file or cricketer_key not in CRICKET_DATABASE:
            return redirect(url_for('home'))

        # Generate unique filename
        filename = f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(file_path)
        
        # Add file link into database category
        file_url = f"/static/uploads/{filename}"
        CRICKET_DATABASE[cricketer_key]["videos"].append({
            "title": video_title,
            "url": file_url
        })

        return redirect(url_for('home'))
    except Exception as e:
        print(f"Upload error: {e}")
        return redirect(url_for('home'))

@app.route('/proxy-download')
def proxy_download():
    try:
        video_url = request.args.get('url')
        filename = request.args.get('title', 'video')
        media_type = request.args.get('type', 'video')
        
        if not video_url:
            return "URL is required", 400
        
        # Decode URL if needed
        if '%' in video_url:
            video_url = requests.utils.unquote(video_url)
        
        # Check if URL is valid
        if not is_valid_url(video_url):
            return "Invalid URL", 400
        
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        extension = '.mp4' if media_type == 'video' else '.mp3'
        full_filename = f"{safe_filename}{extension}"
        
        # Stream download with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Handle redirects
        session = requests.Session()
        session.max_redirects = 5
        
        response = session.get(video_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Determine content type
        content_type = response.headers.get('content-type', '')
        if 'audio' in content_type:
            full_filename = f"{safe_filename}.mp3"
        elif 'video' in content_type:
            full_filename = f"{safe_filename}.mp4"
        
        # Stream the file
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        return app.response_class(
            generate(),
            headers={
                'Content-Disposition': f'attachment; filename="{full_filename}"',
                'Content-Type': content_type or 'application/octet-stream',
                'Content-Length': response.headers.get('content-length'),
                'Cache-Control': 'no-cache'
            }
        )
    except requests.exceptions.Timeout:
        return "Download timeout. Please try again.", 408
    except requests.exceptions.RequestException as e:
        return f"Download failed: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/process-media', methods=['POST'])
def process_media():
    try:
        data = request.json
        video_url = data.get('url', '').strip()
        quality = data.get('quality', 'best')

        if not video_url:
            return jsonify({'success': False, 'message': 'URL is required'})
        
        if not is_valid_url(video_url):
            return jsonify({'success': False, 'message': 'Invalid URL format'})

        # Common headers for yt-dlp
        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }

        # Configure yt-dlp options based on quality
        if quality == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'geo_bypass': True,
                'http_headers': common_headers,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'ios'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
        elif quality == 'best':
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'geo_bypass': True,
                'http_headers': common_headers,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'ios'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
        else:
            # For specific quality (480, 720, 1080)
            quality_value = quality.replace('p', '')
            if quality_value.isdigit():
                height = int(quality_value)
                ydl_opts = {
                    'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                    'geo_bypass': True,
                    'http_headers': common_headers,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'ios'],
                            'skip': ['hls', 'dash']
                        }
                    }
                }
            else:
                # Fallback to best
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                    'geo_bypass': True,
                    'http_headers': common_headers
                }

        # Extract video info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
                if not info:
                    return jsonify({'success': False, 'message': 'Could not extract video information'})
                
                # Get the best available URL
                download_url = info.get('url')
                if not download_url:
                    # Try to get from formats
                    formats = info.get('formats', [])
                    if formats:
                        # Get the format with highest quality
                        best_format = max(formats, key=lambda f: f.get('height', 0) if f.get('height') else 0)
                        download_url = best_format.get('url')
                
                if not download_url:
                    return jsonify({'success': False, 'message': 'No downloadable URL found'})
                
                # Get title and metadata
                title = info.get('title', 'Media File')
                resolution = "Best"
                if quality != 'best' and quality != 'audio':
                    resolution = f"{quality}p"
                elif quality == 'audio':
                    resolution = "Audio Only"
                
                # Get file size if available
                file_size = info.get('filesize')
                if not file_size and formats:
                    for fmt in formats:
                        if fmt.get('url') == download_url and fmt.get('filesize'):
                            file_size = fmt.get('filesize')
                            break
                
                size_str = "Unknown"
                if file_size:
                    if file_size > 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024*1024*1024):.2f} GB"
                    elif file_size > 1024 * 1024:
                        size_str = f"{file_size / (1024*1024):.2f} MB"
                    else:
                        size_str = f"{file_size / 1024:.2f} KB"
                
                return jsonify({
                    'success': True,
                    'title': title,
                    'download_link': download_url,
                    'resolution': resolution,
                    'size': size_str,
                    'type': 'audio' if quality == 'audio' else 'video'
                })
                
            except yt_dlp.utils.DownloadError as e:
                return jsonify({'success': False, 'message': f'Download error: {str(e)[:100]}'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Extraction error: {str(e)[:100]}'})
                
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)[:100]}'})

# --- TELEGRAM WEBHOOK ENDPOINT ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            if update:
                bot.process_new_updates([update])
            return "OK", 200
        else:
            return "Forbidden", 403
    except Exception as e:
        print(f"Webhook error: {e}")
        return "Error", 500

# --- TELEGRAM BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        web_app_url = "https://web-production-6836d.up.railway.app/"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "⚡ Open Badass Tools Hub", 
            web_app=telebot.types.WebAppInfo(url=web_app_url)
        ))
        bot.reply_to(
            message, 
            "Assalamu Alaikum! 🎯\n\nClick the button below to open Badass Tools Hub & Cricket Vault:", 
            reply_markup=markup
        )
    except Exception as e:
        print(f"Bot error: {e}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        # Simple reply for any other messages
        bot.reply_to(message, "Use the button above to open the Badass Tools Hub! 🚀")
    except Exception as e:
        print(f"Bot error: {e}")

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get("PORT", 5000))
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        print(f"🚀 Server starting on port {port}")
        print(f"📁 Upload directory: {UPLOAD_FOLDER}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Failed to start server: {e}")
        
