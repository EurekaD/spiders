# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

"""
标题、类型、地区、时长、上映时间 、导演、演员。 获取前10页的数据
详情页 获取电影的 简介、导演、演员
"""


class QySpider1Item(scrapy.Item):
    title = scrapy.Field()
    video_type = scrapy.Field()
    play_url = scrapy.Field()


class QySpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    movie_type = scrapy.Field()
    area = scrapy.Field()
    time = scrapy.Field()
    open_time = scrapy.Field()

    daoyan = scrapy.Field()
    yanyuan = scrapy.Field()
    info = scrapy.Field()

