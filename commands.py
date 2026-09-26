"""Comandos administrativos interactivos de Aurora."""

from datetime import date, datetime, time, timedelta
import click
from werkzeug.security import generate_password_hash

from demo_nicaragua import CENTROS as CENTROS_VERIFICADOS
from extensions import db
from models.acceso import Rol
from models.directorio import CentroAtencion
from models.gestacion import Embarazo, PerfilGestante
from models.seguimiento import ControlPrenatal, Recordatorio
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

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Carga una gestante demo ficticia y centros confirmados por el MINSA."""
        if not app.config.get("DEMO_MODE"):
            raise click.ClickException(
                "seed-demo solo carga datos de demostración. Ejecútalo en una base de "
                "demo con AURORA_DEMO=1; nunca en la base real."
            )
        click.echo("Preparando datos de demostración (perfil ficticio y centros oficiales)...")

        # Retira las filas de centros demo que versiones anteriores marcaban como verificadas.
        codigos_demo = ["MINSA-MGA-001", "MINSA-MGA-002", "MINSA-MGA-003", "MINSA-MGA-004", "MINSA-MGA-005", "MINSA-LEO-001", "MINSA-MAS-001", "MINSA-GRA-001", "MINSA-EST-002", "MINSA-MAT-001"]
        db.session.execute(
            db.update(CentroAtencion)
            .where(CentroAtencion.codigo_minsa.in_(codigos_demo))
            .values(activo=0, fecha_verificacion=None)
        )
        from models.contenido import ContenidoPrenatal, SenalAlerta
        db.session.execute(
            db.update(ContenidoPrenatal)
            .where(ContenidoPrenatal.creado_por_usuario_id.is_(None))
            .values(publicado=0)
        )
        db.session.execute(
            db.update(SenalAlerta)
            .where(SenalAlerta.creado_por_usuario_id.is_(None))
            .values(activo=0)
        )

        # Centros confirmados en fuentes oficiales (MINSA). Idempotente: solo
        # inserta los que no existen y no modifica centros preexistentes.
        centros_nuevos = 0
        for datos in CENTROS_VERIFICADOS:
            existente = db.session.scalar(
                db.select(CentroAtencion).where(
                    CentroAtencion.nombre == datos["nombre"],
                    CentroAtencion.municipio == datos["municipio"],
                )
            )
            if existente:
                continue
            db.session.add(
                CentroAtencion(
                    nombre=datos["nombre"],
                    tipo_establecimiento=datos["tipo_establecimiento"],
                    silais=datos["silais"],
                    departamento=datos["departamento"],
                    municipio=datos["municipio"],
                    direccion=datos["direccion"],
                    telefono=None,
                    horario=None,
                    latitud=None,
                    longitud=None,
                    fecha_verificacion=None,
                    activo=1,
                )
            )
            centros_nuevos += 1
        db.session.flush()

        # 4. Asegurar cuenta demo gestante
        rol_usuario = db.session.scalar(db.select(Rol).filter_by(nombre="usuario"))
        if not rol_usuario:
            rol_usuario = Rol(nombre="usuario", descripcion="Gestante de Aurora")
            db.session.add(rol_usuario)
            db.session.flush()

        email_demo = "maria.demo@aurora.ni"
        usuario_demo = db.session.scalar(db.select(Usuario).filter_by(email=email_demo))
        if not usuario_demo:
            usuario_demo = Usuario(
                rol_id=rol_usuario.id,
                nombres="María José",
                apellidos="Pérez Gómez",
                email=email_demo,
                password_hash=generate_password_hash("Password123!"),
                activo=1,
            )
            db.session.add(usuario_demo)
            db.session.flush()
        else:
            usuario_demo.nombres = "María José"
            usuario_demo.apellidos = "Pérez Gómez"
            usuario_demo.password_hash = generate_password_hash("Password123!")
            usuario_demo.activo = 1
            db.session.flush()

        # 5. Perfil de la gestante
        perfil = db.session.scalar(
            db.select(PerfilGestante).filter_by(usuario_id=usuario_demo.id)
        )
        if not perfil:
            perfil = PerfilGestante(usuario_id=usuario_demo.id)
            db.session.add(perfil)
        perfil.cedula = None
        perfil.fecha_nacimiento = None
        perfil.telefono = None
        perfil.municipio = None
        perfil.departamento = None
        perfil.direccion_residencia = None
        perfil.contacto_emergencia_nombre = None
        perfil.contacto_emergencia_telefono = None
        perfil.consentimiento_datos = 0
        perfil.fecha_consentimiento = None
        db.session.flush()

        # 6. Embarazo activo en Semana 24 (punto ideal de demostración)
        hoy = date.today()
        fum_calculada = hoy - timedelta(days=24 * 7)  # Hace exactamente 24 semanas
        fpp_calculada = fum_calculada + timedelta(days=280)

        embarazo = db.session.scalar(
            db.select(Embarazo).filter_by(perfil_gestante_id=perfil.id, estado="activo")
        )
        if not embarazo:
            embarazo = Embarazo(
                perfil_gestante_id=perfil.id,
                fum=fum_calculada,
                fpp=fpp_calculada,
                metodo_fpp="fum",
                estado="activo",
            )
            db.session.add(embarazo)
            db.session.flush()
        else:
            embarazo.fum = fum_calculada
            embarazo.fpp = fpp_calculada
            embarazo.metodo_fpp = "fum"
            db.session.flush()

        # Eliminar detalles de salud y citas ficticias anteriores de esta cuenta demo.
        db.session.execute(
            db.delete(ControlPrenatal).where(ControlPrenatal.embarazo_id == embarazo.id)
        )
        db.session.flush()

        # Cita ficticia solo para demostrar el calendario: no contiene indicaciones médicas.
        control = ControlPrenatal(
            embarazo_id=embarazo.id,
            registrado_por_usuario_id=usuario_demo.id,
            numero_control=1,
            fecha_control=hoy + timedelta(days=4),
            hora_control=None,
            edad_gestacional_semanas=None,
            estado="programado",
            centro_atencion_id=None,
            indicaciones=None,
            notas=None,
        )
        db.session.add(control)
        db.session.flush()

        # 8. Recordatorios activos en calendario
        # Limpiar recordatorios previos de la cuenta demo
        db.session.execute(
            db.delete(Recordatorio).where(Recordatorio.usuario_id == usuario_demo.id)
        )
        db.session.flush()

        recordatorio = Recordatorio(
            usuario_id=usuario_demo.id,
            control_prenatal_id=control.id,
            titulo="Preparar preguntas para mi cita",
            descripcion="Ejemplo ficticio: anota dudas para conversarlas con el personal de salud.",
            tipo="control",
            fecha_hora=datetime.combine(hoy + timedelta(days=4), time(7, 30)),
            estado="pendiente",
        )
        db.session.add(recordatorio)
        db.session.commit()

        click.echo(f"- Centros confirmados por el MINSA: {centros_nuevos} nuevos.")
        click.echo("- Gestante demo configurada con éxito:")
        click.echo("  * Correo:      maria.demo@aurora.ni")
        click.echo("  * Contraseña:  Password123!")
        click.echo("  * Datos ficticios, sin información clínica ni de contacto real.")
        click.echo("  * Teléfonos y horarios de centros: no confirmados en la fuente.")
        click.echo("  * Contenido clínico: no se publica; permanece como borrador.")
        click.echo("¡Datos de demostración listos!")
