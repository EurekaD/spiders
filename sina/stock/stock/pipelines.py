# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from database.local_database import MYSQL_CONNECT
from database.db_utils import DbUtils
from sina.stock.stock.items import StockNewsItem

class StockPipeline:
    def __init__(self):
        self.conn = MYSQL_CONNECT
        self.cursor = self.conn.cursor()
        self.spider_name = "新浪股票模块新闻"
        self.table_name = 'sina_news'

        column = '(' + ",".join(self.get_column_names()) + ')'

        values_str = ['%s' for _ in range(0, len(self.get_column_names()))]
        values = '(' + ','.join(values_str) + ')'

        self.insert_sql = "REPLACE INTO {} {} VALUES {}".format(self.table_name, column, values)


    def get_column_names(self) -> list[str]:
        db_util = DbUtils()
        return db_util.get_table_fields(self.table_name)

    def process_item(self, item, spider):
        fields = StockNewsItem.get_field_names()
        data = []
        for field in fields:
            data.append(item[field])
        self.cursor.execute(self.insert_sql, data)
        self.conn.commit()
        data.clear()
        return item



if __name__ == "__main__":
    test = StockPipeline()





