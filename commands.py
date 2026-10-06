"""Comandos administrativos interactivos de Aurora."""

from datetime import date, datetime, time, timedelta
import click
from werkzeug.security import generate_password_hash

from demo_nicaragua import CENTROS as CENTROS_VERIFICADOS
from demo_nicaragua import CUENTA_DEMO_EMAIL
from extensions import db
from models.acceso import Rol
from models.directorio import CentroAtencion
from models.gestacion import ContactoComunitario, Embarazo, PerfilGestante, PlanParto
from models.seguimiento import ControlPrenatal, PreguntaConsulta, Recordatorio
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

        email_demo = CUENTA_DEMO_EMAIL
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
        perfil.municipio = "Managua"
        perfil.departamento = "Managua"
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

        # 6b. Plan de parto demostrativo (logística, sin datos clínicos)
        db.session.execute(
            db.delete(PlanParto).where(PlanParto.embarazo_id == embarazo.id)
        )
        centro_referencia = db.session.scalar(
            db.select(CentroAtencion)
            .where(
                CentroAtencion.activo == 1,
                CentroAtencion.tipo_establecimiento.in_(("hospital", "centro_salud")),
            )
            .order_by(CentroAtencion.id)
            .limit(1)
        )
        db.session.add(
            PlanParto(
                embarazo_id=embarazo.id,
                centro_atencion_id=centro_referencia.id if centro_referencia else None,
                requiere_casa_materna=0,
                acompanante_nombre="Rosa Guevara (Hermana)",
                acompanante_telefono="8888-0000",
                cuidador_hijos="Abuela materna en casa",
                transporte_tipo="caponera_taxi",
                transporte_contacto="Don Carlos (Taxi barrio) - 8777-1111",
                bulto_listo=1,
                recursos_traslado_listos=1,
                notas=None,
            )
        )
        db.session.flush()

        # 6c. Red comunitaria de apoyo demostrativa (brigadista y traslado local)
        db.session.execute(
            db.delete(ContactoComunitario).where(
                ContactoComunitario.perfil_gestante_id == perfil.id
            )
        )
        db.session.flush()
        contactos_comunitarios_def = [
            (
                "Doña Silvia Martínez",
                "brigadista",
                "8888-2345",
                "Barrio Jorge Smith",
                "Enlace con el centro de salud municipal",
            ),
            (
                "Don Pedro Fonseca",
                "traslado_local",
                "8765-4321",
                "Sector San Antonio",
                "Camioneta disponible para traslado hacia el centro de salud u hospital",
            ),
        ]
        for nombre, rol, telefono, comunidad, notas in contactos_comunitarios_def:
            db.session.add(
                ContactoComunitario(
                    perfil_gestante_id=perfil.id,
                    nombre=nombre,
                    rol=rol,
                    telefono=telefono,
                    comunidad_barrio=comunidad,
                    notas=notas,
                )
            )
        db.session.flush()

        # 7. Controles ficticios coherentes (sin indicaciones clínicas)
        db.session.execute(
            db.delete(ControlPrenatal).where(ControlPrenatal.embarazo_id == embarazo.id)
        )
        db.session.flush()

        controles_def = [
            (1, fum_calculada + timedelta(days=8 * 7), 8, "realizado"),
            (2, fum_calculada + timedelta(days=16 * 7), 16, "realizado"),
            (3, hoy - timedelta(days=5), 24, "realizado"),
            (4, hoy + timedelta(days=7), 25, "programado"),
        ]
        controles = []
        for numero, fecha, edad, estado in controles_def:
            control = ControlPrenatal(
                embarazo_id=embarazo.id,
                registrado_por_usuario_id=usuario_demo.id,
                numero_control=numero,
                fecha_control=fecha,
                hora_control=time(9, 0),
                edad_gestacional_semanas=float(edad),
                estado=estado,
                centro_atencion_id=None,
                indicaciones=None,
            )
            db.session.add(control)
            db.session.flush()
            controles.append(control)
        proximo = controles[-1]

        # 8. Preguntas ficticias del hilo persistente (reemplazan la nota del control)
        db.session.execute(
            db.delete(PreguntaConsulta).where(PreguntaConsulta.usuario_id == usuario_demo.id)
        )
        db.session.flush()
        preguntas_def = [
            "¿Qué documentos necesito llevar a mi próxima consulta?",
            "¿Cuándo será mi próximo control prenatal?",
        ]
        for texto in preguntas_def:
            db.session.add(
                PreguntaConsulta(usuario_id=usuario_demo.id, pregunta=texto, estado="pendiente")
            )

        # 9. Recordatorios ficticios coherentes (sin indicaciones clínicas)
        db.session.execute(
            db.delete(Recordatorio).where(Recordatorio.usuario_id == usuario_demo.id)
        )
        db.session.flush()

        recordatorios_def = [
            ("Próximo control prenatal", "Recuerda asistir a tu cita de demostración.", "control", datetime.combine(hoy + timedelta(days=7), time(8, 0)), proximo.id),
            ("Anotar dudas para la consulta", "Ejemplo ficticio: prepara tus preguntas.", "personal", datetime.combine(hoy + timedelta(days=2), time(19, 0)), None),
            ("Preparar documentos para mi cita", "Ejemplo ficticio de recordatorio personal.", "personal", datetime.combine(hoy + timedelta(days=5), time(18, 0)), None),
        ]
        for titulo, descripcion, tipo, fecha_hora, control_id in recordatorios_def:
            db.session.add(
                Recordatorio(
                    usuario_id=usuario_demo.id,
                    control_prenatal_id=control_id,
                    titulo=titulo,
                    descripcion=descripcion,
                    tipo=tipo,
                    fecha_hora=fecha_hora,
                    estado="pendiente",
                )
            )
        db.session.commit()

        click.echo(f"- Centros confirmados por el MINSA: {centros_nuevos} nuevos.")
        click.echo("- Gestante demo configurada con éxito:")
        click.echo(f"  * Correo:      {email_demo}")
        click.echo("  * Contraseña:  Password123!")
        click.echo("  * Perfil, embarazo semana 24, 3 controles realizados + 1 programado, 2 preguntas, 3 recordatorios, plan de traslado y apoyo, y contactos personales listos.")
        click.echo("  * Datos ficticios, sin cédula, teléfonos ni contacto de emergencia.")
        click.echo("  * Teléfonos y horarios de centros: no confirmados en la fuente.")
        click.echo("  * Contenido clínico: no se publica; permanece como borrador.")
        click.echo("¡Datos de demostración listos!")
