"""Comandos administrativos interactivos de Aurora."""

from datetime import date, datetime, time, timedelta
import secrets
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
        """Carga cuatro cuentas ficticias y centros listados por el MINSA."""
        if not app.config.get("DEMO_MODE"):
            raise click.ClickException(
                "seed-demo solo carga datos de demostración. Ejecútalo en una base de "
                "demo con AURORA_DEMO=1; nunca en la base real."
            )
        click.echo("Preparando cuatro perfiles ficticios y centros oficiales...")

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

        # Centros confirmados en el listado oficial del MINSA. Idempotente:
        # inserta los faltantes, sincroniza los existentes con el listado y
        # retira del directorio activo los que no provienen del listado
        # (p. ej. registros de seeds anteriores con nombres distintos).
        centros_nuevos = 0
        claves_canonicas = {
            (datos["nombre"], datos["municipio"]) for datos in CENTROS_VERIFICADOS
        }
        for datos in CENTROS_VERIFICADOS:
            existente = db.session.scalar(
                db.select(CentroAtencion).where(
                    CentroAtencion.nombre == datos["nombre"],
                    CentroAtencion.municipio == datos["municipio"],
                )
            )
            if existente:
                existente.tipo_establecimiento = datos["tipo_establecimiento"]
                existente.subtipo = datos.get("subtipo")
                existente.silais = datos["silais"]
                existente.departamento = datos["departamento"]
                existente.direccion = datos["direccion"]
                existente.zona = datos.get("zona")
                existente.activo = 1
                continue
            db.session.add(
                CentroAtencion(
                    nombre=datos["nombre"],
                    tipo_establecimiento=datos["tipo_establecimiento"],
                    subtipo=datos.get("subtipo"),
                    zona=datos.get("zona"),
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
        retirados = 0
        for centro in db.session.scalars(
            db.select(CentroAtencion).where(CentroAtencion.activo == 1)
        ):
            if (centro.nombre, centro.municipio) not in claves_canonicas:
                centro.activo = 0
                retirados += 1
        db.session.flush()
        click.echo(
            f"Directorio MINSA listo: {len(CENTROS_VERIFICADOS)} centros del listado "
            f"({centros_nuevos} nuevos, {retirados} retirados)."
        )

        # 4. Asegurar cuenta de prueba principal
        rol_usuario = db.session.scalar(db.select(Rol).filter_by(nombre="usuario"))
        if not rol_usuario:
            rol_usuario = Rol(nombre="usuario", descripcion="Gestante de Aurora")
            db.session.add(rol_usuario)
            db.session.flush()

        email_demo = CUENTA_DEMO_EMAIL
        password_demo = secrets.token_urlsafe(12)
        usuario_demo = db.session.scalar(db.select(Usuario).filter_by(email=email_demo))
        if not usuario_demo:
            usuario_demo = Usuario(
                rol_id=rol_usuario.id,
                nombres="Caso ficticio semana 24",
                apellidos="",
                email=email_demo,
                password_hash=generate_password_hash(password_demo),
                activo=1,
            )
            db.session.add(usuario_demo)
            db.session.flush()
        else:
            usuario_demo.nombres = "Caso ficticio semana 24"
            usuario_demo.apellidos = ""
            usuario_demo.password_hash = generate_password_hash(password_demo)
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
                acompanante_nombre="Acompañante ficticio",
                acompanante_telefono=None,
                cuidador_hijos="Dato de ejemplo",
                transporte_tipo="caponera_taxi",
                transporte_contacto="Transporte ficticio; sin teléfono",
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
                "Contacto ficticio 1",
                "brigadista",
                None,
                "Barrio de ejemplo",
                "Dato ficticio; no corresponde a una persona real.",
            ),
            (
                "Contacto ficticio 2",
                "traslado_local",
                None,
                "Sector de ejemplo",
                "Dato ficticio; no corresponde a una persona real.",
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

        credenciales = [(email_demo, password_demo)]
        for email, nombre, semana, departamento, municipio in [
            ("prueba.semana08@example.com", "Caso ficticio semana 8", 8, "Managua", "Managua"),
            ("prueba.semana20@example.com", "Caso ficticio semana 20", 20, "Boaco", "Boaco"),
            ("prueba.semana34@example.com", "Caso ficticio semana 34", 34, "Estelí", "Estelí"),
        ]:
            password = secrets.token_urlsafe(12)
            cuenta = db.session.scalar(db.select(Usuario).filter_by(email=email))
            if not cuenta:
                cuenta = Usuario(
                    rol_id=rol_usuario.id,
                    nombres=nombre,
                    apellidos="",
                    email=email,
                    password_hash=generate_password_hash(password),
                    activo=1,
                )
                db.session.add(cuenta)
                db.session.flush()
            else:
                cuenta.nombres = nombre
                cuenta.apellidos = ""
                cuenta.password_hash = generate_password_hash(password)
                cuenta.activo = 1

            perfil_prueba = db.session.scalar(
                db.select(PerfilGestante).filter_by(usuario_id=cuenta.id)
            )
            if not perfil_prueba:
                perfil_prueba = PerfilGestante(usuario_id=cuenta.id)
                db.session.add(perfil_prueba)
                db.session.flush()
            perfil_prueba.cedula = None
            perfil_prueba.fecha_nacimiento = None
            perfil_prueba.telefono = None
            perfil_prueba.municipio = municipio
            perfil_prueba.departamento = departamento
            perfil_prueba.direccion_residencia = None
            perfil_prueba.contacto_emergencia_nombre = None
            perfil_prueba.contacto_emergencia_telefono = None
            perfil_prueba.consentimiento_datos = 0
            perfil_prueba.fecha_consentimiento = None
            db.session.flush()

            embarazo_prueba = db.session.scalar(
                db.select(Embarazo).filter_by(
                    perfil_gestante_id=perfil_prueba.id, estado="activo"
                )
            )
            fum_prueba = hoy - timedelta(days=semana * 7)
            if not embarazo_prueba:
                embarazo_prueba = Embarazo(
                    perfil_gestante_id=perfil_prueba.id,
                    fum=fum_prueba,
                    fpp=fum_prueba + timedelta(days=280),
                    metodo_fpp="fum",
                    estado="activo",
                )
                db.session.add(embarazo_prueba)
                db.session.flush()
            else:
                embarazo_prueba.fum = fum_prueba
                embarazo_prueba.fpp = fum_prueba + timedelta(days=280)
                embarazo_prueba.metodo_fpp = "fum"

            db.session.execute(
                db.delete(Recordatorio).where(Recordatorio.usuario_id == cuenta.id)
            )
            db.session.execute(
                db.delete(PlanParto).where(PlanParto.embarazo_id == embarazo_prueba.id)
            )
            db.session.execute(
                db.delete(ContactoComunitario).where(
                    ContactoComunitario.perfil_gestante_id == perfil_prueba.id
                )
            )
            db.session.execute(
                db.delete(ControlPrenatal).where(
                    ControlPrenatal.embarazo_id == embarazo_prueba.id
                )
            )
            db.session.execute(
                db.delete(PreguntaConsulta).where(PreguntaConsulta.usuario_id == cuenta.id)
            )
            db.session.flush()

            control_prueba = ControlPrenatal(
                embarazo_id=embarazo_prueba.id,
                registrado_por_usuario_id=cuenta.id,
                numero_control=1,
                fecha_control=hoy + timedelta(days=7),
                hora_control=time(10, 0),
                edad_gestacional_semanas=float(semana + 1),
                estado="programado",
                indicaciones=None,
            )
            db.session.add(control_prueba)
            db.session.flush()
            db.session.add(
                PlanParto(
                    embarazo_id=embarazo_prueba.id,
                    requiere_casa_materna=0,
                    acompanante_nombre="Acompañante ficticio",
                    cuidador_hijos="Dato de ejemplo",
                    transporte_tipo="familiar_vecino",
                    transporte_contacto="Transporte ficticio; sin teléfono",
                    bulto_listo=0,
                    recursos_traslado_listos=0,
                    notas="Registro ficticio para conocer la aplicación.",
                )
            )
            db.session.add(
                ContactoComunitario(
                    perfil_gestante_id=perfil_prueba.id,
                    nombre="Contacto de prueba",
                    rol="otro",
                    comunidad_barrio="Ubicación de ejemplo",
                    notas="Dato ficticio; no corresponde a una persona real.",
                )
            )
            db.session.add(
                PreguntaConsulta(
                    usuario_id=cuenta.id,
                    pregunta="¿Dónde puedo revisar mi próxima cita de ejemplo?",
                    estado="pendiente",
                )
            )
            db.session.add(
                Recordatorio(
                    usuario_id=cuenta.id,
                    control_prenatal_id=control_prueba.id,
                    titulo="Próximo control de ejemplo",
                    descripcion="Dato ficticio para explorar la agenda.",
                    tipo="control",
                    fecha_hora=datetime.combine(hoy + timedelta(days=6), time(10, 0)),
                    estado="pendiente",
                )
            )
            credenciales.append((email, password))

        db.session.commit()

        click.echo(f"- Centros confirmados por el MINSA: {centros_nuevos} nuevos.")
        click.echo("- Cuatro cuentas de prueba listas; comparte cada credencial en privado:")
        for email, password in credenciales:
            click.echo(f"  * {email} / {password}")
        click.echo("  * Perfiles, agendas y apoyos ficticios; sin teléfonos reales.")
        click.echo("  * Teléfonos y horarios de centros: no confirmados en la fuente.")
        click.echo("  * Contenido clínico: no se publica; permanece como borrador.")
        click.echo("¡Datos de demostración listos!")
