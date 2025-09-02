import os
import requests
from core.headers_config import HEADERS
from core.delay import random_delay

M3U8_FILE = "mixed.m3u8"
OUTPUT_DIR = "ts_parts"
OUTPUT_VIDEO = "output.mp4"


# m3u8 基础 URL（你给的完整 ts 链接去掉文件名部分）
BASE_URL = "https://vip.dytt-cinema.com/20250823/31389_edbd47c8/3000k/hls/"

# 读取 m3u8 文件
with open(M3U8_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 提取 ts 链接（过滤掉注释行）
ts_urls = [BASE_URL+line.strip() for line in lines if line and not line.startswith("#")]

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 下载每个 ts 分片
for idx, ts_url in enumerate(ts_urls, start=1):
    ts_path = os.path.join(OUTPUT_DIR, f"{idx}.ts")
    if os.path.exists(ts_path):
        print(f"[跳过] {ts_path} 已存在")
        continue

    print(f"[下载] {idx}/{len(ts_urls)} -> {ts_path}")
    resp = requests.get(ts_url, headers=HEADERS, stream=True, timeout=15)
    resp.raise_for_status()
    random_delay()

    with open(ts_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024*512):  # 512KB
            f.write(chunk)

print("所有 ts 分片下载完成 ✅")

# 生成 ts 文件列表给 ffmpeg 使用
list_file = "ts_list.txt"
with open(list_file, "w", encoding="utf-8") as f:
    for idx in range(1, len(ts_urls)+1):
        f.write(f"file '{os.path.join(OUTPUT_DIR, str(idx) + '.ts')}'\n")

# 用 ffmpeg 合并
print("开始合并视频...")
os.system(f"ffmpeg -f concat -safe 0 -i {list_file} -c copy {OUTPUT_VIDEO}")

print(f"视频已合并完成 -> {OUTPUT_VIDEO}")
