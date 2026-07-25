import requests

# Fast processing
response = requests.post('https://your-app.railway.app/process-media', json={
    'url': 'https://youtube.com/shorts/_BbraEsZJF8',
    'quality': '480p'
})

data = response.json()
if data['success']:
    print(f"Download: {data['download_link']}")
    print(f"Time: {data['processing_time']}s")