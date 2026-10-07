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
        # Columnas añadidas después del despliegue inicial: se crean si faltan
        # para que el inicializador sea idempotente sobre bases ya existentes.
        cursor.execute(
            "select count(*) from information_schema.columns "
            "where table_schema = database() "
            "and table_name = 'centros_atencion' and column_name = 'zona'"
        )
        tiene_zona = cursor.fetchone()[0] > 0
        cursor.execute(
            "select count(*) from information_schema.tables "
            "where table_schema = database() and table_name = 'centros_atencion'"
        )
        if not tiene_zona and cursor.fetchone()[0] > 0:
            cursor.execute(
                "alter table centros_atencion "
                "add column subtipo varchar(60) null after tipo_establecimiento, "
                "add column zona enum('urbano', 'rural') null after subtipo"
            )
            print("Columnas subtipo y zona añadidas a centros_atencion.")

        sql = Path(__file__).with_name("Aurora_BD.sql").read_text(encoding="utf-8")
        cursor.execute(sql)
        while cursor.nextset():
            pass
finally:
    connection.close()

print("Esquema de Aurora inicializado.")
