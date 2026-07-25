import os
import re
import requests
import telebot
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

# --- ISOLATED AD DOCUMENT ROUTE ---
AD_FRAME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            width: 320px;
            height: 50px;
        }
    </style>
</head>
<body>
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
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexGen Video Downloader & Cricket Videos</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: var(--tg-theme-bg-color, #121418);
            --text-color: var(--tg-theme-text-color, #ffffff);
            --card-bg: rgba(255, 255, 255, 0.04);
            --btn-color: var(--tg-theme-button-color, #00d2ff);
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
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
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
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
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
            position: relative;
            z-index: 2;
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
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            color: #ffffff;
            border: none;
            padding: 12px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
            position: relative;
            z-index: 3;
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
            border-top: 3px solid #00d2ff;
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
            color: #00d2ff;
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
            background: rgba(0,0,0,0.2);
        }
        .banner-ad iframe {
            width: 320px;
            height: 50px;
            border: none;
            overflow: hidden;
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
            font-size: 12px;
        }
        .download-btn {
            background: #00d2ff;
            color: #000;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 8px;
            display: block;
            font-weight: bold;
            font-size: 14px;
            margin-top: 8px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 210, 255, 0.3);
            position: relative;
            z-index: 3;
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
            color: #00d2ff;
            text-decoration: none;
            font-weight: bold;
        }
        .social-icons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 12px;
            font-size: 20px;
        }
        .social-icons a {
            color: #fff;
            opacity: 0.8;
            transition: 0.2s;
        }
        .social-icons a:hover {
            opacity: 1;
            color: #00d2ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>NexGen Downloader ⚡</h2>
        <div class="subtitle">Ultimate Media Stream Grabber</div>

        <div class="banner-ad">
            <!-- Strictly Sandboxed Isolated Frame loading separate safe route -->
            <iframe src="/banner-ad" sandbox="allow-scripts allow-same-origin allow-popups"></iframe>
        </div>

        <div class="nav-tabs">
            <div class="nav-tab active" onclick="switchTab('downloader')">Downloader</div>
            <div class="nav-tab" onclick="switchTab('cricket')">📁 Cricket Videos</div>
        </div>

        <div id="downloader-tab" class="tab-content active">
            <div class="card">
                <input type="text" id="videoUrl" placeholder="Paste YouTube link here...">
                <select id="qualitySelect">
                    <option value="best" selected>🎬 Best Quality (Video)</option>
                    <option value="480">📱 480p (Medium)</option>
                    <option value="720">💻 720p (HD)</option>
                    <option value="1080">🖥️ 1080p (Full HD)</option>
                    <option value="audio">🎵 Audio Only (MP3)</option>
                </select>
                <button class="btn" id="downloadBtn" onclick="processDownload()">Download Now 🚀</button>
                <div id="result"></div>
            </div>
        </div>

        <div id="cricket-tab" class="tab-content">
            <div class="card" style="max-height: 400px; overflow-y: auto;">
                <h3 style="margin-top:0; font-size:15px; color:#00d2ff;">📂 Cricket Video Folders</h3>
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
            <div class="social-icons">
                <a href="https://youtube.com/@BadassToonsOfficial" target="_blank"><i class="fab fa-youtube"></i></a>
                <a href="#" target="_blank"><i class="fab fa-instagram"></i></a>
                <a href="#" target="_blank"><i class="fab fa-facebook"></i></a>
                <a href="#" target="_blank"><i class="fab fa-tiktok"></i></a>
            </div>
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

        async function processDownload() {
            let url = document.getElementById('videoUrl').value.trim();
            let quality = document.getElementById('qualitySelect').value;
            let resultDiv = document.getElementById('result');
            let downloadBtn = document.getElementById('downloadBtn');

            if (!url) {
                resultDiv.innerHTML = '<div class="error-box">⚠️ Please paste a valid YouTube link!</div>';
                return;
            }

            downloadBtn.disabled = true;
            downloadBtn.textContent = 'Processing...';
            resultDiv.innerHTML = '<div class="loader"></div><div style="font-size:12px; opacity:0.8; margin-top:5px; color:#fff;">Connecting via client IP...</div>';

            try {
                let payload = {
                    url: url,
                    vQuality: quality === 'best' ? 'max' : quality,
                    isAudioOnly: quality === 'audio',
                    dubLang: false
                };

                let apis = [
                    "https://api.cobalt.tools/api/json",
                    "https://co.wuk.sh/api/json"
                ];

                let downloadUrl = null;

                for (let api of apis) {
                    try {
                        let response = await fetch(api, {
                            method: "POST",
                            headers: {
                                "Accept": "application/json",
                                "Content-Type": "application/json",
                                "User-Agent": navigator.userAgent
                            },
                            body: JSON.stringify(payload)
                        });

                        let data = await response.json();
                        if (data) {
                            if (data.url) {
                                downloadUrl = data.url;
                                break;
                            } else if (data.picker && data.picker.length > 0) {
                                downloadUrl = data.picker[0].url;
                                break;
                            } else if (data.status === "redirect" && data.url) {
                                downloadUrl = data.url;
                                break;
                            }
                        }
                    } catch (e) {
                        continue;
                    }
                }

                if (downloadUrl) {
                    resultDiv.innerHTML = `
                        <div class="success-box">
                            <b style="color: #4cd137; font-size: 13px; display:block; margin-bottom:5px;">✅ Link Extracted Successfully!</b>
                            <a href="${downloadUrl}" class="download-btn" target="_blank">⬇️ Download File Now</a>
                        </div>`;
                } else {
                    resultDiv.innerHTML = `<div class="error-box">❌ Unable to fetch stream. Please ensure the YouTube link is public and correct.</div>`;
                }

            } catch (err) {
                resultDiv.innerHTML = `<div class="error-box">❌ Network error occurred. Please check your connection.</div>`;
            } finally {
                downloadBtn.disabled = false;
                downloadBtn.textContent = 'Download Now 🚀';
            }
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
    <title>Admin Panel - NexGen Downloader</title>
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
        h2 { color: #00d2ff; text-align: center; margin-top: 0; }
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
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
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

def sanitize_filename(filename):
    filename = re.sub(r'[^\w\s-]', '', filename)
    return re.sub(r'[-\s]+', '_', filename).strip()[:100]

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, cricketers=CRICKET_DATABASE)

@app.route('/banner-ad')
def banner_ad():
    return render_template_string(AD_FRAME_TEMPLATE)

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

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@bot.message_handler(commands=['start'])
def send_welcome(message):
    host_url = "https://web-production-6836d.up.railway.app/"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⚡ Open NexGen Downloader", web_app=telebot.types.WebAppInfo(url=host_url)))
    bot.reply_to(message, "Assalamu Alaikum! 🎯 Click below to open app:", reply_markup=markup)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
