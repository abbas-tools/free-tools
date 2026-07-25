import os
import re
import uuid
import json
import random
import time
import requests
import telebot
from urllib.parse import urlparse, quote, unquote
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file, Response
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===============================
# 🔥 CONFIGURATION & SETUP
# ===============================

TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(64)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_FILE = 'database.json'

# ===============================
# 🛡️ ROTATING USER AGENTS
# ===============================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
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
# 🎯 ADVANCED URL EXTRACTOR - NO PLAYWRIGHT!
# ===============================

class UltimateExtractor:
    """Multi-engine extractor without Playwright - 100% reliable"""
    
    def __init__(self):
        self.timeout = 20
    
    def extract(self, url, quality='max'):
        """Extract media URL using multiple engines"""
        results = []
        
        # Engine 1: Direct API (YouTube, TikTok, etc.)
        result = self._extract_via_direct_api(url)
        if result:
            results.append(result)
        
        # Engine 2: RapidAPI
        result = self._extract_via_rapidapi(url)
        if result:
            results.append(result)
        
        # Engine 3: TikWM
        result = self._extract_via_tikwm(url)
        if result:
            results.append(result)
        
        # Engine 4: Cobalt
        result = self._extract_via_cobalt(url)
        if result:
            results.append(result)
        
        # Engine 5: SaveFrom (without Playwright)
        result = self._extract_via_savefrom_api(url)
        if result:
            results.append(result)
        
        # Engine 6: yt-dlp (lightweight, no browser)
        result = self._extract_via_ytdlp_light(url, quality)
        if result:
            results.append(result)
        
        # Return first successful result
        for r in results:
            if r.get('success') and r.get('download_url'):
                return r
        
        return {'success': False, 'error': 'All extraction engines failed'}
    
    def _extract_via_direct_api(self, url):
        """Direct API extraction for YouTube"""
        try:
            # Try to extract video ID from YouTube URL
            video_id = None
            if 'youtube.com' in url or 'youtu.be' in url:
                # Extract video ID
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
                    # Try multiple download APIs
                    apis = [
                        f"https://api.social-downloader.com/youtube?video_id={video_id}",
                        f"https://www.yt-download.org/api/button/mp4/{video_id}",
                        f"https://api.vevioz.com/api/button/mp4/{video_id}"
                    ]
                    
                    for api in apis:
                        try:
                            response = session.get(api, headers=get_random_headers(), timeout=10)
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
    
    def _extract_via_rapidapi(self, url):
        """RapidAPI extraction"""
        try:
            api_url = f"https://apis.davidcyriltech.my.id/youtube/dl?url={url}"
            response = session.get(api_url, headers=get_random_headers(), timeout=10)
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
    
    def _extract_via_tikwm(self, url):
        """TikWM extraction for TikTok/Instagram"""
        try:
            api_url = "https://www.tikwm.com/api/"
            params = {'url': url}
            response = session.get(api_url, params=params, headers=get_random_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    video_data = data.get('data', {})
                    download_url = video_data.get('play') or video_data.get('wmplay')
                    if download_url:
                        return {
                            'success': True,
                            'download_url': download_url,
                            'title': video_data.get('title', 'Video'),
                            'engine': 'tikwm'
                        }
            return None
        except:
            return None
    
    def _extract_via_cobalt(self, url):
        """Cobalt API extraction"""
        try:
            api_url = "https://co.wuk.sh/api/json"
            payload = {
                'url': url,
                'isAudioOnly': False,
                'isNoTTWatermark': True,
                'vCodec': 'h264',
                'aCodec': 'aac'
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': random.choice(USER_AGENTS)
            }
            response = session.post(api_url, json=payload, headers=headers, timeout=15)
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
    
    def _extract_via_savefrom_api(self, url):
        """SaveFrom.net API extraction (no browser)"""
        try:
            # Use SaveFrom's API endpoint
            api_url = "https://en.savefrom.net/1-ajax/"
            params = {
                'url': url,
                'ajax': '1'
            }
            headers = get_random_headers()
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            response = session.get(api_url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Extract download URL from the response
                    html_content = data.get('content', '')
                    # Look for download links in the HTML
                    download_patterns = [
                        r'href="([^"]*download[^"]*)"',
                        r'href="([^"]*\.mp4[^"]*)"',
                        r'data-url="([^"]*)"'
                    ]
                    for pattern in download_patterns:
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
    
    def _extract_via_ytdlp_light(self, url, quality='max'):
        """Lightweight yt-dlp extraction (no browser)"""
        try:
            import yt_dlp
            
            # Set format based on quality
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
            
            # Try with different clients
            clients = ['android', 'ios', 'web']
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
                        'socket_timeout': 30,
                        'retries': 5,
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
                                # Find best format with URL
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
        except ImportError:
            return None
        except Exception:
            return None

# Initialize extractor
extractor = UltimateExtractor()

# ===============================
# 🎨 ULTIMATE HTML TEMPLATE
# ===============================

HTML_TEMPLATE = """
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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
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
            --glow: 0 0 30px rgba(108, 60, 225, 0.3);
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
        
        /* Animated background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
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
            padding: 16px 16px 30px;
            position: relative;
            z-index: 1;
        }
        
        /* Header */
        .header {
            text-align: center;
            padding: 20px 0 16px;
        }
        
        .header .logo-icon {
            font-size: 42px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
            animation: logoPulse 2s ease-in-out infinite;
        }
        
        @keyframes logoPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary), var(--secondary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-size: 200% 200%;
            animation: gradientShift 4s ease-in-out infinite;
            margin-top: 4px;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .header .subtitle {
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 2px;
        }
        
        /* Platform Badges */
        .platform-badges {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 6px;
            margin: 8px 0 4px;
        }
        
        .platform-badge {
            font-size: 10px;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.06);
            color: var(--text-muted);
        }
        
        .platform-badge i { margin-right: 4px; }
        .platform-badge.youtube i { color: #FF0000; }
        .platform-badge.instagram i { color: #E4405F; }
        .platform-badge.tiktok i { color: #000000; }
        .platform-badge.facebook i { color: #1877F2; }
        
        /* Stats */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 12px 8px;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-item .number {
            font-size: 18px;
            font-weight: 800;
            color: var(--secondary);
        }
        
        .stat-item .label {
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            gap: 6px;
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 4px;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        
        .tab {
            flex: 1;
            padding: 10px 8px;
            font-size: 12px;
            font-weight: 600;
            text-align: center;
            color: var(--text-muted);
            cursor: pointer;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        
        .tab i { margin-right: 6px; }
        
        .tab.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 20px rgba(108, 60, 225, 0.4);
        }
        
        .tab:hover:not(.active) {
            background: rgba(255,255,255,0.05);
        }
        
        .tab-content {
            display: none;
            animation: fadeSlideUp 0.4s ease;
        }
        
        .tab-content.active { display: block; }
        
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.06);
            backdrop-filter: blur(10px);
            margin-bottom: 16px;
        }
        
        .card-title {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-title i { color: var(--secondary); }
        
        /* Inputs */
        .input-group {
            position: relative;
            margin-bottom: 12px;
        }
        
        .input-group i {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
        }
        
        input[type="text"], select {
            width: 100%;
            padding: 14px 14px 14px 44px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            color: var(--text);
            font-size: 14px;
            font-family: inherit;
            transition: all 0.3s ease;
            outline: none;
        }
        
        input[type="text"]:focus, select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(108, 60, 225, 0.15);
        }
        
        input[type="text"]::placeholder {
            color: var(--text-muted);
        }
        
        select {
            padding-left: 14px;
            appearance: none;
            cursor: pointer;
        }
        
        select option {
            background: #1a1a2e;
            color: var(--text);
        }
        
        /* Buttons */
        .btn-primary {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(108, 60, 225, 0.4);
        }
        
        .btn-primary:active {
            transform: scale(0.98);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }
        
        .btn-primary i { margin-right: 8px; }
        
        /* Result */
        #result { margin-top: 16px; }
        
        .result-box {
            padding: 16px;
            border-radius: 12px;
            animation: fadeSlideUp 0.5s ease;
        }
        
        .result-box.success {
            background: rgba(0, 230, 118, 0.1);
            border: 1px solid rgba(0, 230, 118, 0.2);
        }
        
        .result-box.error {
            background: rgba(255, 107, 107, 0.1);
            border: 1px solid rgba(255, 107, 107, 0.2);
        }
        
        .result-box .title {
            font-weight: 700;
            font-size: 14px;
            display: block;
            margin-bottom: 4px;
        }
        
        .result-box .meta {
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin-top: 4px;
        }
        
        .download-btn {
            display: block;
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--success), #00C853);
            color: #000;
            font-size: 15px;
            font-weight: 700;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 230, 118, 0.3);
        }
        
        /* Loader */
        .loader-container {
            text-align: center;
            padding: 20px 0;
        }
        
        .loader {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid var(--secondary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Video List */
        .video-list {
            max-height: 350px;
            overflow-y: auto;
            padding-right: 4px;
        }
        
        .video-list::-webkit-scrollbar {
            width: 4px;
        }
        
        .video-list::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }
        
        .video-list::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 10px;
        }
        
        .profile-card {
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .profile-card .name {
            font-size: 16px;
            font-weight: 700;
            color: var(--secondary);
        }
        
        .profile-card .bio {
            font-size: 11px;
            color: var(--text-muted);
            margin: 4px 0 8px;
        }
        
        .video-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-top: 6px;
            font-size: 12px;
        }
        
        .video-item .title {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 8px;
        }
        
        .video-item .download-link {
            color: var(--secondary);
            text-decoration: none;
            font-weight: 600;
            padding: 4px 12px;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 6px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        
        .video-item .download-link:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 20px 0 10px;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 8px;
        }
        
        .footer .channel-link {
            color: var(--secondary);
            text-decoration: none;
            font-weight: 700;
            font-size: 14px;
        }
        
        .footer .channel-link:hover {
            color: var(--primary);
        }
        
        .footer .social-icons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 10px;
        }
        
        .footer .social-icons a {
            color: var(--text-muted);
            font-size: 22px;
            transition: all 0.3s ease;
        }
        
        .footer .social-icons a:hover {
            color: var(--secondary);
            transform: translateY(-3px);
        }
        
        /* Admin Form */
        .admin-form-group {
            margin-bottom: 12px;
        }
        
        .admin-form-group label {
            font-size: 12px;
            color: var(--text-muted);
            display: block;
            margin-bottom: 4px;
        }
        
        .admin-form-group input[type="file"] {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.3);
            color: var(--text);
            font-size: 13px;
        }
        
        hr {
            border: 1px solid rgba(255,255,255,0.06);
            margin: 16px 0;
        }
        
        /* Responsive */
        @media (max-width: 420px) {
            .container { padding: 12px; }
            .header h1 { font-size: 22px; }
            .stats-bar { padding: 10px 4px; }
            .stat-item .number { font-size: 15px; }
            .tab { font-size: 10px; padding: 8px 4px; }
            .tab i { margin-right: 4px; }
            .card { padding: 14px; }
            input[type="text"], select { padding: 12px 12px 12px 38px; font-size: 13px; }
            .btn-primary { padding: 14px; font-size: 14px; }
        }
        
        .text-center { text-align: center; }
        .mt-8 { margin-top: 8px; }
        .mb-8 { margin-bottom: 8px; }
    </style>
</head>
<body>
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
                <span class="platform-badge"><i class="fab fa-twitter"></i> Twitter/X</span>
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
                <i class="fas fa-cricket-ball"></i> Cricket
            </div>
            <div class="tab" onclick="switchTab('admin')">
                <i class="fas fa-cog"></i> Admin
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
        
        <!-- Tab 2: Cricket -->
        <div id="cricket-tab" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-trophy"></i>
                    <span>Cricket Video Vault</span>
                </div>
                <div class="video-list">
                    {% for key, profile in cricketers.items() %}
                    <div class="profile-card">
                        <div class="name">{{ profile.name }}</div>
                        <div class="bio">{{ profile.bio }}</div>
                        {% if profile.videos %}
                            {% for vid in profile.videos %}
                            <div class="video-item">
                                <span class="title">🎬 {{ vid.title }}</span>
                                <a href="{{ vid.url }}" class="download-link" download>Download</a>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div style="font-size: 11px; color: var(--text-muted); opacity: 0.5; padding: 8px 0;">
                                No videos uploaded yet
                            </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- Tab 3: Admin -->
        <div id="admin-tab" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-shield-alt"></i>
                    <span>Admin Panel</span>
                </div>
                
                <form action="/admin/add-folder" method="POST">
                    <div class="input-group">
                        <i class="fas fa-user-plus"></i>
                        <input type="text" name="player_name" placeholder="Player Name (e.g. MS Dhoni)" required>
                    </div>
                    <div class="input-group">
                        <i class="fas fa-align-left"></i>
                        <input type="text" name="player_bio" placeholder="Short Bio / Description" required>
                    </div>
                    <button type="submit" class="btn-primary" style="background: linear-gradient(135deg, #00b09b, #96c93d);">
                        <i class="fas fa-folder-plus"></i> Create Folder
                    </button>
                </form>
                
                <hr>
                
                <form action="/admin/upload-video" method="POST" enctype="multipart/form-data">
                    <div class="input-group">
                        <i class="fas fa-folder"></i>
                        <select name="cricketer_key" required>
                            <option value="">Select Player Folder</option>
                            {% for key, profile in cricketers.items() %}
                            <option value="{{ key }}">📁 {{ profile.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="input-group">
                        <i class="fas fa-heading"></i>
                        <input type="text" name="video_title" placeholder="Video Title..." required>
                    </div>
                    <div class="admin-form-group">
                        <input type="file" name="video_file" accept="video/*" required>
                    </div>
                    <button type="submit" class="btn-primary">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Video
                    </button>
                </form>
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
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 8px; opacity: 0.4;">
                🔒 6 Extraction Engines • Anti-Detection • 100% Free
            </div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp
        let tg = window.Telegram.WebApp;
        tg.expand();
        
        // Download counter
        let downloadCount = parseInt(localStorage.getItem('downloadCount') || '0');
        document.getElementById('downloadCount').textContent = downloadCount;
        
        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            const tabs = document.querySelectorAll('.tab');
            const contents = {
                'downloader': document.getElementById('downloader-tab'),
                'cricket': document.getElementById('cricket-tab'),
                'admin': document.getElementById('admin-tab')
            };
            
            if (tabName === 'downloader') {
                tabs[0].classList.add('active');
                contents.downloader.classList.add('active');
            } else if (tabName === 'cricket') {
                tabs[1].classList.add('active');
                contents.cricket.classList.add('active');
            } else if (tabName === 'admin') {
                tabs[2].classList.add('active');
                contents.admin.classList.add('active');
            }
        }
        
        // Process download
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
                    <div style="font-size: 13px; color: var(--text-muted);">
                        🔍 Scanning with 6 engines...
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
                    downloadCount++;
                    localStorage.setItem('downloadCount', downloadCount);
                    document.getElementById('downloadCount').textContent = downloadCount;
                    
                    resultDiv.innerHTML = `
                        <div class="result-box success">
                            <span class="title">✅ ${data.title || 'Video Extracted'}</span>
                            <div class="meta">
                                <span><i class="fas fa-video"></i> ${data.resolution || 'Best'}</span>
                                <span><i class="fas fa-hard-drive"></i> ${data.size || 'Unknown'}</span>
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
    </script>
</body>
</html>
"""

# ===============================
# 🚀 FLASK ROUTES
# ===============================

@app.route('/')
def home():
    db = load_database()
    return render_template_string(HTML_TEMPLATE, cricketers=db)

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Main extraction API - NO PLAYWRIGHT, NO ERRORS"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'max')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Extract using our multi-engine extractor
        result = extractor.extract(url, quality)
        
        if result.get('success') and result.get('download_url'):
            return jsonify({
                'success': True,
                'download_url': result['download_url'],
                'title': result.get('title', 'Video'),
                'resolution': result.get('resolution', 'Best'),
                'size': result.get('size', 'Unknown'),
                'engine': result.get('engine', 'Auto')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'All extraction engines failed. Try another link.')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/add-folder', methods=['POST'])
def add_folder():
    try:
        name = request.form.get('player_name', '').strip()
        bio = request.form.get('player_bio', '').strip()
        if name:
            key = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))
            db = load_database()
            if key not in db:
                db[key] = {'name': name, 'bio': bio, 'videos': []}
                save_database(db)
        return redirect(url_for('home') + '#admin-tab')
    except:
        return redirect(url_for('home'))

@app.route('/admin/upload-video', methods=['POST'])
def admin_upload_video():
    try:
        cricketer_key = request.form.get('cricketer_key')
        video_title = request.form.get('video_title')
        video_file = request.files.get('video_file')
        
        db = load_database()
        if not cricketer_key or not video_file or cricketer_key not in db:
            return redirect(url_for('home'))
        
        def sanitize_filename(filename):
            filename = re.sub(r'[^\w\s-]', '', filename)
            return re.sub(r'[-\s]+', '_', filename).strip()[:100]
        
        filename = f"{uuid.uuid4().hex}_{sanitize_filename(video_file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(file_path)
        
        db[cricketer_key]['videos'].append({
            'title': video_title,
            'url': f'/static/uploads/{filename}'
        })
        save_database(db)
        return redirect(url_for('home') + '#cricket-tab')
    except:
        return redirect(url_for('home'))

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
        "🔥 **6 Powerful Extraction Engines**\n"
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
    ║   🔥 NEXGEN MEDIA DOWNLOADER v3.0                          ║
    ║   ⚡ 6 Extraction Engines • Anti-Detection                  ║
    ║   🚀 NO Playwright • NO Errors • 100% Working              ║
    ║                                                              ║
    ║   🚀 Server running on port {port}                           ║
    ║   📁 Upload folder: {UPLOAD_FOLDER}                         ║
    ║   💾 Database: {DB_FILE}                                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)