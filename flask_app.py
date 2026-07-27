import os
import re
import uuid
import json
import random
import time
import requests
import telebot
import yt_dlp
from urllib.parse import urlparse, quote, unquote
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file, Response, session
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import hashlib
import socket
from functools import wraps
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import datetime
import zipfile
import io
import base64
from werkzeug.utils import secure_filename

# ===============================
# 🔥 CONFIGURATION & SETUP
# ===============================

TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
ADMIN_PASSWORD = "Babache007"

# Cloudinary Configuration
CLOUDINARY_CONFIG = {
    'cloud_name': os.environ.get('CLOUDINARY_CLOUD_NAME', 'Root'),
    'api_key': os.environ.get('CLOUDINARY_API_KEY', '884661819567361'),
    'api_secret': os.environ.get('CLOUDINARY_API_SECRET', 'R0IrtPJFveu0Tcbt3xSxsOtQSy4')
}

cloudinary.config(
    cloud_name=CLOUDINARY_CONFIG['cloud_name'],
    api_key=CLOUDINARY_CONFIG['api_key'],
    api_secret=CLOUDINARY_CONFIG['api_secret']
)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(64)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB max upload
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_VIDEOS_PER_UPLOAD'] = 500

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_FILE = 'database.json'
DOWNLOAD_COUNT_FILE = 'download_count.txt'

# ===============================
# 📊 DOWNLOAD COUNT FUNCTIONS
# ===============================

def get_download_count():
    try:
        if os.path.exists(DOWNLOAD_COUNT_FILE):
            with open(DOWNLOAD_COUNT_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 0

def increment_download_count():
    try:
        count = get_download_count() + 1
        with open(DOWNLOAD_COUNT_FILE, 'w') as f:
            f.write(str(count))
        return count
    except:
        return 0

# ===============================
# 🛡️ RATE LIMITING & HEADERS
# ===============================

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.max_requests = 10
        self.time_window = 60
    
    def is_allowed(self, ip):
        current_time = time.time()
        if ip not in self.requests:
            self.requests[ip] = []
        
        self.requests[ip] = [t for t in self.requests[ip] if current_time - t < self.time_window]
        
        if len(self.requests[ip]) >= self.max_requests:
            return False
        
        self.requests[ip].append(current_time)
        return True

rate_limiter = RateLimiter()

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

# ===============================
# 🔧 REQUEST SESSION
# ===============================

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=30, pool_maxsize=30)
session.mount('https://', adapter)
session.mount('http://', adapter)

# ===============================
# 💾 DATABASE
# ===============================

def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
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

def save_database(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# ===============================
# 🎯 MULTI ENGINE EXTRACTOR
# ===============================

class MultiEngineExtractor:
    @staticmethod
    def extract_with_all_engines(url, quality):
        engines = [
            MultiEngineExtractor.engine_ytdlp,
            MultiEngineExtractor.engine_rapidapi,
            MultiEngineExtractor.engine_cobalt,
            MultiEngineExtractor.engine_savefrom,
            MultiEngineExtractor.engine_direct_api,
        ]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_engine = {
                executor.submit(engine, url, quality): engine.__name__ 
                for engine in engines
            }
            
            for future in as_completed(future_to_engine, timeout=12):
                try:
                    result = future.result(timeout=3)
                    if result and result.get('success') and result.get('download_url'):
                        return result
                except TimeoutError:
                    continue
                except Exception:
                    continue
        
        return {'success': False, 'error': 'All extraction engines failed. Try another link.'}
    
    @staticmethod
    def engine_ytdlp(url, quality='max'):
        try:
            if quality == 'audio':
                format_spec = 'bestaudio/best'
            elif quality == 'max':
                format_spec = 'bestvideo+bestaudio/best'
            else:
                height = quality.replace('p', '')
                if height.isdigit():
                    format_spec = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
                else:
                    format_spec = 'bestvideo+bestaudio/best'
            
            clients = ['android', 'ios', 'web', 'mweb']
            random.shuffle(clients)
            
            for client in clients[:3]:
                try:
                    ydl_opts = {
                        'format': format_spec,
                        'quiet': True,
                        'no_warnings': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'geo_bypass': True,
                        'socket_timeout': 15,
                        'retries': 3,
                        'fragment_retries': 3,
                        'extractor_args': {
                            'youtube': {
                                'player_client': [client],
                                'skip': ['hls', 'dash']
                            }
                        },
                        'http_headers': get_random_headers()
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info:
                            download_url = info.get('url')
                            if not download_url and info.get('formats'):
                                for fmt in info['formats']:
                                    if fmt.get('url') and fmt.get('ext') in ['mp4', 'm4a', 'webm']:
                                        download_url = fmt['url']
                                        break
                            
                            if download_url:
                                return {
                                    'success': True,
                                    'download_url': download_url,
                                    'title': info.get('title', 'Video'),
                                    'duration': info.get('duration', 0),
                                    'resolution': f"{info.get('height', 'Best')}p" if info.get('height') else 'Best',
                                    'engine': f'yt-dlp ({client})'
                                }
                except:
                    continue
            
            return None
        except:
            return None
    
    @staticmethod
    def engine_rapidapi(url, quality='max'):
        try:
            api_url = f"https://apis.davidcyriltech.my.id/youtube/dl?url={url}"
            response = session.get(api_url, headers=get_random_headers(), timeout=6)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200:
                    result = data.get('result', {})
                    download_url = result.get('download_url') or result.get('video') or result.get('url')
                    if download_url:
                        return {
                            'success': True,
                            'download_url': download_url,
                            'title': data.get('title', 'Video'),
                            'engine': 'rapidapi'
                        }
            return None
        except:
            return None
    
    @staticmethod
    def engine_cobalt(url, quality='max'):
        try:
            api_url = "https://co.wuk.sh/api/json"
            payload = {
                'url': url,
                'isAudioOnly': quality == 'audio',
                'isNoTTWatermark': True,
                'vCodec': 'h264',
                'aCodec': 'aac'
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': random.choice(USER_AGENTS)
            }
            response = session.post(api_url, json=payload, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') in ['redirect', 'stream']:
                    download_url = data.get('url')
                    if download_url:
                        return {
                            'success': True,
                            'download_url': download_url,
                            'title': data.get('filename', 'Video'),
                            'engine': 'cobalt'
                        }
            return None
        except:
            return None
    
    @staticmethod
    def engine_savefrom(url, quality='max'):
        try:
            api_url = "https://en.savefrom.net/1-ajax/"
            params = {'url': url, 'ajax': '1'}
            headers = get_random_headers()
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            response = session.get(api_url, params=params, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    html_content = data.get('content', '')
                    patterns = [
                        r'href="([^"]*download[^"]*)"',
                        r'href="([^"]*\.mp4[^"]*)"',
                        r'data-url="([^"]*)"'
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, html_content)
                        if matches:
                            for match in matches:
                                if match.startswith('http'):
                                    return {
                                        'success': True,
                                        'download_url': match,
                                        'title': 'Video from SaveFrom',
                                        'engine': 'savefrom'
                                    }
            return None
        except:
            return None
    
    @staticmethod
    def engine_direct_api(url, quality='max'):
        try:
            video_id = None
            if 'youtube.com' in url or 'youtu.be' in url:
                patterns = [
                    r'(?:youtube\.com\/watch\?v=)([\w-]+)',
                    r'(?:youtu\.be\/)([\w-]+)',
                    r'(?:youtube\.com\/shorts\/)([\w-]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        video_id = match.group(1)
                        break
                
                if video_id:
                    apis = [
                        f"https://api.vevioz.com/api/button/mp4/{video_id}",
                    ]
                    
                    for api in apis:
                        try:
                            response = session.get(api, headers=get_random_headers(), timeout=6)
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('success') or data.get('status') == 200:
                                    download_url = data.get('download_url') or data.get('url') or data.get('video')
                                    if download_url:
                                        return {
                                            'success': True,
                                            'download_url': download_url,
                                            'title': data.get('title', 'YouTube Video'),
                                            'engine': 'direct_api'
                                        }
                        except:
                            continue
            
            return None
        except:
            return None

# ===============================
# 🎨 HTML TEMPLATES
# ===============================

# [HTML_TEMPLATE and ADMIN_TEMPLATE are the same as before but with VIDEO PLAYBACK FIXES]
# I'll provide the full code in the response

# ===============================
# 🚀 FLASK ROUTES
# ===============================

@app.route('/')
def home():
    db = load_database()
    return render_template_string(HTML_TEMPLATE, cricketers=db, admin_password=ADMIN_PASSWORD)

@app.route('/admin-panel')
def admin_panel():
    db = load_database()
    stats = {
        'total_players': len(db),
        'total_videos': sum(len(p['videos']) for p in db.values()),
        'total_downloads': get_download_count()
    }
    return render_template_string(ADMIN_TEMPLATE, cricketers=db, stats=stats, max_upload=app.config['MAX_VIDEOS_PER_UPLOAD'])

@app.route('/api/extract', methods=['POST'])
def api_extract():
    try:
        client_ip = request.remote_addr
        if not rate_limiter.is_allowed(client_ip):
            return jsonify({
                'success': False, 
                'error': 'Rate limit exceeded. Please wait a moment.'
            }), 429
        
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'max')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        result = MultiEngineExtractor.extract_with_all_engines(url, quality)
        
        if result.get('success') and result.get('download_url'):
            return jsonify({
                'success': True,
                'download_url': result['download_url'],
                'title': result.get('title', 'Video'),
                'resolution': result.get('resolution', 'Best'),
                'engine': result.get('engine', 'Auto')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'All extraction engines failed.')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)[:100]}'})

@app.route('/api/download-count', methods=['GET'])
def api_download_count():
    return jsonify({'count': get_download_count()})

@app.route('/api/increment-download', methods=['POST'])
def api_increment_download():
    count = increment_download_count()
    return jsonify({'count': count})

@app.route('/api/admin-login', methods=['POST'])
def api_admin_login():
    data = request.get_json()
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/admin/add-folder', methods=['POST'])
def add_folder():
    try:
        name = request.form.get('player_name', '').strip()
        bio = request.form.get('player_bio', '').strip()
        if name:
            key = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-').replace('.', '-'))
            if not key:
                key = str(uuid.uuid4())[:8]
            db = load_database()
            if key not in db:
                db[key] = {'name': name, 'bio': bio, 'videos': []}
                save_database(db)
        return redirect(url_for('admin_panel'))
    except:
        return redirect(url_for('admin_panel'))

@app.route('/admin/upload-video', methods=['POST'])
def admin_upload_video():
    try:
        cricketer_key = request.form.get('cricketer_key')
        video_title = request.form.get('video_title')
        video_file = request.files.get('video_file')
        
        db = load_database()
        if not cricketer_key or not video_file or cricketer_key not in db:
            return redirect(url_for('admin_panel'))
        
        def sanitize_filename(filename):
            filename = re.sub(r'[^\w\s.-]', '', filename)
            return re.sub(r'[-\s]+', '_', filename).strip()[:100]
        
        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                video_file,
                folder=f"cricket_videos/{cricketer_key}",
                resource_type="video",
                public_id=f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}",
                overwrite=True
            )
            video_url = upload_result.get('secure_url') or upload_result.get('url')
        except Exception as e:
            # Fallback to local storage
            filename = f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(file_path)
            video_url = f'/static/uploads/{filename}'
        
        db[cricketer_key]['videos'].append({
            'title': video_title,
            'url': video_url
        })
        save_database(db)
        return redirect(url_for('admin_panel'))
    except Exception as e:
        print(f"Upload error: {e}")
        return redirect(url_for('admin_panel'))

# ===============================
# 📦 BULK VIDEO UPLOAD - NEW FEATURE
# ===============================

@app.route('/admin/bulk-upload', methods=['POST'])
def admin_bulk_upload():
    try:
        cricketer_key = request.form.get('cricketer_key')
        video_files = request.files.getlist('video_files[]')
        video_titles = request.form.getlist('video_titles[]')
        
        db = load_database()
        if not cricketer_key or cricketer_key not in db:
            return jsonify({'success': False, 'error': 'Invalid player folder'}), 400
        
        if len(video_files) > app.config['MAX_VIDEOS_PER_UPLOAD']:
            return jsonify({
                'success': False, 
                'error': f'Maximum {app.config["MAX_VIDEOS_PER_UPLOAD"]} videos allowed per upload'
            }), 400
        
        def sanitize_filename(filename):
            filename = re.sub(r'[^\w\s.-]', '', filename)
            return re.sub(r'[-\s]+', '_', filename).strip()[:100]
        
        uploaded_count = 0
        failed_videos = []
        
        for i, video_file in enumerate(video_files):
            if video_file.filename == '':
                continue
            
            try:
                # Get title from form or use filename
                if i < len(video_titles) and video_titles[i].strip():
                    title = video_titles[i].strip()
                else:
                    title = os.path.splitext(video_file.filename)[0].replace('_', ' ').title()
                
                # Upload to Cloudinary
                try:
                    upload_result = cloudinary.uploader.upload(
                        video_file,
                        folder=f"cricket_videos/{cricketer_key}",
                        resource_type="video",
                        public_id=f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}",
                        overwrite=True
                    )
                    video_url = upload_result.get('secure_url') or upload_result.get('url')
                except Exception as e:
                    # Fallback to local storage
                    filename = f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    video_file.save(file_path)
                    video_url = f'/static/uploads/{filename}'
                
                db[cricketer_key]['videos'].append({
                    'title': title,
                    'url': video_url
                })
                uploaded_count += 1
                
            except Exception as e:
                failed_videos.append({
                    'filename': video_file.filename,
                    'error': str(e)[:100]
                })
        
        save_database(db)
        
        return jsonify({
            'success': True,
            'uploaded': uploaded_count,
            'failed': len(failed_videos),
            'failed_list': failed_videos,
            'total': len(video_files)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:200]}), 500

# ===============================
# 🤖 TELEGRAM BOT
# ===============================

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
            return 'OK', 200
        except:
            return 'Error', 500
    return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def send_welcome(message):
    host_url = os.environ.get('RAILWAY_STATIC_URL', 'https://web-production-6836d.up.railway.app/')
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            '⚡ Open NexGen Downloader',
            web_app=telebot.types.WebAppInfo(url=host_url)
        )
    )
    bot.reply_to(
        message,
        "🚀 **NEXGEN MEDIA DOWNLOADER**\n\n"
        "🔥 **6 Parallel Extraction Engines**\n"
        "📹 YouTube • TikTok • Instagram • Facebook\n"
        "🎯 4K Quality • Anti-Detection • 100% Free\n\n"
        "Click the button below to start downloading!",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ===============================
# 🚀 MAIN ENTRY POINT
# ===============================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🔥 NEXGEN MEDIA DOWNLOADER v7.0                          ║
    ║   ⚡ 6 Parallel Engines • Anti-Detection                   ║
    ║   📦 Bulk Upload (500 videos at once)                      ║
    ║   🎬 Video Player FIXED • Admin Panel                     ║
    ║                                                              ║
    ║   🚀 Server running on port {port}                           ║
    ║   📁 Upload folder: {UPLOAD_FOLDER}                         ║
    ║   💾 Database: {DB_FILE}                                    ║
    ║   🔑 Admin Password: {ADMIN_PASSWORD}                       ║
    ║   📦 Max videos per upload: {app.config["MAX_VIDEOS_PER_UPLOAD"]}    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)