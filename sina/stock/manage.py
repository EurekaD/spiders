"""
启动爬虫的脚本，方便调试
"""
from scrapy.cmdline import execute

if __name__ == '__main__':
    execute('scrapy crawl 要闻'.split())
