import pymysql

MYSQL_CONNECT = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='chenlin',
    database='fastnews',
    charset='utf8'
)