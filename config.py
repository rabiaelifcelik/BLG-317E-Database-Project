import pymysql

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='myDb',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)