"""Comandos administrativos interactivos de Aurora."""

import click
from werkzeug.security import generate_password_hash

from extensions import db
from models.acceso import Rol
from models.usuario import Usuario


def register_commands(app) -> None:
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
