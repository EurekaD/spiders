# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import json

from itemadapter import ItemAdapter


class QySpiderPipeline:
    def __init__(self):
        self.file = open('items.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):

        json_item = json.dumps(dict(item), ensure_ascii=False)

        # 将JSON格式的Item写入文件
        line = json_item + '\n'
        self.file.write(line)

        return item
