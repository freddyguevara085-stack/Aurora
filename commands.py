"""Comandos administrativos interactivos de Aurora."""

import os

import click
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from extensions import db
from models.acceso import Rol
from models.usuario import Usuario
from services.seed import sincronizar_centros_minsa


def register_commands(app) -> None:
    @app.cli.command('consolidate-content')
    def consolidate_content():
        """Publica alertas documentadas y consolida lecturas sin borrar registros."""
        from services.curacion import consolidar_contenido
        try:
            resultado = consolidar_contenido()
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        for nombre, cantidad in resultado.items():
            click.echo(f'{nombre}: {cantidad}')

    @app.cli.command("prepare-deploy")
    def prepare_deploy():
        """Inicializa tablas y catálogos faltantes sin borrar datos existentes."""
        from models.directorio import CentroAtencion

        try:
            db.create_all()
            # create_all no agrega columnas a tablas existentes. Esta migración
            # conserva tanto las fechas estimadas como los registros anteriores.
            with db.engine.begin() as connection:
                columnas = {c['name'] for c in inspect(connection).get_columns('embarazos')}
                if 'fecha_nacimiento_real' not in columnas:
                    connection.execute(text(
                        'ALTER TABLE embarazos ADD COLUMN fecha_nacimiento_real DATE NULL AFTER fpp'))
            for nombre in ("usuario", "administrador", "auditor"):
                if not db.session.scalar(db.select(Rol).filter_by(nombre=nombre)):
                    db.session.add(Rol(nombre=nombre))
            if not db.session.scalar(db.select(CentroAtencion.id).limit(1)):
                sincronizar_centros_minsa()
            if os.getenv("AURORA_DEMO_PASSWORD"):
                from services.demo import crear_demo
                crear_demo(os.environ["AURORA_DEMO_PASSWORD"])
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        click.echo("Base de datos preparada. Los registros existentes se conservan.")

    @app.cli.command("create-demo")
    def create_demo():
        """Crea una sola cuenta ficticia completa para una presentación."""
        from services.demo import crear_demo
        password = os.getenv("AURORA_DEMO_PASSWORD") or click.prompt(
            "Contraseña de demostración (mínimo 12 caracteres)", hide_input=True, confirmation_prompt=True)
        try:
            usuario, creado = crear_demo(password)
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            raise click.ClickException(str(error))
        except Exception:
            db.session.rollback()
            raise
        click.echo(f"{'Cuenta creada' if creado else 'Cuenta existente, sin cambios'}: {usuario.email}")

    @app.cli.command("create-user")
    def create_user() -> None:
        """Crea una cuenta inicial sin aceptar contraseñas como argumentos."""
        nombres = click.prompt("Nombres").strip()
        apellidos = click.prompt("Apellidos").strip()
        email = click.prompt("Correo").strip().lower()
        roles = db.session.scalars(db.select(Rol).order_by(Rol.id)).all()
        if not roles:
            raise click.ClickException("No hay roles disponibles.")

        click.echo("Roles disponibles: " + ", ".join(f"{rol.id}: {rol.nombre}" for rol in roles))
        rol_id = click.prompt("ID de rol", type=int)
        password = click.prompt("Contraseña", hide_input=True, confirmation_prompt=True)
        if len(password) < 8:
            raise click.ClickException("La contraseña debe tener al menos 8 caracteres.")
        if db.session.scalar(db.select(Usuario).filter_by(email=email)):
            raise click.ClickException("No se pudo crear la cuenta.")
        if not db.session.get(Rol, rol_id):
            raise click.ClickException("No se pudo crear la cuenta.")

        try:
            db.session.add(
                Usuario(
                    rol_id=rol_id,
                    nombres=nombres,
                    apellidos=apellidos,
                    email=email,
                    password_hash=generate_password_hash(password),
                    activo=1,
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise click.ClickException("No se pudo crear la cuenta.")

        click.echo("Cuenta creada.")

    @app.cli.command("seed-centros")
    @click.option('--departamento', default=None, help='Sincronizar únicamente este departamento.')
    def seed_centros(departamento) -> None:
        """Puebla o sincroniza el directorio nacional de centros de salud del MINSA."""
        click.echo("Sincronizando directorio MINSA (hospitales, centros de salud, casas maternas)...")
        resumen = sincronizar_centros_minsa(retirar_no_listados=False, departamento=departamento)
        db.session.commit()
        click.echo(
            f"Directorio MINSA listo: {resumen['total']} centros de {departamento or 'toda Nicaragua'} "
            f"({resumen['nuevos']} nuevos, {resumen['actualizados']} actualizados)."
        )

    @app.cli.command('publish-madriz-info')
    def publish_madriz_info():
        """Publica las cuatro orientaciones documentales sobre acceso y organización."""
        import json
        from datetime import date
        from pathlib import Path
        from models.contenido import ContenidoPrenatal

        ruta = Path(app.root_path) / 'database/seeds/orientaciones_madriz.json'
        nuevos = 0
        for datos in json.loads(ruta.read_text(encoding='utf-8')):
            # Repetir el comando conserva las ediciones posteriores del administrador.
            if db.session.scalar(db.select(ContenidoPrenatal).filter_by(titulo=datos['titulo'])):
                continue
            datos['fecha_revision'] = date.fromisoformat(datos['fecha_revision'])
            db.session.add(ContenidoPrenatal(**datos, publicado=1))
            nuevos += 1
        db.session.commit()
        click.echo(f'Orientaciones publicadas: {nuevos}. Las existentes se conservan.')
