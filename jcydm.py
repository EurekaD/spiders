"""
囧次元动漫
https://www.jcydm1.com/index.php/vod/play/id/12834/sid/1/nid/157.html
"""


import requests
from core.headers_config import HEADERS


# STEP 1
url = "https://vip.dytt-cinema.com/20250823/31389_edbd47c8/3000k/hls/mixed.m3u8"

resp = requests.get(
    url,
    headers=HEADERS,
    timeout=10
)

resp.raise_for_status()

with open("mixed.m3u8", "wb") as f:
    f.write(resp.content)

print("m3u8 文件已保存为 mixed.m3u8")


# STEP 2


