# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class StockNewsItem(scrapy.Item):
    # 这个顺序应该严格对应 数据库 表的字段顺序，否则插入的数据会错位
    _fields_order = ['title', 'article', 'href']
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    article = scrapy.Field()
    href = scrapy.Field()

    @classmethod
    def get_field_names(cls):
        return cls._fields_order

