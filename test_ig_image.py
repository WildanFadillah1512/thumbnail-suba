import sys
import requests
import re

url = sys.argv[1]
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
response = requests.get(url, headers=headers)
print("Status:", response.status_code)
html = response.text
# Try to find og:image
match = re.search(r'<meta property="og:image" content="(.*?)"', html)
if match:
    print("Found image:", match.group(1))
else:
    print("No og:image found")
