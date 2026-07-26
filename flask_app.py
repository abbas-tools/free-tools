from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import re
import time
import logging
import json
from urllib.parse import urlparse

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temp directory
TEMP_DIR = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Simple cache
CACHE = {}
CACHE_TIMEOUT = 300

# Clean headers - NO PROXY
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
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

@app.route('/process-media', methods=['POST'])
def process_media():
    """Process media with robust error handling"""
    try:
        # Parse JSON with error handling
        try:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({
                    'success': False, 
                    'message': 'Invalid JSON. Please send valid JSON data.'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'JSON parsing error: {str(e)}'
            }), 400
        
        # Get URL
        video_url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        
        if not video_url:
            return jsonify({
                'success': False, 
                'message': 'URL is required'
            }), 400
        
        # Validate URL
        if not video_url.startswith(('http://', 'https://')):
            return jsonify({
                'success': False, 
                'message': 'Invalid URL. Please include http:// or https://'
            }), 400
        
        logger.info(f"Processing: {video_url}")
        
        # Check cache
        cache_key = f"{video_url}_{quality}"
        if cache_key in CACHE:
            cache_time, cached_data = CACHE[cache_key]
            if time.time() - cache_time < CACHE_TIMEOUT:
                logger.info("Returning cached result")
                return jsonify(cached_data)
        
        # Extract video
        result = extract_video(video_url, quality)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Failed to extract video. Please try with a different quality or URL.'
            }), 500
        
        # Cache result
        CACHE[cache_key] = (time.time(), result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)[:100]}'
        }), 500

def extract_video(url, quality):
    """Extract video using yt-dlp with multiple fallbacks"""
    
    # Different configurations to try
    configs = [
        # Config 1: Standard
        {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'proxy': '',
            'format': get_format_quality(quality),
            'http_headers': get_headers(),
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['dash', 'hls'],
                }
            }
        },
        # Config 2: Mobile only
        {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'proxy': '',
            'format': get_format_quality(quality),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android'],
                }
            }
        },
        # Config 3: Simple
        {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'proxy': '',
            'format': 'best',
            'http_headers': get_headers(),
        }
    ]
    
    for i, config in enumerate(configs, 1):
        try:
            logger.info(f"Trying config {i}...")
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    # Get download URL
                    download_url = None
                    
                    # Try direct URL first
                    if info.get('url'):
                        download_url = info['url']
                    elif info.get('formats'):
                        # Find best format
                        for f in reversed(info['formats']):
                            if f.get('url') and f.get('height'):
                                download_url = f['url']
                                break
                        if not download_url and info['formats']:
                            download_url = info['formats'][-1].get('url')
                    
                    if download_url:
                        # Prepare response
                        title = info.get('title', 'Media')
                        clean_title = re.sub(r'[^\w\s-]', '', title)
                        clean_title = re.sub(r'[-\s]+', '_', clean_title)
                        
                        # Get available qualities
                        qualities = []
                        if info.get('formats'):
                            for f in info['formats']:
                                if f.get('height'):
                                    qualities.append(f"{f['height']}p")
                            qualities = sorted(set(qualities), key=lambda x: int(x.replace('p', '')))
                        
                        return {
                            'success': True,
                            'title': title,
                            'download_link': download_url,
                            'platform': detect_platform(url),
                            'duration': info.get('duration', 0),
                            'thumbnail': info.get('thumbnail', ''),
                            'available_qualities': qualities[:10],
                            'quality_selected': quality,
                            'filename': f"{clean_title}.mp4",
                            'file_size': info.get('filesize', 0) or info.get('filesize_approx', 0)
                        }
        except Exception as e:
            logger.warning(f"Config {i} failed: {str(e)[:50]}")
            continue
    
    return None

def get_format_quality(quality):
    """Get format string for quality"""
    if quality == 'audio':
        return 'bestaudio/best'
    elif quality == 'best':
        return 'best'
    elif quality == 'worst':
        return 'worst'
    elif quality.endswith('p'):
        height = quality.replace('p', '')
        if height.isdigit():
            return f'best[height<={height}]/best'
    return 'best'

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

@app.route('/download', methods=['GET'])
def download():
    """Download media file directly"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'success': False, 'message': 'URL required'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'proxy': '',
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=os.path.basename(filename)
                )
            else:
                return jsonify({'success': False, 'message': 'File not found'}), 404
                
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)[:100]}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'temp_files': len(os.listdir(TEMP_DIR)),
        'cache_size': len(CACHE)
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    os.makedirs(TEMP_DIR, exist_ok=True)
    # Use port 5000 for local, Railway will override
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)