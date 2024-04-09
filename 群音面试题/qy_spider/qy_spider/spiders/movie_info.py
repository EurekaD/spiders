"""
https://ssr3.scrape.center/

标题、类型、地区、时长、上映时间 、导演、演员。 获取前10页的数据
详情页 获取电影的 简介、导演、演员
"""
from copy import deepcopy
from typing import Iterable, Any
from urllib.request import Request

import scrapy
from scrapy.http import Response
from 群音面试题.qy_spider.qy_spider.items import QySpiderItem


class MovieInfo(scrapy.Spider):
    name = '电影信息'
    allowed_domains = ["ssr3.scrape.center"]
    page = 10

    header = {
        "Referer": "https://ssr3.scrape.center/",
        "Authorization": "Basic YWRtaW46YWRtaW4="
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start_requests(self) -> Iterable[Request]:
        start_url = "https://ssr3.scrape.center/"

        yield scrapy.FormRequest(
            url=start_url,
            method='GET',
            headers=self.header,
            callback=self.parse
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # print(response.text)
        element_div_list = response.xpath("//*[@id='index']/div[1]/div[1]/div")

        for div in element_div_list:
            item = QySpiderItem()

            # 外层
            item['title'] = div.xpath("./div/div/div[2]/a/h2/text()").extract_first()
            href = "https://ssr3.scrape.center" + div.xpath("./div/div/div[2]/a/@href").extract_first()

            item['movie_type'] = ".".join(div.xpath("./div/div/div[2]/div[1]/button/span/text()").extract())
            item['area'] = div.xpath("./div/div/div[2]/div[2]/span[1]/text()").extract_first()
            item['time'] = div.xpath("./div/div/div[2]/div[2]/span[3]/text()").extract_first()
            item['open_time'] = div.xpath("./div/div/div[2]/div[3]/span/text()").extract_first()

            yield scrapy.Request(
                url=href,
                method='GET',
                headers=self.header,
                callback=self.parse_detail,
                meta=deepcopy({'item': item, 'href': href})
            )

        # 翻页
        now_page = int(response.xpath("//*[@id='index']//li[@class='number active']/a/text()").extract_first())
        if now_page <= self.page:
            now_page += 1
            yield scrapy.Request(
                url="https://ssr3.scrape.center/page/{}".format(str(now_page)),
                method='GET',
                headers=self.header,
                callback=self.parse
            )

    def parse_detail(self, response: Response, **kwargs: Any) -> Any:

        item = deepcopy(response.meta['item'])
        # 内层

        item['info'] = response.xpath("//*[@id='detail']/div[1]/div/div/div[1]/div/div[2]/div[4]/p").extract_first()

        item['daoyan'] = response.xpath("//*[@id='detail']/div[2]/div/div/div//text()").extract_first()

        # 演员有很多
        div_yanyuan = response.xpath("//*[@id='detail']/div[3]/div/div/div")
        yanyuan = []
        for div in div_yanyuan:
            yanyuan.append("".join(div.xpath("./div/div/p/text()").extract()))
        item['yanyuan'] = " ".join(yanyuan)

        yield item
