from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import re
import time
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urlparse
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary directory
TEMP_DIR = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Global variables
executor = ThreadPoolExecutor(max_workers=10)
CACHE = {}  # Simple cache for repeated requests
CACHE_TIMEOUT = 300  # 5 minutes

# Detection patterns for platforms
PLATFORM_PATTERNS = {
    'youtube': ['youtube.com', 'youtu.be', 'm.youtube.com'],
    'instagram': ['instagram.com', 'instagr.am'],
    'tiktok': ['tiktok.com', 'vm.tiktok.com'],
    'facebook': ['facebook.com', 'fb.watch', 'fb.com'],
    'twitter': ['twitter.com', 'x.com'],
    'vimeo': ['vimeo.com'],
    'dailymotion': ['dailymotion.com'],
    'twitch': ['twitch.tv'],
    'reddit': ['reddit.com'],
    'soundcloud': ['soundcloud.com'],
}

class MediaExtractor:
    """Fast media extraction with multiple engines"""
    
    @staticmethod
    def get_platform(url):
        """Detect platform from URL"""
        parsed = urlparse(url)
        for platform, domains in PLATFORM_PATTERNS.items():
            for domain in domains:
                if domain in parsed.netloc:
                    return platform
        return 'generic'
    
    @staticmethod
    def get_headers(platform='generic'):
        """Get optimized headers for platform"""
        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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
        
        # Platform-specific headers
        if platform == 'youtube':
            base_headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            })
        elif platform == 'instagram':
            base_headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            })
        elif platform == 'tiktok':
            base_headers.update({
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36',
            })
        
        return base_headers
    
    @staticmethod
    def extract_fast(url, quality='best'):
        """Fast extraction with optimized settings"""
        platform = MediaExtractor.get_platform(url)
        headers = MediaExtractor.get_headers(platform)
        
        # Different configs for different platforms
        extractor_args = {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls'],
                'player_skip': ['configs'],
                'no_live': ['true'],
            },
            'instagram': {
                'skip_login': ['true'],
            },
            'tiktok': {
                'skip_login': ['true'],
                'app_version': ['29.3.5'],
            },
            'facebook': {
                'skip_download': ['true'],
            },
            'twitter': {
                'skip_download': ['true'],
            }
        }
        
        # Base options - SUPER FAST
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'http_headers': headers,
            'ignoreerrors': True,
            'extract_flat': False,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 10,
            'proxy': '',
            'cookiefile': None,
            'extractor_args': extractor_args.get(platform, {}),
            # Speed optimizations
            'concurrent_fragment_downloads': 5,
            'throttledratelimit': 0,
            'buffersize': 1024 * 1024,  # 1MB buffer
        }
        
        # Quality settings
        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
        elif quality == 'best':
            ydl_opts['format'] = 'best'
        elif quality == 'worst':
            ydl_opts['format'] = 'worst'
        elif quality.endswith('p'):
            height = quality.replace('p', '')
            if height.isdigit():
                ydl_opts['format'] = f'best[height<={height}]/best'
        
        return ydl_opts

class MultiEngineExtractor:
    """Multiple extraction engines for reliability"""
    
    @staticmethod
    def engine_1(url, quality):
        """Engine 1: Standard yt-dlp"""
        try:
            opts = MediaExtractor.extract_fast(url, quality)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    return info
            return None
        except Exception as e:
            logger.error(f"Engine 1 failed: {str(e)}")
            return None
    
    @staticmethod
    def engine_2(url, quality):
        """Engine 2: Alternative YouTube client"""
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'proxy': '',
                'format': 'best',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android'],
                        'skip': ['hls'],
                    }
                }
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    return info
            return None
        except Exception as e:
            logger.error(f"Engine 2 failed: {str(e)}")
            return None
    
    @staticmethod
    def engine_3(url, quality):
        """Engine 3: Mobile user agent"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            }
            opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'proxy': '',
                'http_headers': headers,
                'format': 'best',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                        'skip': ['dash'],
                    }
                }
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    return info
            return None
        except Exception as e:
            logger.error(f"Engine 3 failed: {str(e)}")
            return None
    
    @staticmethod
    def engine_4(url, quality):
        """Engine 4: Direct URL extraction"""
        try:
            # Try to get direct video URL from page source
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                # Look for video URLs in page source
                video_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|webm|mov|avi|mkv)[^\s"\'<>]*', response.text)
                if video_urls:
                    return {
                        'url': video_urls[0],
                        'title': 'Video from page',
                        'extractor': 'direct'
                    }
            return None
        except Exception as e:
            logger.error(f"Engine 4 failed: {str(e)}")
            return None
    
    @staticmethod
    def engine_5(url, quality):
        """Engine 5: Alternative extractor with cookie support"""
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'proxy': '',
                'format': 'best',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls'],
                        'player_skip': ['configs', 'webpage'],
                    }
                }
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    return info
            return None
        except Exception as e:
            logger.error(f"Engine 5 failed: {str(e)}")
            return None
    
    @staticmethod
    def extract_with_all_engines(url, quality):
        """Try all engines in parallel"""
        engines = [
            MultiEngineExtractor.engine_1,
            MultiEngineExtractor.engine_2,
            MultiEngineExtractor.engine_3,
            MultiEngineExtractor.engine_5,  # Skip engine 4 as it's slower
        ]
        
        # Try all engines in parallel with timeout
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(engine, url, quality): engine.__name__ for engine in engines}
            
            for future in as_completed(futures, timeout=15):
                try:
                    result = future.result(timeout=5)
                    if result and result.get('url'):
                        logger.info(f"Success with {futures[future]}")
                        return result
                except Exception as e:
                    logger.error(f"Engine {futures[future]} error: {str(e)}")
                    continue
        
        return None

@app.route('/process-media', methods=['POST'])
def process_media():
    """Super fast media processing with multi-engine approach"""
    try:
        start_time = time.time()
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON payload'}), 400
        
        video_url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        
        if not video_url:
            return jsonify({'success': False, 'message': 'URL is required'}), 400
        
        # Check cache first
        cache_key = f"{video_url}_{quality}"
        if cache_key in CACHE:
            cache_time, cached_data = CACHE[cache_key]
            if time.time() - cache_time < CACHE_TIMEOUT:
                logger.info("Returning cached result")
                return jsonify(cached_data)
        
        # Detect platform
        platform = MediaExtractor.get_platform(video_url)
        logger.info(f"Processing {platform} video: {video_url}")
        
        # Extract using multi-engine approach
        info = MultiEngineExtractor.extract_with_all_engines(video_url, quality)
        
        if not info:
            return jsonify({
                'success': False, 
                'message': 'All extraction engines failed. Please try again.'
            }), 500
        
        # Extract video details
        download_url = info.get('url')
        if not download_url:
            # Try to get from formats
            formats = info.get('formats', [])
            if formats:
                # Get the best format
                for f in reversed(formats):
                    if f.get('url'):
                        download_url = f['url']
                        break
        
        if not download_url:
            return jsonify({'success': False, 'message': 'Could not extract download URL'}), 404
        
        # Get title and other info
        title = info.get('title', 'Media File')
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'[-\s]+', '_', clean_title)
        
        # Get available qualities
        available_qualities = []
        if info.get('formats'):
            for f in info['formats']:
                if f.get('height'):
                    height = f['height']
                    if height:
                        available_qualities.append(f"{height}p")
            available_qualities = sorted(set(available_qualities), key=lambda x: int(x.replace('p', '')))
        
        # Prepare response
        response_data = {
            'success': True,
            'title': title,
            'download_link': download_url,
            'platform': platform,
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', ''),
            'available_qualities': available_qualities[:10],  # Limit to 10
            'quality_selected': quality,
            'filename': f"{clean_title}.mp4",
            'file_size': info.get('filesize', 0) or info.get('filesize_approx', 0),
            'processing_time': round(time.time() - start_time, 2)
        }
        
        # Cache the result
        CACHE[cache_key] = (time.time(), response_data)
        
        logger.info(f"Successfully extracted in {response_data['processing_time']}s")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing media: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)[:100]}'}), 500

@app.route('/download', methods=['GET'])
def download_file():
    """Download media file directly"""
    try:
        url = request.args.get('url')
        quality = request.args.get('quality', 'best')
        
        if not url:
            return jsonify({'success': False, 'message': 'URL is required'}), 400
        
        # Optimized download options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'proxy': '',
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'retries': 3,
            'socket_timeout': 30,
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
        'temp_files': len(os.listdir(TEMP_DIR)) if os.path.exists(TEMP_DIR) else 0,
        'cache_size': len(CACHE)
    })

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear cache"""
    CACHE.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'})

if __name__ == '__main__':
    os.makedirs(TEMP_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)