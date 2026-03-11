import yt_dlp
import sys
import tempfile
import os

url = sys.argv[1]

temp_dir = tempfile.mkdtemp()
output_path = os.path.join(temp_dir, "video.%(ext)s")

ydl_opts = {
    'format': 'best[ext=mp4]/best',
    'outtmpl': output_path,
    'quiet': False,
    'no_warnings': False,
    'socket_timeout': 30,
    'retries': 3,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

try:
    print(f"Downloading from {url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', '')
        print("Success:", title)
except Exception as e:
    print("Error occurred:", e)
