import pymysql

connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='12345',
    database='myDb',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)