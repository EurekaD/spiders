import json
from copy import deepcopy
from typing import Iterable, Any
from urllib.request import Request

import scrapy
from scrapy.http import Response
from 群音面试题.qy_spider.qy_spider.items import QySpider1Item


class VideoInfo(scrapy.Spider):
    name = '视频信息'
    allowed_domains = ["www.xinpianchang.com"]
    page = 7

    header = {
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    # 时间戳或许有影响？
    Cookies = {
        "Cookie": "Device_ID=6612718a7aebe1024; Authorization=BFAC74E576E68764876E68457D76E68AE3476E68E3984307F7AC; sl-session=NMSFWlP/FGajNf2GCg9OKw==; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2214589435%22%2C%22first_id%22%3A%2218eb80c54832c3-0793a1535de6db8-26001a51-1327104-18eb80c548462f%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218eb80c54832c3-0793a1535de6db8-26001a51-1327104-18eb80c548462f%22%7D; Hm_lvt_446567e1546b322b726d54ed9b5ad346=1712484799,1712545525,1712636527; Hm_lpvt_446567e1546b322b726d54ed9b5ad346=1712636527"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start_requests(self) -> Iterable[Request]:
        # 第一页
        start_url = "https://www.xinpianchang.com/_next/data/3Ro4vc_ybw72yeHZvXbYx/discover/article/27-0.json"
        param = "27-0"
        yield scrapy.FormRequest(
                url=start_url,
                method='GET',
                headers=self.header,
                cookies=self.Cookies,
                formdata={"param": param},
                callback=self.parse
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.body)
        data_list = data['pageProps']['discoverArticleData']['list']

        for video in data_list:
            item = QySpider1Item()

            item['title'] = video['title']

            category_name = []
            for categories in video['categories']:
                category_name.append(categories['category_name'])
            item['video_type'] = " ".join(category_name)

            # 使用这个网址可以播放视频
            item['play_url'] = "https://www.xinpianchang.com/a{}?from=ArticleList".format(video['id'])
            yield item

        # 剩余的6页
        for i in range(1, self.page):
            next_url = "https://www.xinpianchang.com/_next/data/3Ro4vc_ybw72yeHZvXbYx/discover/article/27-0-all-all-0-0-score-pp{}.json".format(str(i+1))
            param = "27-0-all-all-0-0-score-pp{}".format(str(i+1))
            yield scrapy.FormRequest(
                url=next_url,
                method='GET',
                headers=self.header,
                cookies=self.Cookies,
                formdata={"param": param},
                callback=self.parse
            )


