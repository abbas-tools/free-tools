from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import re
import requests
from urllib.parse import urlparse
import time
import hashlib
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary directory for downloads
TEMP_DIR = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

@app.route('/process-media', methods=['POST'])
def process_media():
    """
    Process media from any platform and provide download link or file
    """
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON payload'}), 400
        
        video_url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        download_mode = data.get('download_mode', 'direct_link')
        
        if not video_url:
            return jsonify({'success': False, 'message': 'URL is required'}), 400
        
        # Validate URL
        try:
            parsed = urlparse(video_url)
            if not parsed.scheme or not parsed.netloc:
                return jsonify({'success': False, 'message': 'Invalid URL format'}), 400
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid URL format'}), 400
        
        logger.info(f"Processing media: {video_url}")
        
        # Configure yt-dlp options
        ydl_opts = get_ytdl_options(quality)
        
        # Extract video info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
                if not info:
                    return jsonify({'success': False, 'message': 'Could not extract video information'}), 404
                
                # Get available formats
                formats = info.get('formats', [])
                available_qualities = []
                for f in formats:
                    height = f.get('height')
                    if height:
                        available_qualities.append(f"{height}p")
                available_qualities = sorted(set(available_qualities), key=lambda x: int(x.replace('p', '')))
                
                # Extract download URL
                download_url = None
                if 'url' in info:
                    download_url = info['url']
                elif 'formats' in info and info['formats']:
                    # Get the best format based on quality
                    for f in reversed(info['formats']):
                        if f.get('url'):
                            download_url = f['url']
                            break
                
                if not download_url:
                    return jsonify({'success': False, 'message': 'No download URL found'}), 404
                
                # Get video details
                title = info.get('title', 'Media File')
                clean_title = re.sub(r'[^\w\s-]', '', title)
                clean_title = re.sub(r'[-\s]+', '_', clean_title)
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')
                
                # Prepare response
                response_data = {
                    'success': True,
                    'title': title,
                    'download_link': download_url,
                    'duration': duration,
                    'thumbnail': thumbnail,
                    'available_qualities': available_qualities,
                    'quality_selected': quality,
                    'filename': f"{clean_title}.mp4",
                    'file_size': info.get('filesize', 0) or info.get('filesize_approx', 0),
                }
                
                return jsonify(response_data)
                
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                logger.error(f"Download error: {error_msg}")
                
                # Try alternative method for YouTube
                if 'youtube' in video_url or 'youtu.be' in video_url:
                    logger.info("Retrying with alternative YouTube settings...")
                    alt_opts = get_alternative_ytdl_options()
                    try:
                        with yt_dlp.YoutubeDL(alt_opts) as ydl2:
                            info = ydl2.extract_info(video_url, download=False)
                            if info and info.get('url'):
                                return jsonify({
                                    'success': True,
                                    'title': info.get('title', 'Media File'),
                                    'download_link': info['url'],
                                    'download_mode': 'direct_link'
                                })
                    except Exception as retry_error:
                        logger.error(f"Retry failed: {str(retry_error)}")
                        return jsonify({
                            'success': False, 
                            'message': f'Unable to download video. Error: {str(e)[:100]}'
                        }), 500
                
                return jsonify({'success': False, 'message': f'Error: {str(e)[:150]}'}), 500
                
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)[:100]}'}), 500

def get_ytdl_options(quality):
    """Get yt-dlp options WITHOUT any proxy settings"""
    common_headers = {
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
    
    # Base options - NO PROXY
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'http_headers': common_headers,
        'ignoreerrors': True,
        'extract_flat': False,
        'retries': 10,  # More retries
        'fragment_retries': 10,
        'socket_timeout': 30,
        'cookiefile': None,  # Disable cookies
        'proxy': '',  # Explicitly set empty proxy
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls'],
                'player_skip': ['configs'],
                'no_live': ['true'],
            },
            'generic': {
                'no_live': ['true']
            }
        }
    }
    
    # Quality settings
    if quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif quality == 'best':
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    elif quality == 'worst':
        ydl_opts['format'] = 'worst'
    else:
        # Handle quality like '1080p', '720p', etc.
        q_val = quality.replace("p", "")
        if q_val.isdigit():
            ydl_opts['format'] = f'bestvideo[height<={q_val}]+bestaudio/best[height<={q_val}]/best'
        else:
            ydl_opts['format'] = 'best'
    
    return ydl_opts

def get_alternative_ytdl_options():
    """Alternative options for YouTube without proxy"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    return {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'http_headers': headers,
        'proxy': '',  # No proxy
        'ignoreerrors': True,
        'retries': 5,
        'format': 'best',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['hls'],
                'no_live': ['true'],
            }
        }
    }

@app.route('/download-file', methods=['GET'])
def download_file():
    """Download a previously processed file"""
    url = request.args.get('url')
    if not url:
        return jsonify({'success': False, 'message': 'URL is required'}), 400
    
    try:
        # Download and serve the file directly
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'proxy': '',  # No proxy
            'format': 'best',
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
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'temp_directory': TEMP_DIR,
        'temp_files': len(os.listdir(TEMP_DIR)) if os.path.exists(TEMP_DIR) else 0
    })

if __name__ == '__main__':
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)