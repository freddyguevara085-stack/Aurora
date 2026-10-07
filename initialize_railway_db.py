"""Initialize the Railway MySQL schema from inside the private app network."""

import os
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

from demo_nicaragua import CENTROS, SENALES_ALERTA


connection = pymysql.connect(
    host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
    port=int(os.environ.get("MYSQL_PORT", 3306)),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", ""),
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

        # La conexión no fija una base por defecto: recién tras ejecutar el SQL
        # (que hace `use aurora`) `database()` apunta al esquema correcto.
        # MySQL no admite "add column if not exists", así que se consulta
        # information_schema para mantener el inicializador idempotente sobre
        # bases creadas antes de añadir subtipo y zona.
        cursor.execute(
            "select count(*) from information_schema.columns "
            "where table_schema = database() "
            "and table_name = 'centros_atencion' and column_name = 'zona'"
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "alter table centros_atencion "
                "add column subtipo varchar(60) null after tipo_establecimiento, "
                "add column zona enum('urbano', 'rural') null after subtipo"
            )
            print("Columnas subtipo y zona añadidas a centros_atencion.")

        # Sincronización idempotente de los 438 centros del MINSA en toda Nicaragua
        cursor.execute("select id, nombre, municipio from centros_atencion")
        existentes = {(row[1], row[2]): row[0] for row in cursor.fetchall()}

        nuevos_centros = 0
        actualizados_centros = 0
        for datos in CENTROS:
            clave = (datos["nombre"], datos["municipio"])
            if clave in existentes:
                cursor.execute(
                    "update centros_atencion set "
                    "tipo_establecimiento = %s, subtipo = %s, zona = %s, "
                    "silais = %s, departamento = %s, direccion = %s, activo = 1 "
                    "where id = %s",
                    (
                        datos["tipo_establecimiento"],
                        datos.get("subtipo"),
                        datos.get("zona"),
                        datos["silais"],
                        datos["departamento"],
                        datos["direccion"],
                        existentes[clave],
                    ),
                )
                actualizados_centros += 1
            else:
                cursor.execute(
                    "insert into centros_atencion "
                    "(nombre, tipo_establecimiento, subtipo, zona, silais, "
                    "departamento, municipio, direccion, activo) "
                    "values (%s, %s, %s, %s, %s, %s, %s, %s, 1)",
                    (
                        datos["nombre"],
                        datos["tipo_establecimiento"],
                        datos.get("subtipo"),
                        datos.get("zona"),
                        datos["silais"],
                        datos["departamento"],
                        datos["municipio"],
                        datos["direccion"],
                    ),
                )
                nuevos_centros += 1

        print(
            f"Directorio MINSA sincronizado ({len(CENTROS)} centros de toda Nicaragua: "
            f"{nuevos_centros} insertados, {actualizados_centros} actualizados)."
        )

        # Sincronización idempotente del catálogo de señales de alerta oficiales MINSA
        cursor.execute("select id, titulo from senales_alerta")
        senales_existentes = {row[1]: row[0] for row in cursor.fetchall()}

        senales_nuevas = 0
        senales_actualizadas = 0
        for senal in SENALES_ALERTA:
            if senal["titulo"] in senales_existentes:
                cursor.execute(
                    "update senales_alerta set "
                    "descripcion = %s, accion_recomendada = %s, orden_visual = %s, "
                    "fuente_nombre = %s, fuente_url = %s, fecha_revision = %s, activo = 1 "
                    "where id = %s",
                    (
                        senal["descripcion"],
                        senal["accion_recomendada"],
                        senal["orden_visual"],
                        senal["fuente_nombre"],
                        senal.get("fuente_url"),
                        senal["fecha_revision"],
                        senales_existentes[senal["titulo"]],
                    ),
                )
                senales_actualizadas += 1
            else:
                cursor.execute(
                    "insert into senales_alerta "
                    "(titulo, descripcion, accion_recomendada, orden_visual, "
                    "fuente_nombre, fuente_url, fecha_revision, activo) "
                    "values (%s, %s, %s, %s, %s, %s, %s, 1)",
                    (
                        senal["titulo"],
                        senal["descripcion"],
                        senal["accion_recomendada"],
                        senal["orden_visual"],
                        senal["fuente_nombre"],
                        senal.get("fuente_url"),
                        senal["fecha_revision"],
                    ),
                )
                senales_nuevas += 1

        print(
            f"Señales de alerta sincronizadas ({len(SENALES_ALERTA)} señales: "
            f"{senales_nuevas} insertadas, {senales_actualizadas} actualizadas)."
        )

finally:
    connection.close()

print("Esquema y datos de Aurora inicializados con éxito.")
