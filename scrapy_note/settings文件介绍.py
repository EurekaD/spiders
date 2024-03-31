"""
BOT_NAME
默认: ‘scrapybot’
项目名称，当您使用 startproject 命令创建项目时其也被自动赋值。

SPIDER_MODULES
Python爬虫储存的文件路径

NEWSPIDER_MODULE
创建爬虫文件的模板,创建好的爬虫文件会存放在这个目录下

ROBOTSTXT_OBEY
设置是否需要遵循robot协议:默认为True
通俗来说， robots.txt 是遵循 Robot协议 的一个文件，它保存在网站的服务器中，它的作用是，告诉搜索引擎爬虫，
本网站哪些目录下的网页 不希望 你进行爬取收录。在Scrapy启动后，会在第一时间访问网站的 robots.txt 文件，然后决定该网站的爬取范围。
当然，我们并不是在做搜索引擎，而且在某些情况下我们想要获取的内容恰恰是被 robots.txt 所禁止访问的。
所以，某些时候，我们就要将此配置项设置为 False ，拒绝遵守 Robot协议

CONCURRENT_ITEMS
默认: 100
Item Processor(即 Item Pipeline) 同时处理(每个response的)item的最大值。

CONCURRENT_REQUESTS
默认: 16
Scrapy downloader 并发请求(concurrent requests)的最大值。

DEFAULT_REQUEST_HEADERS
默认: 如下
{
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}
Scrapy HTTP Request使用的默认header。

DEPTH_LIMIT
默认: 0
爬取网站最大允许的深度(depth)值。如果为0，则没有限制。

DOWNLOAD_DELAY
默认: 0
下载器在下载同一个网站下一个页面前需要等待的时间。该选项可以用来限制爬取速度， 减轻服务器压力。同时也支持小数:
DOWNLOAD_DELAY = 0.25 # 250 ms of delay
默认情况下，Scrapy在两个请求间不等待一个固定的值， 而是使用0.5到1.5之间的一个随机值 DOWNLOAD_DELAY 的结果作为等待间隔。

CONCURRENT_REQUESTS_PER_DOMAIN
设置网站的最大并发请求数量,默认是8

CONCURRENT_REQUESTS_PER_IP
设置某个ip的最大并发请求数量,默认是0,如果非 0 ,CONCURRENT_REQUESTS_PER_DOMAIN不生效,
这时的请求并发数量针对于ip,而不是网站,DOWNLOAD_DELAY针对ip而不是网站。

DOWNLOAD_TIMEOUT
默认: 180
下载器超时时间(单位: 秒)。

ITEM_PIPELINES
默认: {}
保存项目中启用的pipeline及其顺序的字典。该字典默认为空，值(value)任意，不过值(value)习惯设置在0-1000范围内，值越小优先级越高。

设置日志
LOG_ENABLED
默认: True    是否启用logging。

LOG_ENCODING
默认: ‘utf-8’ logging使用的编码。

LOG_LEVEL
默认: ‘DEBUG’ log的最低级别。可选的级别有: CRITICAL、ERROR、WARNING、INFO、DEBUG

LOG_FILE
默认: None    logging输出的文件名。如果为None，则使用标准错误输出(standard error)

USER_AGENT
默认: “Scrapy/VERSION (+http://scrapy.org)”
爬取的默认User-Agent，除非被覆盖。

PROXIES
代理设置
   PROXIES = [
      {'ip_port': '111.11.228.75:80', 'password': ''},
      {'ip_port': '120.198.243.22:80', 'password': ''},
      {'ip_port': '111.8.60.9:8123', 'password': ''},
      {'ip_port': '101.71.27.120:80', 'password': ''},
      {'ip_port': '122.96.59.104:80', 'password': ''},
      {'ip_port': '122.224.249.122:8088', 'password':''},
    ]

COOKIES_ENABLED
是否携带 cookkie，默认 “true”

COOKIES_DEBUG
跟踪cookies,默认情况为False


"""