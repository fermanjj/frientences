from config import *
import mysql.connector


def get_conn_cursor(
        user: str = MYSQL_USER, pw: str = MYSQL_PW, host: str = MYSQL_HOSTNAME, port: int = MYSQL_PORT,
        auto_commit: bool = True, raise_warnings: bool = True, get_warnings: bool = True,
        auth_plugin: str = 'mysql_native_password'
):

    conn_info = {
        'user': user,
        'password': pw,
        'host': host,
        'port': port,
        'autocommit': auto_commit,
        'raise_on_warnings': raise_warnings,
        'get_warnings': get_warnings,
        'auth_plugin': auth_plugin
    }

    conn = mysql.connector.connect(**conn_info)
    cursor = conn.cursor(dictionary=True)

    return conn, cursor
