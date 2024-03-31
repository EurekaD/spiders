"""
新浪网 股票模块
https://finance.sina.com.cn/stock/

要闻区域新闻
"""
from copy import deepcopy
from typing import Iterable, Any
from urllib.request import Request

import scrapy
from scrapy.http import Response
from sina.stock.stock.items import StockNewsItem


class SinaStock(scrapy.Spider):
    name = '要闻'
    allowed_domains = ["finance.sina.com.cn"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start_requests(self) -> Iterable[Request]:
        start_url = "https://finance.sina.com.cn/stock/"
        yield scrapy.Request(
            url=start_url,
            method='GET',
            callback=self.parse
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # print(response.text)
        element_a_list = response.xpath("//div[@class='tabs-cont sto_cont0']/ul/li/a")

        for a in element_a_list:
            text = a.xpath("string(.)").extract_first()
            href = a.xpath("@href").extract_first()
            print(text)

            yield scrapy.Request(
                url=href,
                method='GET',
                callback=self.parse_detail,
                meta=deepcopy({'text': text, 'href': href})
            )

    def parse_detail(self, response: Response, **kwargs: Any) -> Any:
        items = StockNewsItem()
        items['title'] = deepcopy(response.meta['text'])

        p_list = response.xpath("//div[@class='article-content-left']//p")

        article_text_p_list = []
        for p in p_list:
            article_text_p_list.append(p.xpath("string(.)").extract_first())
        items['article'] = ' '.join(article_text_p_list).replace('\u3000', '')
        items['href'] = deepcopy(response.meta['href'])

        if items['article'] != "":
            yield items
