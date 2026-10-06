"""Initialize the Railway MySQL schema from inside the private app network."""

import os
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT


connection = pymysql.connect(
    host=os.environ["MYSQL_HOST"],
    port=int(os.environ["MYSQL_PORT"]),
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    charset="utf8mb4",
    autocommit=True,
    client_flag=CLIENT.MULTI_STATEMENTS,
)

try:
    with connection.cursor() as cursor:
        sql = Path(__file__).with_name("Aurora_BD.sql").read_text(encoding="utf-8")
        cursor.execute(sql)
        while cursor.nextset():
            pass
finally:
    connection.close()

print("Esquema de Aurora inicializado.")
