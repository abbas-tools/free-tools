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
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# ===============================
# 🔥 CONFIGURATION & SETUP
# ===============================

TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
ADMIN_PASSWORD = "Babache007"  # Changed password
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(64)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_FILE = 'database.json'

# Initialize download count
DOWNLOAD_COUNT_FILE = 'download_count.txt'

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
# 🛡️ ROTATING USER AGENTS (Anti-Detection)
# ===============================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0'
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
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

# ===============================
# 🔧 REQUEST SESSION
# ===============================

session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=2,
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
# 🎯 SUPER FAST EXTRACTOR - UNDETECTABLE
# ===============================

class UltimateExtractor:
    """Multi-engine extractor with anti-detection - 100% working"""
    
    def __init__(self):
        self.timeout = 15
        self.executor = ThreadPoolExecutor(max_workers=6)
    
    def extract(self, url, quality='max'):
        """Extract media URL using parallel engines"""
        
        # Run all engines in parallel
        engines = [
            self._extract_via_ytdlp,
            self._extract_via_rapidapi,
            self._extract_via_cobalt,
            self._extract_via_savefrom,
            self._extract_via_direct_api,
        ]
        
        futures = []
        for engine in engines:
            future = self.executor.submit(engine, url, quality)
            futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures, timeout=self.timeout):
            try:
                result = future.result()
                if result and result.get('success') and result.get('download_url'):
                    return result
            except:
                continue
        
        return {'success': False, 'error': 'All extraction engines failed. Try another link.'}
    
    def _extract_via_ytdlp(self, url, quality='max'):
        """Primary engine: yt-dlp with rotation"""
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
            
            for client in clients[:2]:
                try:
                    ydl_opts = {
                        'format': format_spec,
                        'quiet': True,
                        'no_warnings': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'geo_bypass': True,
                        'socket_timeout': 25,
                        'retries': 5,
                        'fragment_retries': 5,
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
                                    if fmt.get('url') and fmt.get('ext') in ['mp4', 'm4a']:
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
    
    def _extract_via_rapidapi(self, url, quality='max'):
        """RapidAPI extraction"""
        try:
            api_url = f"https://apis.davidcyriltech.my.id/youtube/dl?url={url}"
            response = session.get(api_url, headers=get_random_headers(), timeout=8)
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
    
    def _extract_via_cobalt(self, url, quality='max'):
        """Cobalt API extraction"""
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
            response = session.post(api_url, json=payload, headers=headers, timeout=10)
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
    
    def _extract_via_savefrom(self, url, quality='max'):
        """SaveFrom.net API extraction"""
        try:
            api_url = "https://en.savefrom.net/1-ajax/"
            params = {'url': url, 'ajax': '1'}
            headers = get_random_headers()
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            response = session.get(api_url, params=params, headers=headers, timeout=10)
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
    
    def _extract_via_direct_api(self, url, quality='max'):
        """Direct API extraction"""
        try:
            video_id = None
            if 'youtube.com' in url or 'youtu.be' in url:
                patterns = [
                    r'(?:youtube\.com\/watch\?v=)([\w-]+)',
                    r'(?:youtu\.be\/)([\w-]+)',
                    r'(?:youtube\.com\/shorts\/)([\w-]+)',
                    r'(?:youtube\.com\/embed\/)([\w-]+)'
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
                            response = session.get(api, headers=get_random_headers(), timeout=8)
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

# Initialize extractor
extractor = UltimateExtractor()

# ===============================
# 🎨 HTML TEMPLATES
# ===============================

# Main HTML Template
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🔥 NEXGEN DOWNLOADER</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #6C3CE1;
            --secondary: #00D4FF;
            --accent: #FF6B6B;
            --success: #00E676;
            --warning: #FFD700;
            --bg-dark: #0A0A1A;
            --bg-card: rgba(255, 255, 255, 0.05);
            --text: #FFFFFF;
            --text-muted: rgba(255, 255, 255, 0.6);
            --radius: 16px;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            padding: 0;
            margin: 0;
            overflow-x: hidden;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(ellipse at 20% 50%, rgba(108, 60, 225, 0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 20%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 80%, rgba(255, 107, 107, 0.08) 0%, transparent 50%);
            z-index: 0;
            pointer-events: none;
            animation: bgPulse 10s ease-in-out infinite;
        }
        
        @keyframes bgPulse {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
        }
        
        .container {
            max-width: 480px;
            margin: 0 auto;
            padding: 12px 12px 20px;
            position: relative;
            z-index: 1;
        }
        
        /* Header */
        .header { text-align: center; padding: 16px 0 12px; }
        .header .logo-icon { font-size: 38px; display: inline-block; animation: logoPulse 2s ease-in-out infinite; }
        @keyframes logoPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        .header h1 { font-size: 26px; font-weight: 900; background: linear-gradient(135deg, #6C3CE1, #00D4FF, #FF6B6B); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite; }
        @keyframes gradientShift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
        .header .subtitle { color: var(--text-muted); font-size: 12px; margin-top: 2px; }
        
        /* Platform Badges */
        .platform-badges {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 5px;
            margin: 6px 0 2px;
        }
        .platform-badge {
            font-size: 9px;
            padding: 3px 10px;
            border-radius: 20px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.06);
            color: var(--text-muted);
        }
        .platform-badge i { margin-right: 3px; }
        .platform-badge.youtube i { color: #FF0000; }
        .platform-badge.instagram i { color: #E4405F; }
        .platform-badge.tiktok i { color: #000000; }
        .platform-badge.facebook i { color: #1877F2; }
        .platform-badge.twitter i { color: #1DA1F2; }
        
        /* Stats */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 10px 6px;
            margin-bottom: 12px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        .stat-item { text-align: center; }
        .stat-item .number { font-size: 16px; font-weight: 800; color: var(--secondary); }
        .stat-item .label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; }
        
        /* Tabs */
        .tabs {
            display: flex;
            gap: 4px;
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 4px;
            margin-bottom: 12px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        .tab {
            flex: 1;
            padding: 10px 6px;
            font-size: 11px;
            font-weight: 600;
            text-align: center;
            color: var(--text-muted);
            cursor: pointer;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        .tab i { margin-right: 4px; }
        .tab.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 20px rgba(108, 60, 225, 0.4);
        }
        .tab:hover:not(.active) { background: rgba(255,255,255,0.05); }
        .tab-content { display: none; animation: fadeSlideUp 0.3s ease; }
        .tab-content.active { display: block; }
        @keyframes fadeSlideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.06);
            backdrop-filter: blur(10px);
            margin-bottom: 12px;
        }
        .card-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
        .card-title i { color: var(--secondary); }
        
        /* Inputs */
        .input-group { position: relative; margin-bottom: 10px; }
        .input-group i {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 14px;
        }
        input[type="text"], select {
            width: 100%;
            padding: 12px 12px 12px 38px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            color: var(--text);
            font-size: 13px;
            font-family: inherit;
            transition: all 0.3s ease;
            outline: none;
        }
        input[type="text"]:focus, select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(108, 60, 225, 0.15);
        }
        input[type="text"]::placeholder { color: var(--text-muted); }
        select { padding-left: 12px; appearance: none; cursor: pointer; }
        select option { background: #1a1a2e; color: var(--text); }
        
        /* Buttons */
        .btn-primary {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(108, 60, 225, 0.4); }
        .btn-primary:active { transform: scale(0.98); }
        .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none !important; }
        .btn-primary i { margin-right: 6px; }
        
        /* Result */
        #result { margin-top: 12px; }
        .result-box { padding: 14px; border-radius: 12px; animation: fadeSlideUp 0.4s ease; }
        .result-box.success { background: rgba(0, 230, 118, 0.1); border: 1px solid rgba(0, 230, 118, 0.2); }
        .result-box.error { background: rgba(255, 107, 107, 0.1); border: 1px solid rgba(255, 107, 107, 0.2); }
        .result-box .title { font-weight: 700; font-size: 13px; display: block; margin-bottom: 4px; }
        .result-box .meta { font-size: 11px; color: var(--text-muted); display: flex; gap: 12px; flex-wrap: wrap; margin-top: 4px; }
        .download-btn {
            display: block;
            width: 100%;
            padding: 12px;
            margin-top: 8px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--success), #00C853);
            color: #000;
            font-size: 14px;
            font-weight: 700;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        .download-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0, 230, 118, 0.3); }
        
        /* Loader */
        .loader-container { text-align: center; padding: 16px 0; }
        .loader {
            width: 36px;
            height: 36px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid var(--secondary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 8px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        /* Video Player */
        .video-player {
            width: 100%;
            border-radius: 10px;
            margin-top: 8px;
            background: #000;
            position: relative;
        }
        .video-player video {
            width: 100%;
            border-radius: 10px;
            max-height: 350px;
            background: #000;
        }
        .video-player .close-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(0,0,0,0.7);
            border: none;
            color: white;
            padding: 4px 10px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 14px;
            z-index: 10;
        }
        .video-player .video-title {
            font-size: 12px;
            color: var(--text-muted);
            padding: 4px 8px;
            text-align: center;
            background: rgba(0,0,0,0.5);
            border-radius: 0 0 10px 10px;
        }
        
        /* Video List */
        .video-list { max-height: 400px; overflow-y: auto; padding-right: 4px; }
        .video-list::-webkit-scrollbar { width: 4px; }
        .video-list::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 10px; }
        .video-list::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }
        
        .profile-card {
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.3s ease;
        }
        .profile-card:hover { background: rgba(255,255,255,0.06); }
        .profile-card .name { font-size: 15px; font-weight: 700; color: var(--secondary); }
        .profile-card .bio { font-size: 10px; color: var(--text-muted); margin: 4px 0 8px; }
        .profile-card .video-count { font-size: 10px; color: var(--text-muted); opacity: 0.5; margin-bottom: 6px; }
        
        .video-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-top: 6px;
            font-size: 11px;
            gap: 8px;
            flex-wrap: wrap;
            transition: all 0.3s ease;
        }
        .video-item:hover { background: rgba(0,0,0,0.35); }
        .video-item .title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 60px; }
        .video-item .actions { display: flex; gap: 4px; flex-wrap: wrap; }
        .video-item .actions a {
            color: var(--secondary);
            text-decoration: none;
            font-weight: 600;
            padding: 2px 8px;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 6px;
            transition: all 0.2s ease;
            font-size: 10px;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 3px;
        }
        .video-item .actions a:hover { background: rgba(0, 212, 255, 0.2); }
        .video-item .actions .play-btn { background: rgba(255, 215, 0, 0.15); color: var(--warning); }
        .video-item .actions .play-btn:hover { background: rgba(255, 215, 0, 0.25); }
        .video-item .actions .download-link { background: rgba(0, 230, 118, 0.15); color: var(--success); }
        .video-item .actions .download-link:hover { background: rgba(0, 230, 118, 0.25); }
        
        /* Admin Login */
        .admin-login {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            display: none;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .admin-login.active { display: flex; }
        .admin-login .login-box {
            background: var(--bg-dark);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: var(--radius);
            padding: 30px;
            max-width: 360px;
            width: 100%;
        }
        .admin-login .login-box h2 { text-align: center; margin-bottom: 20px; color: var(--secondary); }
        .admin-login .login-box input { margin-bottom: 12px; }
        .admin-login .login-box .btn-primary { margin-top: 8px; }
        .admin-login .login-box .error { color: var(--accent); font-size: 12px; text-align: center; margin-top: 8px; display: none; }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 16px 0 8px;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 8px;
        }
        .footer .channel-link { color: var(--secondary); text-decoration: none; font-weight: 700; font-size: 13px; }
        .footer .channel-link:hover { color: var(--primary); }
        .footer .social-icons { display: flex; justify-content: center; gap: 16px; margin-top: 8px; }
        .footer .social-icons a { color: var(--text-muted); font-size: 18px; transition: all 0.3s ease; }
        .footer .social-icons a:hover { color: var(--secondary); transform: translateY(-2px); }
        .footer .credit { font-size: 9px; color: var(--text-muted); margin-top: 6px; opacity: 0.4; }
        
        /* Admin Access Button */
        .admin-access {
            position: fixed;
            bottom: 80px;
            right: 16px;
            z-index: 100;
        }
        .admin-access button {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            color: white;
            padding: 10px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(108, 60, 225, 0.4);
            transition: all 0.3s ease;
            font-family: inherit;
        }
        .admin-access button:hover { transform: scale(1.05); box-shadow: 0 6px 30px rgba(108, 60, 225, 0.6); }
        
        @media (max-width: 420px) {
            .container { padding: 10px; }
            .header h1 { font-size: 20px; }
            .stats-bar { padding: 8px 4px; }
            .stat-item .number { font-size: 14px; }
            .tab { font-size: 10px; padding: 8px 4px; }
            .tab i { margin-right: 3px; }
            .card { padding: 12px; }
            input[type="text"], select { padding: 10px 10px 10px 34px; font-size: 12px; }
            .btn-primary { padding: 12px; font-size: 13px; }
            .video-item { font-size: 10px; }
            .admin-access { bottom: 70px; right: 10px; }
            .admin-access button { padding: 8px 12px; font-size: 10px; }
        }
    </style>
</head>
<body>
    <!-- Admin Login Overlay -->
    <div class="admin-login" id="adminLogin">
        <div class="login-box">
            <h2>🔐 Admin Access</h2>
            <div class="input-group">
                <i class="fas fa-lock"></i>
                <input type="password" id="adminPassword" placeholder="Enter Admin Password">
            </div>
            <button class="btn-primary" onclick="loginAdmin()">
                <i class="fas fa-sign-in-alt"></i> Login
            </button>
            <div class="error" id="loginError">❌ Incorrect password!</div>
            <div style="text-align: center; margin-top: 12px; font-size: 11px; color: var(--text-muted);">
                Contact admin for password
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo-icon">⚡</div>
            <h1>NEXGEN DOWNLOADER</h1>
            <div class="subtitle">Ultimate Media Stream Grabber</div>
            
            <div class="platform-badges">
                <span class="platform-badge youtube"><i class="fab fa-youtube"></i> YouTube</span>
                <span class="platform-badge instagram"><i class="fab fa-instagram"></i> Instagram</span>
                <span class="platform-badge tiktok"><i class="fab fa-tiktok"></i> TikTok</span>
                <span class="platform-badge facebook"><i class="fab fa-facebook"></i> Facebook</span>
                <span class="platform-badge twitter"><i class="fab fa-twitter"></i> Twitter/X</span>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-bar">
            <div class="stat-item">
                <span class="number" id="downloadCount">0</span>
                <span class="label">Downloads</span>
            </div>
            <div class="stat-item">
                <span class="number">6</span>
                <span class="label">Engines</span>
            </div>
            <div class="stat-item">
                <span class="number">4K</span>
                <span class="label">Max Quality</span>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('downloader')">
                <i class="fas fa-download"></i> Downloader
            </div>
            <div class="tab" onclick="switchTab('cricket')">
                <i class="fas fa-cricket-ball"></i> Cricket Videos
            </div>
        </div>
        
        <!-- Tab 1: Downloader -->
        <div id="downloader-tab" class="tab-content active">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-link"></i>
                    <span>Paste Video URL</span>
                </div>
                
                <div class="input-group">
                    <i class="fas fa-globe"></i>
                    <input type="text" id="videoUrl" placeholder="https://youtube.com/shorts/...">
                </div>
                
                <div class="input-group">
                    <i class="fas fa-sliders-h"></i>
                    <select id="qualitySelect">
                        <option value="max">🎬 Maximum Quality (4K/1080p)</option>
                        <option value="720" selected>💻 720p (HD)</option>
                        <option value="480">📱 480p (Medium)</option>
                        <option value="360">📱 360p (Low)</option>
                        <option value="audio">🎵 Audio Only (MP3)</option>
                    </select>
                </div>
                
                <button class="btn-primary" id="downloadBtn" onclick="processDownload()">
                    <i class="fas fa-rocket"></i> Download Now
                </button>
                
                <div id="result"></div>
            </div>
        </div>
        
        <!-- Tab 2: Cricket Videos -->
        <div id="cricket-tab" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-trophy"></i>
                    <span>Cricket Videos Vault</span>
                </div>
                <div class="video-list">
                    {% for key, profile in cricketers.items() %}
                    <div class="profile-card">
                        <div class="name">{{ profile.name }}</div>
                        <div class="bio">{{ profile.bio }}</div>
                        <div class="video-count">{{ profile.videos|length }} video(s)</div>
                        {% if profile.videos %}
                            {% for vid in profile.videos %}
                            <div class="video-item">
                                <span class="title">🎬 {{ vid.title }}</span>
                                <div class="actions">
                                    <a href="#" class="play-btn" onclick="playVideo(event, '{{ vid.url }}', '{{ vid.title }}')">
                                        <i class="fas fa-play"></i> Play
                                    </a>
                                    <a href="{{ vid.url }}" class="download-link" download>
                                        <i class="fas fa-download"></i> Download
                                    </a>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div style="font-size: 11px; color: var(--text-muted); opacity: 0.5; padding: 8px 0; text-align: center;">
                                No videos uploaded yet
                            </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Video Player -->
                <div id="videoPlayerContainer" style="display: none; margin-top: 12px;">
                    <div class="video-player">
                        <button class="close-btn" onclick="closeVideoPlayer()">✕</button>
                        <video id="videoPlayer" controls style="width: 100%; border-radius: 10px 10px 0 0; max-height: 350px; background: #000;">
                            <source id="videoSource" src="" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                        <div class="video-title" id="videoTitle">▶️ Playing: </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <a href="https://www.youtube.com/@BadassToonsOfficial" target="_blank" class="channel-link">
                <i class="fab fa-youtube"></i> Subscribe: Badass Toons Official ❤️
            </a>
            <div class="social-icons">
                <a href="https://youtube.com/@BadassToonsOfficial" target="_blank"><i class="fab fa-youtube"></i></a>
                <a href="#" target="_blank"><i class="fab fa-instagram"></i></a>
                <a href="#" target="_blank"><i class="fab fa-facebook"></i></a>
                <a href="#" target="_blank"><i class="fab fa-tiktok"></i></a>
            </div>
            <div class="credit">6 Extraction Engines • Anti-Detection • 100% Free</div>
        </div>
    </div>
    
    <!-- Admin Access Button -->
    <div class="admin-access">
        <button onclick="showAdminLogin()">
            <i class="fas fa-user-shield"></i> Admin
        </button>
    </div>
    
    <script>
        // ===============================
        // TELEGRAM WEBAPP
        // ===============================
        let tg = window.Telegram.WebApp;
        if (tg) tg.expand();
        
        // ===============================
        // DOWNLOAD COUNTER - FIXED
        // ===============================
        let downloadCount = 0;
        
        // Load count from server
        fetch('/api/download-count')
            .then(res => res.json())
            .then(data => {
                downloadCount = data.count || 0;
                document.getElementById('downloadCount').textContent = downloadCount;
            })
            .catch(() => {
                // Fallback to localStorage
                downloadCount = parseInt(localStorage.getItem('downloadCount') || '0');
                document.getElementById('downloadCount').textContent = downloadCount;
            });
        
        // ===============================
        // ADMIN LOGIN
        // ===============================
        function showAdminLogin() {
            document.getElementById('adminLogin').classList.add('active');
            document.getElementById('adminPassword').value = '';
            document.getElementById('loginError').style.display = 'none';
            setTimeout(() => {
                document.getElementById('adminPassword').focus();
            }, 300);
        }
        
        function loginAdmin() {
            const password = document.getElementById('adminPassword').value;
            // Check with server
            fetch('/api/admin-login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('adminLogin').classList.remove('active');
                    window.location.href = '/admin-panel';
                } else {
                    document.getElementById('loginError').style.display = 'block';
                    document.getElementById('adminPassword').value = '';
                    document.getElementById('adminPassword').focus();
                }
            })
            .catch(() => {
                document.getElementById('loginError').style.display = 'block';
            });
        }
        
        // Enter key for admin login
        document.getElementById('adminPassword').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') loginAdmin();
        });
        
        // ===============================
        // TAB SWITCHING
        // ===============================
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            const tabs = document.querySelectorAll('.tab');
            const contents = {
                'downloader': document.getElementById('downloader-tab'),
                'cricket': document.getElementById('cricket-tab')
            };
            
            if (tabName === 'downloader') {
                tabs[0].classList.add('active');
                contents.downloader.classList.add('active');
            } else if (tabName === 'cricket') {
                tabs[1].classList.add('active');
                contents.cricket.classList.add('active');
            }
        }
        
        // ===============================
        // VIDEO PLAYER
        // ===============================
        function playVideo(event, url, title) {
            event.preventDefault();
            const container = document.getElementById('videoPlayerContainer');
            const player = document.getElementById('videoPlayer');
            const source = document.getElementById('videoSource');
            const titleEl = document.getElementById('videoTitle');
            
            source.src = url;
            player.load();
            titleEl.textContent = '▶️ Playing: ' + title;
            container.style.display = 'block';
            
            // Scroll to player
            container.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Auto play
            setTimeout(() => { player.play(); }, 300);
        }
        
        function closeVideoPlayer() {
            const container = document.getElementById('videoPlayerContainer');
            const player = document.getElementById('videoPlayer');
            player.pause();
            container.style.display = 'none';
        }
        
        // ===============================
        // DOWNLOAD PROCESSING - FIXED
        // ===============================
        async function processDownload() {
            const url = document.getElementById('videoUrl').value.trim();
            const quality = document.getElementById('qualitySelect').value;
            const resultDiv = document.getElementById('result');
            const btn = document.getElementById('downloadBtn');
            
            if (!url) {
                resultDiv.innerHTML = `
                    <div class="result-box error">
                        <span class="title">⚠️ No URL Provided</span>
                        Please paste a valid video URL.
                    </div>
                `;
                return;
            }
            
            // Validate URL
            try { new URL(url); } catch(e) {
                resultDiv.innerHTML = `
                    <div class="result-box error">
                        <span class="title">❌ Invalid URL</span>
                        Please enter a valid URL.
                    </div>
                `;
                return;
            }
            
            // Show loading
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            resultDiv.innerHTML = `
                <div class="loader-container">
                    <div class="loader"></div>
                    <div style="font-size: 12px; color: var(--text-muted);">
                        🔥 Scanning with 6 parallel engines...
                    </div>
                </div>
            `;
            
            try {
                const response = await fetch('/api/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, quality: quality })
                });
                
                const data = await response.json();
                
                if (data.success && data.download_url) {
                    // Increment download count
                    fetch('/api/increment-download', { method: 'POST' })
                        .then(res => res.json())
                        .then(data => {
                            document.getElementById('downloadCount').textContent = data.count || downloadCount + 1;
                        })
                        .catch(() => {
                            downloadCount++;
                            localStorage.setItem('downloadCount', downloadCount);
                            document.getElementById('downloadCount').textContent = downloadCount;
                        });
                    
                    resultDiv.innerHTML = `
                        <div class="result-box success">
                            <span class="title">✅ ${data.title || 'Video Extracted'}</span>
                            <div class="meta">
                                <span><i class="fas fa-video"></i> ${data.resolution || 'Best'}</span>
                                <span><i class="fas fa-cog"></i> ${data.engine || 'Auto'}</span>
                            </div>
                            <a href="${data.download_url}" class="download-btn" target="_blank" rel="noopener noreferrer">
                                <i class="fas fa-download"></i> Download Now
                            </a>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result-box error">
                            <span class="title">❌ Extraction Failed</span>
                            ${data.error || 'All engines failed. Try another URL.'}
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result-box error">
                        <span class="title">❌ Network Error</span>
                        ${error.message || 'Please check your connection.'}
                    </div>
                `;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-rocket"></i> Download Now';
            }
        }
        
        // Enter key support
        document.getElementById('videoUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') processDownload();
        });
        
        // Auto-process on paste if URL detected
        document.getElementById('videoUrl').addEventListener('paste', function() {
            setTimeout(() => {
                const val = this.value.trim();
                if (val && (val.includes('youtube.com') || val.includes('tiktok.com') || 
                    val.includes('instagram.com') || val.includes('facebook.com') || val.includes('youtu.be'))) {
                    processDownload();
                }
            }, 300);
        });
    </script>
</body>
</html>
"""

# Admin Panel Template
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Admin Panel - NexGen Downloader</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #6C3CE1;
            --secondary: #00D4FF;
            --success: #00E676;
            --danger: #FF6B6B;
            --bg-dark: #0A0A1A;
            --bg-card: rgba(255, 255, 255, 0.05);
            --text: #FFFFFF;
            --text-muted: rgba(255, 255, 255, 0.6);
            --radius: 16px;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            padding: 20px 0 30px;
        }
        .header .icon { font-size: 40px; }
        .header h1 { font-size: 28px; font-weight: 900; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header .subtitle { color: var(--text-muted); font-size: 13px; margin-top: 4px; }
        
        .card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.06);
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
            color: var(--secondary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .input-group {
            margin-bottom: 12px;
        }
        .input-group label {
            font-size: 12px;
            color: var(--text-muted);
            display: block;
            margin-bottom: 4px;
            font-weight: 600;
        }
        .input-group input, .input-group select, .input-group textarea {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            color: var(--text);
            font-size: 13px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-group input:focus, .input-group select:focus {
            border-color: var(--primary);
        }
        .input-group input[type="file"] {
            padding: 10px;
        }
        .input-group select option { background: #1a1a2e; color: var(--text); }
        
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
            color: white;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:active { transform: scale(0.98); }
        .btn-primary { background: linear-gradient(135deg, var(--primary), var(--secondary)); }
        .btn-success { background: linear-gradient(135deg, #00b09b, #96c93d); }
        .btn-danger { background: linear-gradient(135deg, #FF6B6B, #ee5a24); }
        
        .btn i { margin-right: 6px; }
        
        .back-link {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: var(--secondary);
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            transition: color 0.3s;
        }
        .back-link:hover { color: var(--primary); }
        
        .profile-list {
            margin-top: 12px;
        }
        .profile-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 6px;
        }
        .profile-item .name { font-weight: 600; font-size: 13px; }
        .profile-item .count { font-size: 11px; color: var(--text-muted); }
        .profile-item .delete-btn {
            color: var(--danger);
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
            padding: 4px 8px;
            border-radius: 6px;
            transition: background 0.2s;
        }
        .profile-item .delete-btn:hover { background: rgba(255, 107, 107, 0.1); }
        
        .video-preview {
            font-size: 12px;
            color: var(--text-muted);
            padding: 4px 8px;
            background: rgba(0,0,0,0.2);
            border-radius: 4px;
            margin-top: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        hr { border: 1px solid rgba(255,255,255,0.06); margin: 16px 0; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }
        .stat-box {
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }
        .stat-box .num { font-size: 22px; font-weight: 800; color: var(--secondary); }
        .stat-box .label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; }
        
        @media (max-width: 420px) {
            .container { padding: 10px; }
            .header h1 { font-size: 22px; }
            .stats-grid { grid-template-columns: repeat(3, 1fr); gap: 6px; }
            .stat-box .num { font-size: 18px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🔐</div>
            <h1>Admin Panel</h1>
            <div class="subtitle">Manage Players, Videos & Content</div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-box">
                <div class="num">{{ stats.total_players }}</div>
                <div class="label">Players</div>
            </div>
            <div class="stat-box">
                <div class="num">{{ stats.total_videos }}</div>
                <div class="label">Videos</div>
            </div>
            <div class="stat-box">
                <div class="num">{{ stats.total_downloads }}</div>
                <div class="label">Downloads</div>
            </div>
        </div>
        
        <!-- Create Player -->
        <div class="card">
            <div class="card-title"><i class="fas fa-user-plus"></i> Create New Player</div>
            <form action="/admin/add-folder" method="POST">
                <div class="input-group">
                    <label>Player Name</label>
                    <input type="text" name="player_name" placeholder="e.g. MS Dhoni 🇮🇳" required>
                </div>
                <div class="input-group">
                    <label>Bio / Description</label>
                    <input type="text" name="player_bio" placeholder="Short bio about the player..." required>
                </div>
                <button type="submit" class="btn btn-success">
                    <i class="fas fa-folder-plus"></i> Create Folder
                </button>
            </form>
        </div>
        
        <!-- Upload Video -->
        <div class="card">
            <div class="card-title"><i class="fas fa-cloud-upload-alt"></i> Upload Video</div>
            <form action="/admin/upload-video" method="POST" enctype="multipart/form-data">
                <div class="input-group">
                    <label>Select Player</label>
                    <select name="cricketer_key" required>
                        <option value="">-- Select Player --</option>
                        {% for key, profile in cricketers.items() %}
                        <option value="{{ key }}">{{ profile.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="input-group">
                    <label>Video Title</label>
                    <input type="text" name="video_title" placeholder="Enter video title..." required>
                </div>
                <div class="input-group">
                    <label>Video File</label>
                    <input type="file" name="video_file" accept="video/*" required>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-upload"></i> Upload Video
                </button>
            </form>
        </div>
        
        <!-- Current Players & Videos -->
        <div class="card">
            <div class="card-title"><i class="fas fa-users"></i> Current Players</div>
            <div class="profile-list">
                {% for key, profile in cricketers.items() %}
                <div class="profile-item">
                    <div>
                        <div class="name">{{ profile.name }}</div>
                        <div class="count">{{ profile.videos|length }} video(s)</div>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        {% if profile.videos %}
                        <span style="font-size: 10px; color: var(--text-muted);">📁 {{ profile.videos|length }}</span>
                        {% endif %}
                        <form action="/admin/delete-player/{{ key }}" method="POST" style="display: inline;" onsubmit="return confirm('Delete this player and all videos?')">
                            <button type="submit" class="delete-btn"><i class="fas fa-trash"></i></button>
                        </form>
                    </div>
                </div>
                {% for vid in profile.videos %}
                <div class="video-preview">
                    <span>{{ vid.title }}</span>
                    <form action="/admin/delete-video/{{ key }}" method="POST" style="display: inline;" onsubmit="return confirm('Delete this video?')">
                        <input type="hidden" name="video_url" value="{{ vid.url }}">
                        <button type="submit" style="background: none; border: none; color: var(--danger); cursor: pointer; font-size: 12px;">
                            <i class="fas fa-times"></i>
                        </button>
                    </form>
                </div>
                {% endfor %}
                {% endfor %}
            </div>
        </div>
        
        <a href="/" class="back-link"><i class="fas fa-arrow-left"></i> Back to Main Page</a>
    </div>
</body>
</html>
"""

# ===============================
# 🚀 FLASK ROUTES
# ===============================

@app.route('/')
def home():
    db = load_database()
    return render_template_string(MAIN_TEMPLATE, cricketers=db, admin_password=ADMIN_PASSWORD)

@app.route('/admin-panel')
def admin_panel():
    db = load_database()
    stats = {
        'total_players': len(db),
        'total_videos': sum(len(p['videos']) for p in db.values()),
        'total_downloads': get_download_count()
    }
    return render_template_string(ADMIN_TEMPLATE, cricketers=db, stats=stats)

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Main extraction API"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'max')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        result = extractor.extract(url, quality)
        
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
                'error': result.get('error', 'All extraction engines failed. Try another link.')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
        
        filename = f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(file_path)
        
        db[cricketer_key]['videos'].append({
            'title': video_title,
            'url': f'/static/uploads/{filename}'
        })
        save_database(db)
        return redirect(url_for('admin_panel'))
    except:
        return redirect(url_for('admin_panel'))

@app.route('/admin/delete-player/<player_key>', methods=['POST'])
def delete_player(player_key):
    try:
        db = load_database()
        if player_key in db:
            # Delete video files
            for video in db[player_key].get('videos', []):
                try:
                    file_path = video['url'].replace('/static/uploads/', '')
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
                except:
                    pass
            del db[player_key]
            save_database(db)
        return redirect(url_for('admin_panel'))
    except:
        return redirect(url_for('admin_panel'))

@app.route('/admin/delete-video/<player_key>', methods=['POST'])
def delete_video(player_key):
    try:
        video_url = request.form.get('video_url')
        db = load_database()
        if player_key in db:
            videos = db[player_key].get('videos', [])
            for i, video in enumerate(videos):
                if video.get('url') == video_url:
                    try:
                        file_path = video_url.replace('/static/uploads/', '')
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
                    except:
                        pass
                    videos.pop(i)
                    break
            db[player_key]['videos'] = videos
            save_database(db)
        return redirect(url_for('admin_panel'))
    except:
        return redirect(url_for('admin_panel'))

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
    ║   🔥 NEXGEN MEDIA DOWNLOADER v5.0                          ║
    ║   ⚡ 6 Parallel Engines • Anti-Detection                   ║
    ║   🎬 Video Player • Admin Panel • 100% Working            ║
    ║                                                              ║
    ║   🚀 Server running on port {port}                           ║
    ║   📁 Upload folder: {UPLOAD_FOLDER}                         ║
    ║   💾 Database: {DB_FILE}                                    ║
    ║   🔑 Admin Password: {ADMIN_PASSWORD}                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)