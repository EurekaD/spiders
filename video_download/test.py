import requests


def download_video(url, save_path):
    # 发送 GET 请求下载视频文件
    proxies = {
        'http': "http://127.0.0.1:7890",
        'https': "https://127.0.0.1:7890"
    }
    response = requests.get(url, stream=True, proxies=proxies, verify=False)
    if response.status_code == 200:
        # 打开文件并写入视频数据
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print("视频下载完成")
    else:
        print("视频下载失败")


if __name__ == "__main__":
    # 视频的 URL
    video_url = "https://us-xpc5-l.xpccdn.com/685234d4-b36b-47d5-8ba8-85ca32da051e/4637a349-191e-412b-a793-df52f52ef09b.mp4"
    # 视频保存的路径
    save_path = "video.mp4"
    # 下载视频
    download_video(video_url, save_path)
