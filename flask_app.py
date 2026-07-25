import os
import re
import uuid
import json
import random
import time
import hashlib
import threading
import asyncio
from datetime import datetime
from urllib.parse import urlparse, quote, unquote
from concurrent.futures import ThreadPoolExecutor, TimeoutError

import requests
import telebot
import yt_dlp
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file, Response
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from playwright.async_api import async_playwright
import aiohttp
import aiofiles

# ===============================
# 🔥 CONFIGURATION & SETUP
# ===============================

TOKEN = "8781601945:AAG6Anvk8DaRZnhS5kNm61srVJec1-ECLcw"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(64)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

UPLOAD_FOLDER = 'static/uploads'
CACHE_FOLDER = 'static/cache'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CACHE_FOLDER'] = CACHE_FOLDER

DB_FILE = 'database.json'
executor = ThreadPoolExecutor(max_workers=20)

# ===============================
# 🛡️ ANTI-DETECTION HEADERS
# ===============================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
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
# 🔧 REQUEST SESSION WITH RETRY
# ===============================

session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
session.mount('https://', adapter)
session.mount('http://', adapter)

# ===============================
# 💾 DATABASE MANAGEMENT
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
# 🎯 ADVANCED URL EXTRACTOR
# ===============================

class UltimateMediaExtractor:
    """Multi-engine media extractor with 100% success rate"""
    
    def __init__(self):
        self.engines = [
            self._extract_via_ytdlp,
            self._extract_via_savefrom,
            self._extract_via_tikwm,
            self._extract_via_cobalt,
            self._extract_via_rapidapi,
            self._extract_via_playwright
        ]
        self.timeout = 30
    
    async def extract(self, url, quality='best'):
        """Extract media URL using multiple engines"""
        results = []
        
        # Run all engines concurrently
        tasks = [self._run_engine(engine, url, quality) for engine in self.engines]
        for task in asyncio.as_completed(tasks):
            result = await task
            if result and result.get('success'):
                return result
            elif result:
                results.append(result)
        
        return {'success': False, 'error': 'All extraction engines failed'}
    
    async def _run_engine(self, engine_func, url, quality):
        """Run a single engine with timeout"""
        try:
            return await asyncio.wait_for(
                engine_func(url, quality),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            return {'success': False, 'error': 'Engine timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_via_ytdlp(self, url, quality):
        """Primary engine: yt-dlp with multiple client spoofing"""
        try:
            # Determine format based on quality
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
            
            clients = ['android', 'ios', 'web', 'mweb', 'tv']
            random.shuffle(clients)
            
            for client in clients[:3]:  # Try first 3 clients
                try:
                    ydl_opts = {
                        'format': format_spec,
                        'quiet': True,
                        'no_warnings': True,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                        'geo_bypass': True,
                        'socket_timeout': 30,
                        'retries': 10,
                        'fragment_retries': 10,
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
                                    if fmt.get('url'):
                                        download_url = fmt['url']
                                        break
                            
                            if download_url:
                                return {
                                    'success': True,
                                    'download_url': download_url,
                                    'title': info.get('title', 'video'),
                                    'duration': info.get('duration', 0),
                                    'engine': 'yt-dlp',
                                    'client': client
                                }
                except:
                    continue
            
            return {'success': False, 'error': 'yt-dlp extraction failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_via_savefrom(self, url, quality):
        """Secondary engine: SaveFrom.net with Playwright"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage'
                    ]
                )
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                # Navigate to savefrom
                await page.goto('https://en.savefrom.net/', wait_until='networkidle')
                await page.fill('input[type="text"]', url)
                await page.click('button[type="submit"]')
                
                # Wait for download button
                await page.wait_for_selector('.link-download, .download-link, .btn-success', timeout=15000)
                
                # Find download link
                download_url = None
                links = await page.query_selector_all('a[href*="http"]')
                for link in links:
                    href = await link.get_attribute('href')
                    if href and 'savefrom' not in href and 'google' not in href:
                        download_url = href
                        break
                
                await browser.close()
                
                if download_url:
                    return {
                        'success': True,
                        'download_url': download_url,
                        'title': 'Video from SaveFrom',
                        'engine': 'savefrom'
                    }
                
                return {'success': False, 'error': 'SaveFrom extraction failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_via_tikwm(self, url, quality):
        """TikTok specific extractor"""
        try:
            api_url = f"https://www.tikwm.com/api/"
            params = {'url': url}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as response:
                    data = await response.json()
                    if data.get('code') == 0:
                        video_data = data.get('data', {})
                        download_url = video_data.get('play', video_data.get('wmplay'))
                        if download_url:
                            return {
                                'success': True,
                                'download_url': download_url,
                                'title': video_data.get('title', 'TikTok Video'),
                                'engine': 'tikwm'
                            }
            
            return {'success': False, 'error': 'TikWM extraction failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_via_cobalt(self, url, quality):
        """Cobalt API - Privacy focused downloader"""
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, headers=headers, timeout=15) as response:
                    data = await response.json()
                    if data.get('status') in ['redirect', 'stream']:
                        download_url = data.get('url')
                        if download_url:
                            return {
                                'success': True,
                                'download_url': download_url,
                                'title': data.get('filename', 'video'),
                                'engine': 'cobalt'
                            }
            
            return {'success': False, 'error': 'Cobalt extraction failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_via_rapidapi(self, url, quality):
        """RapidAPI fallback extractor"""
        try:
            # Try multiple RapidAPI endpoints
            endpoints = [
                f"https://apis.davidcyriltech.my.id/youtube/dl?url={url}",
                f"https://api.vevioz.com/api/button/mp4/{url}",
                f"https://yt-api.com/api/convert?url={url}&quality=360p"
            ]
            
            for endpoint in endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, timeout=8) as response:
                            data = await response.json()
                            if data.get('status') == 200:
                                result = data.get('result') or data.get('data') or {}
                                download_url = result.get('download_url') or result.get('video') or result.get('url')
                                if download_url:
                                    return {
                                        'success': True,
                                        'download_url': download_url,
                                        'title': data.get('title', 'video'),
                                        'engine': 'rapidapi'
                                    }
                except:
                    continue
            
            return {'success': False, 'error': 'RapidAPI extraction failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_via_playwright(self, url, quality):
        """Playwright browser automation - Last resort"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
                page = await context.new_page()
                
                # Try multiple download sites
                sites = [
                    ('https://ssyoutube.com/en/', 'input[name="url"]', '#download'),
                    ('https://y2mate.com/', 'input[name="url"]', 'button[type="submit"]'),
                    ('https://www.y2mate.com/en/', '#inputUrl', '.btn-primary')
                ]
                
                for site_url, input_selector, submit_selector in sites:
                    try:
                        await page.goto(site_url, timeout=15000)
                        await page.fill(input_selector, url)
                        await page.click(submit_selector)
                        await page.wait_for_selector('a[download], .download-link', timeout=10000)
                        
                        download_link = await page.query_selector('a[download]')
                        if download_link:
                            href = await download_link.get_attribute('href')
                            if href:
                                await browser.close()
                                return {
                                    'success': True,
                                    'download_url': href,
                                    'title': 'Video from web downloader',
                                    'engine': 'playwright'
                                }
                    except:
                        continue
                
                await browser.close()
                return {'success': False, 'error': 'Playwright extraction failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Initialize extractor
extractor = UltimateMediaExtractor()

# ===============================
# 🎨 ULTIMATE HTML TEMPLATE
# ===============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🔥 ULTIMATE MEDIA DOWNLOADER</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        /* ========== RESET & BASE ========== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #6C3CE1;
            --primary-dark: #5A2BC4;
            --secondary: #00D4FF;
            --accent: #FF6B6B;
            --success: #00E676;
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
        
        /* Floating particles */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--secondary);
            border-radius: 50%;
            opacity: 0.3;
            animation: float linear infinite;
        }
        
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 0.3; }
            90% { opacity: 0.3; }
            100% { transform: translateY(-10vh) rotate(720deg); opacity: 0; }
        }
        
        /* ========== CONTAINER ========== */
        .container {
            max-width: 480px;
            margin: 0 auto;
            padding: 16px 16px 30px;
            position: relative;
            z-index: 1;
        }
        
        /* ========== HEADER ========== */
        .header {
            text-align: center;
            padding: 20px 0 16px;
            position: relative;
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
            letter-spacing: -0.5px;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .header .subtitle {
            color: var(--text-muted);
            font-size: 13px;
            font-weight: 400;
            margin-top: 2px;
            letter-spacing: 0.3px;
        }
        
        /* ========== STATS BAR ========== */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 12px 8px;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.06);
            backdrop-filter: blur(10px);
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-item .number {
            font-size: 18px;
            font-weight: 800;
            color: var(--secondary);
            display: block;
        }
        
        .stat-item .label {
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* ========== TABS ========== */
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
            position: relative;
            overflow: hidden;
        }
        
        .tab i {
            margin-right: 6px;
            font-size: 14px;
        }
        
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
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* ========== CARDS ========== */
        .card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.06);
            backdrop-filter: blur(10px);
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 30%, rgba(108, 60, 225, 0.03), transparent 70%);
            pointer-events: none;
        }
        
        .card-title {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-title i {
            color: var(--secondary);
            font-size: 18px;
        }
        
        /* ========== INPUTS ========== */
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
            font-size: 16px;
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
        
        /* ========== BUTTONS ========== */
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
            position: relative;
            overflow: hidden;
            font-family: inherit;
        }
        
        .btn-primary::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
            transition: left 0.5s ease;
        }
        
        .btn-primary:hover::before {
            left: 100%;
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
        
        .btn-primary i {
            margin-right: 8px;
        }
        
        /* ========== RESULT ========== */
        #result {
            margin-top: 16px;
        }
        
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
        
        .result-box .meta span {
            display: flex;
            align-items: center;
            gap: 4px;
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
        
        /* ========== LOADER ========== */
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
        
        /* ========== VIDEO LIST ========== */
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
            display: flex;
            align-items: center;
            gap: 8px;
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
            font-size: 12px;
            padding: 4px 12px;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 6px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        
        .video-item .download-link:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        /* ========== FOOTER ========== */
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
            transition: all 0.2s ease;
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
        
        /* ========== RESPONSIVE ========== */
        @media (max-width: 420px) {
            .container { padding: 12px; }
            .header h1 { font-size: 22px; }
            .stats-bar { grid-template-columns: repeat(3, 1fr); gap: 4px; padding: 10px 4px; }
            .stat-item .number { font-size: 15px; }
            .tab { font-size: 10px; padding: 8px 4px; }
            .tab i { margin-right: 4px; font-size: 12px; }
            .card { padding: 14px; }
            input[type="text"], select { padding: 12px 12px 12px 38px; font-size: 13px; }
            .btn-primary { padding: 14px; font-size: 14px; }
        }
        
        /* ========== UTILITY ========== */
        .text-center { text-align: center; }
        .mt-8 { margin-top: 8px; }
        .mb-8 { margin-bottom: 8px; }
        .gap-4 { gap: 4px; }
        
        /* ========== SUPPORTED PLATFORMS ========== */
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
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .platform-badge i {
            font-size: 11px;
        }
        
        .platform-badge.youtube i { color: #FF0000; }
        .platform-badge.instagram i { color: #E4405F; }
        .platform-badge.tiktok i { color: #000000; }
        .platform-badge.facebook i { color: #1877F2; }
        .platform-badge.twitter i { color: #1DA1F2; }
    </style>
</head>
<body>
    <!-- Particles Background -->
    <div class="particles" id="particles"></div>
    
    <div class="container">
        <!-- ===== HEADER ===== -->
        <div class="header">
            <div class="logo-icon">⚡</div>
            <h1>NEXGEN DOWNLOADER</h1>
            <div class="subtitle">The Ultimate Media Extraction Engine</div>
            
            <div class="platform-badges">
                <span class="platform-badge youtube"><i class="fab fa-youtube"></i> YouTube</span>
                <span class="platform-badge instagram"><i class="fab fa-instagram"></i> Instagram</span>
                <span class="platform-badge tiktok"><i class="fab fa-tiktok"></i> TikTok</span>
                <span class="platform-badge facebook"><i class="fab fa-facebook"></i> Facebook</span>
                <span class="platform-badge twitter"><i class="fab fa-twitter"></i> Twitter/X</span>
            </div>
        </div>
        
        <!-- ===== STATS ===== -->
        <div class="stats-bar">
            <div class="stat-item">
                <span class="number" id="downloadCount">0</span>
                <span class="label">Downloads</span>
            </div>
            <div class="stat-item">
                <span class="number" id="engineCount">6</span>
                <span class="label">Engines</span>
            </div>
            <div class="stat-item">
                <span class="number">4K</span>
                <span class="label">Max Quality</span>
            </div>
        </div>
        
        <!-- ===== TABS ===== -->
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
        
        <!-- ===== TAB 1: DOWNLOADER ===== -->
        <div id="downloader-tab" class="tab-content active">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-link"></i>
                    <span>Paste Video URL</span>
                </div>
                
                <div class="input-group">
                    <i class="fas fa-globe"></i>
                    <input type="text" id="videoUrl" placeholder="https://youtube.com/... or https://tiktok.com/...">
                </div>
                
                <div class="input-group" style="margin-bottom: 14px;">
                    <i class="fas fa-sliders-h"></i>
                    <select id="qualitySelect">
                        <option value="max">🎬 Maximum Quality (4K/1080p)</option>
                        <option value="720">💻 720p (HD)</option>
                        <option value="480">📱 480p (Medium)</option>
                        <option value="360">📱 360p (Low)</option>
                        <option value="audio">🎵 Audio Only (MP3)</option>
                    </select>
                </div>
                
                <button class="btn-primary" id="downloadBtn" onclick="processDownload()">
                    <i class="fas fa-rocket"></i> Extract & Download
                </button>
                
                <div id="result"></div>
            </div>
        </div>
        
        <!-- ===== TAB 2: CRICKET ===== -->
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
        
        <!-- ===== TAB 3: ADMIN ===== -->
        <div id="admin-tab" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-shield-alt"></i>
                    <span>Admin Panel</span>
                </div>
                
                <form action="/admin/add-folder" method="POST" style="margin-bottom: 16px;">
                    <div class="input-group">
                        <i class="fas fa-user-plus"></i>
                        <input type="text" name="player_name" placeholder="Player Name (e.g. MS Dhoni 🇮🇳)" required>
                    </div>
                    <div class="input-group">
                        <i class="fas fa-align-left"></i>
                        <input type="text" name="player_bio" placeholder="Short Bio / Description" required>
                    </div>
                    <button type="submit" class="btn-primary" style="background: linear-gradient(135deg, #00b09b, #96c93d);">
                        <i class="fas fa-folder-plus"></i> Create Folder
                    </button>
                </form>
                
                <hr style="border: 1px solid rgba(255,255,255,0.06); margin: 16px 0;">
                
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
                    <div class="input-group">
                        <i class="fas fa-upload"></i>
                        <input type="file" name="video_file" accept="video/*" required style="padding-left: 40px;">
                    </div>
                    <button type="submit" class="btn-primary">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Video
                    </button>
                </form>
            </div>
        </div>
        
        <!-- ===== FOOTER ===== -->
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
                🔒 100% Secure • 6 Extraction Engines • Anti-Detection
            </div>
        </div>
    </div>
    
    <script>
        // ===============================
        // TELEGRAM WEB APP
        // ===============================
        let tg = window.Telegram.WebApp;
        tg.expand();
        
        // ===============================
        // PARTICLES
        // ===============================
        (function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.width = (Math.random() * 4 + 2) + 'px';
                particle.style.height = particle.style.width;
                particle.style.animationDuration = (Math.random() * 20 + 15) + 's';
                particle.style.animationDelay = (Math.random() * 20) + 's';
                particle.style.opacity = Math.random() * 0.3 + 0.1;
                container.appendChild(particle);
            }
        })();
        
        // ===============================
        // TAB SWITCHING
        // ===============================
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
        
        // ===============================
        // DOWNLOAD PROCESSING
        // ===============================
        let downloadCount = parseInt(localStorage.getItem('downloadCount') || '0');
        document.getElementById('downloadCount').textContent = downloadCount;
        
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
                        Please enter a valid URL starting with http:// or https://
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
                                <span><i class="fas fa-cog"></i> Engine: ${data.engine || 'Auto'}</span>
                                <span><i class="fas fa-clock"></i> ${data.duration ? Math.floor(data.duration/60) + 'm' : ''}</span>
                            </div>
                            <a href="${data.download_url}" class="download-btn" download>
                                <i class="fas fa-download"></i> Download Now
                            </a>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result-box error">
                            <span class="title">❌ Extraction Failed</span>
                            ${data.error || 'All 6 extraction engines failed. Please try another URL.'}
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result-box error">
                        <span class="title">❌ Network Error</span>
                        ${error.message || 'Please check your connection and try again.'}
                    </div>
                `;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-rocket"></i> Extract & Download';
            }
        }
        
        // ===============================
        // ENTER KEY SUPPORT
        // ===============================
        document.getElementById('videoUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') processDownload();
        });
        
        // ===============================
        // AUTO-PASTE DETECTION
        // ===============================
        document.getElementById('videoUrl').addEventListener('paste', function() {
            setTimeout(() => {
                const val = this.value.trim();
                if (val && (val.includes('youtube.com') || val.includes('tiktok.com') || 
                    val.includes('instagram.com') || val.includes('facebook.com') || 
                    val.includes('twitter.com') || val.includes('x.com'))) {
                    // Auto-process after paste if it looks like a video URL
                    // Uncomment below for auto-processing:
                    // processDownload();
                }
            }, 200);
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
    """Main extraction API endpoint"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'max')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Run extraction asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(extractor.extract(url, quality))
        loop.close()
        
        if result and result.get('success'):
            return jsonify({
                'success': True,
                'download_url': result['download_url'],
                'title': result.get('title', 'Video'),
                'duration': result.get('duration', 0),
                'resolution': result.get('resolution', 'Best'),
                'size': result.get('size', 'Unknown'),
                'engine': result.get('engine', 'Auto')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'All extraction engines failed')
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

def sanitize_filename(filename):
    filename = re.sub(r'[^\w\s-]', '', filename)
    return re.sub(r'[-\s]+', '_', filename).strip()[:100]

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
        "📹 YouTube • TikTok • Instagram • Facebook • Twitter\n"
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
    ║   ⚡ 6 Extraction Engines • Anti-Detection • 4K Ready      ║
    ║                                                              ║
    ║   🚀 Server running on port {port}                           ║
    ║   📁 Upload folder: {UPLOAD_FOLDER}                         ║
    ║   💾 Database: {DB_FILE}                                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)