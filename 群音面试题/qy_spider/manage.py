"""
启动爬虫的脚本，方便调试
"""
from scrapy.cmdline import execute

if __name__ == '__main__':
    execute('scrapy crawl 电影信息'.split())
    # execute('scrapy crawl 视频信息'.split())
