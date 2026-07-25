import os
import re
import requests
import telebot
import yt_dlp
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, Response
import uuid
from urllib.parse import urlparse

# --- CONFIGURATION ---
TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Dictionary to hold players and their folders
CRICKET_DATABASE = {
    "babar-azam": {
        "name": "Babar Azam 👑",
        "bio": "Master class cover drives and match-winning knocks.",
        "videos": []
    },
    "virat-kohli": {
        "name": "Virat Kohli 🔥",
        "bio": "The Run Machine and chase master highlights.",
        "videos": []
    },
    "shaheen-afridi": {
        "name": "Shaheen Afridi ⚡",
        "bio": "First-over lethal swinging yorkers.",
        "videos": []
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Badass Tools Hub & Cricket Gallery</title>
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
            justify-content: center;
            gap: 10px;
            background: rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 6px;
            margin-bottom: 15px;
        }
        .nav-tab {
            flex: 1;
            padding: 10px;
            font-size: 13px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
            border-radius: 8px;
            transition: 0.2s;
            text-align: center;
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
            padding: 14px;
            margin-bottom: 12px;
            text-align: left;
        }
        .cricket-profile h4 {
            margin: 0 0 4px 0;
            color: #ff4b2b;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .cricket-profile p {
            margin: 0 0 10px 0;
            font-size: 11px;
            opacity: 0.8;
        }
        .video-item {
            font-size: 12px;
            background: rgba(0,0,0,0.3);
            padding: 8px 10px;
            border-radius: 8px;
            margin-top: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .video-item a {
            background: #00a8ff;
            color: white;
            padding: 5px 12px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
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
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 6px;
            display: inline-block;
            font-weight: bold;
            font-size: 14px;
            margin-top: 8px;
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
    </style>
</head>
<body>
    <div class="container">
        <h2>Badass Tools Hub ⚡</h2>
        <div class="subtitle">Ultimate Media Downloader & Cricket Gallery</div>

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

        <div class="nav-tabs">
            <div class="nav-tab active" onclick="switchTab('downloader')">Downloader</div>
            <div class="nav-tab" onclick="switchTab('cricket')">📁 Cricket Folders</div>
        </div>

        <div id="downloader-tab" class="tab-content active">
            <div class="card">
                <input type="text" id="videoUrl" placeholder="Paste video link here...">
                <select id="qualitySelect">
                    <option value="best">🎬 Best Quality (Video)</option>
                    <option value="480" selected>📱 480p (Medium)</option>
                    <option value="720">💻 720p (HD)</option>
                    <option value="1080">🖥️ 1080p (Full HD)</option>
                    <option value="audio">🎵 Audio Only (MP3/M4A)</option>
                </select>
                <button class="btn" id="downloadBtn" onclick="processDownload()">Download Now 🚀</button>
                <div id="result"></div>
            </div>
        </div>

        <div id="cricket-tab" class="tab-content">
            <div class="card" style="max-height: 400px; overflow-y: auto;">
                <h3 style="margin-top:0; font-size:15px; color:#ff4b2b;">📂 Players Gallery Folders</h3>
                {% for key, profile in cricketers.items() %}
                <div class="cricket-profile">
                    <h4><i class="fa-solid fa-folder-open" style="color:#f1c40f;"></i> {{ profile.name }}</h4>
                    <p>{{ profile.bio }}</p>
                    <div style="font-size:11px; font-weight:bold; opacity:0.7; margin-bottom:4px;">Videos Available:</div>
                    {% if profile.videos %}
                        {% for vid in profile.videos %}
                        <div class="video-item">
                            <span style="max-width: 65%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">🎬 {{ vid.title }}</span>
                            <a href="{{ vid.url }}" download>⬇️ Download</a>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div style="font-size: 11px; opacity: 0.5; font-style: italic;">No videos in this folder yet.</div>
                    {% endif %}
                </div>
                {% endfor %}
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
            }
        }

        function processDownload() {
            let url = document.getElementById('videoUrl').value.trim();
            let quality = document.getElementById('qualitySelect').value;
            let resultDiv = document.getElementById('result');
            let downloadBtn = document.getElementById('downloadBtn');

            if (!url) {
                resultDiv.innerHTML = '<div class="error-box">⚠️ Please paste a valid video link!</div>';
                return;
            }

            downloadBtn.disabled = true;
            downloadBtn.textContent = 'Processing...';
            resultDiv.innerHTML = '<div class="loader"></div><div style="font-size:12px; opacity:0.8; margin-top:5px;">Fetching media stream...</div>';

            fetch('/process-media', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, quality: quality })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    let proxyLink = `/proxy-download?url=${encodeURIComponent(data.download_link)}&title=${encodeURIComponent(data.title)}&type=${data.type || 'video'}`;
                    resultDiv.innerHTML = `
                        <div class="success-box">
                            <b style="color: #4cd137; font-size: 14px; display:block; margin-bottom:5px;">✅ ${data.title}</b>
                            <div style="font-size: 12px; color: #aaa; margin: 5px 0;">📊 Quality: ${data.resolution} | 💾 Size: ${data.size}</div>
                            <a href="${proxyLink}" class="download-btn">⬇️ Click to Save File</a>
                        </div>`;
                } else {
                    resultDiv.innerHTML = `<div class="error-box">❌ ${data.message}</div>`;
                }
            })
            .catch(err => {
                resultDiv.innerHTML = `<div class="error-box">❌ Network connection error!</div>`;
            })
            .finally(() => {
                downloadBtn.disabled = false;
                downloadBtn.textContent = 'Download Now 🚀';
            });
        }
    </script>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Badass Tools Hub</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #fff;
            text-align: center;
            padding: 20px;
            margin: 0;
            min-height: 100vh;
        }
        .container {
            max-width: 450px;
            margin: auto;
            background: rgba(255, 255, 255, 0.04);
            padding: 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            text-align: left;
        }
        h2 { color: #ff4b2b; text-align: center; margin-top: 0; }
        h3 { color: #f1c40f; font-size: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; }
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
            margin-bottom: 15px;
        }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 15px;
            color: #00a8ff;
            text-decoration: none;
            font-weight: bold;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🛠️ Admin Panel</h2>

        <h3>➕ Create New Player Folder</h3>
        <form action="/admin/add-folder" method="POST">
            <input type="text" name="player_name" placeholder="Player Name (e.g. MS Dhoni 🇮🇳)" required>
            <input type="text" name="player_bio" placeholder="Short Bio / Description" required>
            <button type="submit" class="btn" style="background: linear-gradient(135deg, #00b09b, #96c93d);">Create Folder 📂</button>
        </form>

        <h3>📤 Upload Video to Folder</h3>
        <form action="/admin/upload-video" method="POST" enctype="multipart/form-data">
            <select name="cricketer_key" required>
                <option value="">Select Player Folder</option>
                {% for key, profile in cricketers.items() %}
                <option value="{{ key }}">📁 {{ profile.name }}</option>
                {% endfor %}
            </select>
            <input type="text" name="video_title" placeholder="Enter Video Title..." required>
            <input type="file" name="video_file" accept="video/*" required>
            <button type="submit" class="btn">Upload Video 🚀</button>
        </form>

        <a href="/" class="back-link">⬅️ Back to Public Website</a>
    </div>
</body>
</html>
"""

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sanitize_filename(filename):
    filename = re.sub(r'[^\w\s-]', '', filename)
    return re.sub(r'[-\s]+', '_', filename).strip()[:100]

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, cricketers=CRICKET_DATABASE)

@app.route('/admin-panel')
def admin_panel():
    return render_template_string(ADMIN_TEMPLATE, cricketers=CRICKET_DATABASE)

@app.route('/admin/add-folder', methods=['POST'])
def add_folder():
    try:
        name = request.form.get('player_name', '').strip()
        bio = request.form.get('player_bio', '').strip()
        if name:
            key = sanitize_filename(name).lower()
            if key not in CRICKET_DATABASE:
                CRICKET_DATABASE[key] = {
                    "name": name,
                    "bio": bio,
                    "videos": []
                }
        return redirect(url_for('admin_panel'))
    except:
        return redirect(url_for('admin_panel'))

@app.route('/admin/upload-video', methods=['POST'])
def admin_upload_video():
    try:
        cricketer_key = request.form.get('cricketer_key')
        video_title = request.form.get('video_title')
        video_file = request.files.get('video_file')

        if not cricketer_key or not video_file or cricketer_key not in CRICKET_DATABASE:
            return redirect(url_for('admin_panel'))

        filename = f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(file_path)
        
        CRICKET_DATABASE[cricketer_key]["videos"].append({
            "title": video_title,
            "url": f"/static/uploads/{filename}"
        })
        return redirect(url_for('admin_panel'))
    except:
        return redirect(url_for('admin_panel'))

@app.route('/proxy-download')
def proxy_download():
    try:
        video_url = request.args.get('url')
        filename = request.args.get('title', 'video')
        media_type = request.args.get('type', 'video')
        
        if not video_url:
            return "URL is required", 400
        
        if '%' in video_url:
            video_url = requests.utils.unquote(video_url)
            
        safe_filename = sanitize_filename(filename)
        extension = '.mp4' if media_type == 'video' else '.mp3'
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'}
        response = requests.get(video_url, headers=headers, stream=True, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
                    
        return Response(generate(), headers={
            'Content-Disposition': f'attachment; filename="{safe_filename}{extension}"',
            'Content-Type': response.headers.get('content-type', 'application/octet-stream')
        })
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/process-media', methods=['POST'])
def process_media():
    try:
        data = request.json
        video_url = data.get('url', '').strip()
        quality = data.get('quality', 'best')

        if not video_url or not is_valid_url(video_url):
            return jsonify({'success': False, 'message': 'Invalid URL format'})

        if quality == 'audio':
            format_spec = 'bestaudio/best'
        elif quality == 'best':
            format_spec = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            height = quality.replace('p', '')
            format_spec = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]/best'
        
        ydl_opts = {
            'format': format_spec,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'source_address': '0.0.0.0',
            'socket_timeout': 30,
            'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if not info:
                return jsonify({'success': False, 'message': 'Could not extract video info'})
            
            download_url = info.get('url')
            if not download_url and info.get('formats'):
                for f in info.get('formats', []):
                    if f.get('ext') in ['mp4', 'm4a'] and f.get('url'):
                        download_url = f.get('url')
                        break
            
            if not download_url:
                return jsonify({'success': False, 'message': 'No downloadable URL found'})
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Media File'),
                'download_link': download_url,
                'resolution': f"{quality}p" if quality not in ['best', 'audio'] else 'Best',
                'size': 'Unknown',
                'type': 'audio' if quality == 'audio' else 'video'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)[:100]}'})

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@bot.message_handler(commands=['start'])
def send_welcome(message):
    web_app_url = "https://web-production-6836d.up.railway.app/"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⚡ Open Badass Tools Hub", web_app=telebot.types.WebAppInfo(url=web_app_url)))
    bot.reply_to(message, "Assalamu Alaikum! 🎯 Click below to open app:", reply_markup=markup)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
