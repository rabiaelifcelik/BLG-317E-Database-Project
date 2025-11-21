import os

class Config:
    SECRET_KEY = "your-secret-key" # To be fixed
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "root"
    MYSQL_DB = "movies_db"
    MYSQL_CURSORCLASS = "DictCursor"