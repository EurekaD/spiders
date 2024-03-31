
from database.local_database import MYSQL_CONNECT


class DbUtils:
    def __init__(self):
        self.conn = MYSQL_CONNECT
        self.__cursor = self.conn.cursor()

    def get_table_fields(self, table_name, increment_primary_key=False):
        """获取表字段信息"""
        sql = 'DESCRIBE {};'.format(table_name)
        self.__cursor.execute(sql)
        result = self.__cursor.fetchall()
        if not increment_primary_key:
            column_names = [row[0] for row in result if row[5] != 'auto_increment']
        else:
            column_names = [row[0] for row in result]
        return column_names


if __name__ == '__main__':
    db_util = DbUtils()
    result = db_util.get_table_fields('sina_news')
    print(result)
