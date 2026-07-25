import os
import requests
import telebot
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import yt_dlp

# --- CONFIGURATION ---
TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# Directory for storing uploaded cricket videos locally or managing categories
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
        .banner-ad {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            min-height: 50px;
            overflow: hidden;
            border-radius: 8px;
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
                <input type="text" id="videoUrl" placeholder="Paste video link here...">
                <select id="qualitySelect">
                    <option value="best">🎬 Best Quality (Video)</option>
                    <option value="480">📱 480p (Medium)</option>
                    <option value="720">💻 720p (HD)</option>
                    <option value="1080">🖥️ 1080p (Full HD)</option>
                    <option value="audio">🎵 Audio Only (MP3/M4A)</option>
                </select>
                <button class="btn" onclick="processDownload()">Download Now 🚀</button>
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

        <div class="subscribe-box" style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); padding: 10px; border-radius: 10px; margin-top: 12px; font-size: 13px;">
            🎬 Subscribe Our Channel: <br>
            <a href="https://www.youtube.com/@BadassToonsOfficial" target="_blank" style="color: #ff4b2b; text-decoration: none; font-weight: bold;">Badass Toons Official ❤️</a>
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

            if (!url) {
                tg.showAlert("Pehle koi valid link paste karein!");
                return;
            }

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
                    let proxyLink = `/proxy-download?url=${encodeURIComponent(data.download_link)}&title=${safeTitle}`;
                    
                    resultDiv.innerHTML = `
                        <div style="background: rgba(0,255,0,0.1); padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid rgba(0,255,0,0.2);">
                            <b style="color: #4cd137; font-size: 13px; display:block; margin-bottom:5px;">${data.title}</b>
                            <a href="${proxyLink}" style="background: #00a8ff; color: white; padding: 8px 15px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 13px;">Click to Save File 🚀</a>
                        </div>`;
                } else {
                    resultDiv.innerHTML = `<span style="color: #e84118; font-size: 13px;">Error: ${data.message}</span>`;
                }
            })
            .catch(err => {
                resultDiv.innerHTML = `<span style="color: #e84118; font-size: 13px;">Network connection error!</span>`;
            });
        }
    </script>
</body>
</html>
"""

# --- WEB APP ROUTES ---
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, cricketers=CRICKET_DATABASE)

@app.route('/upload-video', methods=['POST'])
def upload_video():
    cricketer_key = request.form.get('cricketer_key')
    video_title = request.form.get('video_title')
    video_file = request.files.get('video_file')

    if cricketer_key and video_file and cricketer_key in CRICKET_DATABASE:
        filename = video_file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(file_path)
        
        # Add file link into database category
        file_url = f"/{file_path}"
        CRICKET_DATABASE[cricketer_key]["videos"].append({
            "title": video_title,
            "url": file_url
        })

    return redirect(url_for('home'))

@app.route('/proxy-download')
def proxy_download():
    video_url = request.args.get('url')
    filename = request.args.get('title', 'video') + '.mp4'
    if not video_url:
        return "URL is required", 400
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(video_url, headers=headers, stream=True)
        
        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk
                
        return app.response_class(generate(), headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': r.headers.get('content-type', 'video/mp4')
        })
    except Exception as e:
        return str(e), 500

@app.route('/process-media', methods=['POST'])
def process_media():
    data = request.json
    video_url = data.get('url', '')
    quality = data.get('quality', 'best')

    if not video_url:
        return jsonify({'success': False, 'message': 'URL is required'})

    try:
        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        ext_args = {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        }

        if quality == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'http_headers': common_headers,
                'extractor_args': ext_args,
            }
        elif quality == 'best':
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'http_headers': common_headers,
                'extractor_args': ext_args,
            }
        else:
            ydl_opts = {
                'format': f'best[height<={quality}]/best' if quality.isdigit() else f'best[height<={quality.replace("p","")}]/best',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'http_headers': common_headers,
                'extractor_args': ext_args,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            title = info.get('title', 'Media File')

        if not download_url:
            return jsonify({'success': False, 'message': 'Could not extract direct link for this quality.'})

        return jsonify({
            'success': True,
            'title': title,
            'download_link': download_url
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)[:120]})
        
# --- TELEGRAM WEBHOOK ENDPOINT ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

# --- TELEGRAM BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    web_app_url = "https://web-production-6836d.up.railway.app/"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⚡ Open Badass Tools Hub", web_app=telebot.types.WebAppInfo(url=web_app_url)))
    bot.reply_to(message, "Salam! Niche diye gaye button par click karke Badass Tools Hub & Cricket Vault open karein:", reply_markup=markup)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
