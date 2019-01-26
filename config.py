import os

DEBUG = bool(os.environ.get('DEBUG', 0))

MYSQL_USER = os.environ.get('MYSQL_USER', 'fs')
MYSQL_PW = os.environ.get('MYSQL_PW', 'password')
MYSQL_HOSTNAME = os.environ.get('MYSQL_HOSTNAME', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

SECRET_KEY = os.environ.get('SECRET_KEY', 'test')
