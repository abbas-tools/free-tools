import telebot
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

TOKEN = "7831761974:AAHMaAAbtdk5v78vIkbxJmrStBzr1-1T1Uw"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# --- CONFIGURATION ---
TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# --- MAIN WEB APP HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Badass Tools Hub</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <!-- FontAwesome for Real Brand Icons -->
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
            justify-content: center;
        }
        .container {
            max-width: 400px;
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
        .card {
            background-color: var(--card-bg);
            padding: 18px;
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 15px;
        }
        input[type="text"], select {
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
        .banner-ad {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            min-height: 50px;
            overflow: hidden;
            border-radius: 8px;
        }
        .platforms {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            font-size: 26px;
        }
        .platforms i {
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4));
            transition: transform 0.2s;
        }
        .platforms i:hover {
            transform: scale(1.15);
        }
        .fa-youtube { color: #ff0000; }
        .fa-instagram { color: #e1306c; }
        .fa-facebook { color: #1877f2; }
        .fa-tiktok { color: #ffffff; }
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
        <div class="subtitle">Ultimate Media Downloader</div>

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

        <div class="card">
            <input type="text" id="videoUrl" placeholder="Paste video link here...">

            <select id="qualitySelect">
                <option value="best">🎬 Best Quality (Video)</option>
                <option value="135">📱 480p (Medium)</option>
                <option value="22">💻 720p (HD)</option>
                <option value="137">🖥️ 1080p (Full HD)</option>
                <option value="audio">🎵 Audio Only (MP3/M4A)</option>
            </select>

            <button class="btn" onclick="processDownload()">Download Now 🚀</button>

            <div id="result"></div>
        </div>

        <div class="subscribe-box">
            🎬 Subscribe Our Channel: <br>
            <a href="https://www.youtube.com/@BadassToonsOfficial" target="_blank">Badass Toons Official ❤️</a>
        </div>

        <div class="platforms">
            <i class="fa-brands fa-youtube"></i>
            <i class="fa-brands fa-instagram"></i>
            <i class="fa-brands fa-facebook"></i>
            <i class="fa-brands fa-tiktok"></i>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

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
                    resultDiv.innerHTML = `
                        <div style="background: rgba(0,255,0,0.1); padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid rgba(0,255,0,0.2);">
                            <b style="color: #4cd137; font-size: 13px; display:block; margin-bottom:5px;">${data.title}</b>
                            <a href="${data.download_link}" target="_blank" style="background: #00a8ff; color: white; padding: 8px 15px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 13px;">Click to Save File 🚀</a>
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
                'player_client': ['android']
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
        
# --- TELEGRAM WEBHOOK ENDPOINT (24/7 Background Handler) ---
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

    bot.reply_to(message, "Salam! Niche diye gaye button par click karke Badass Tools Hub open karein:", reply_markup=markup)
    


import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
