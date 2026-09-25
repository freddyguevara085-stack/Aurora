"""Comandos administrativos interactivos de Aurora."""

from datetime import date, datetime, time, timedelta
import click
from werkzeug.security import generate_password_hash

from extensions import db
from models.acceso import Rol
from models.directorio import CentroAtencion, CentroServicio, Servicio
from models.gestacion import Embarazo, PerfilGestante
from models.seguimiento import ControlPrenatal, Recordatorio
from models.usuario import Usuario


CENTROS_NICARAGUA = [
    {
        "codigo_minsa": "MINSA-MGA-001",
        "nombre": "Hospital Bertha Calderón Roque",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS Managua",
        "municipio": "Managua",
        "departamento": "Managua",
        "direccion": "Frente a Zumen, Distrito III, Managua",
        "telefono": "2265-1770",
        "horario": "Atención de emergencias 24 horas. Consulta externa: 7:00 AM - 4:00 PM",
        "latitud": 12.1287600,
        "longitud": -86.2941500,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-MGA-002",
        "nombre": "Hospital Occidental Dr. Fernando Vélez Paiz",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS Managua",
        "municipio": "Managua",
        "departamento": "Managua",
        "direccion": "Km 5.5 Carretera Sur, Managua",
        "telefono": "2250-7100",
        "horario": "Atención continua 24 horas",
        "latitud": 12.1246000,
        "longitud": -86.3115000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-MGA-003",
        "nombre": "Hospital Alemán Nicaragüense",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS Managua",
        "municipio": "Managua",
        "departamento": "Managua",
        "direccion": "Costado norte del complejo Concepción Palacios, Managua",
        "telefono": "2249-1120",
        "horario": "Atención de emergencias 24 horas",
        "latitud": 12.1468000,
        "longitud": -86.2235000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-MGA-004",
        "nombre": "Centro de Salud Silvia Ferrufino",
        "tipo_establecimiento": "centro_salud",
        "silais": "SILAIS Managua",
        "municipio": "Managua",
        "departamento": "Managua",
        "direccion": "Barrio Waspán Sur, de la terminal de buses 2c al lago, Managua",
        "telefono": "2249-3401",
        "horario": "Lunes a Viernes: 7:00 AM - 4:00 PM",
        "latitud": 12.1554000,
        "longitud": -86.2301000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-MGA-005",
        "nombre": "Casa Materna Camila López",
        "tipo_establecimiento": "casa_materna",
        "silais": "SILAIS Managua",
        "municipio": "Managua",
        "departamento": "Managua",
        "direccion": "Distrito V, Managua",
        "telefono": "2278-4512",
        "horario": "Albergue y acompañamiento prenatal continuo 24 horas",
        "latitud": 12.1121000,
        "longitud": -86.2632000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-LEO-001",
        "nombre": "Hospital Escuela Óscar Danilo Rosales Argüello (HEODRA)",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS León",
        "municipio": "León",
        "departamento": "León",
        "direccion": "Costado sur de la Catedral de León",
        "telefono": "2311-2221",
        "horario": "Emergencias 24 horas",
        "latitud": 12.4348000,
        "longitud": -86.8781000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-MAS-001",
        "nombre": "Hospital Departamental Humberto Alvarado Vásquez",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS Masaya",
        "municipio": "Masaya",
        "departamento": "Masaya",
        "direccion": "Entrada principal a Masaya sobre carretera a Granada",
        "telefono": "2522-2244",
        "horario": "Emergencias maternas 24 horas",
        "latitud": 11.9687000,
        "longitud": -86.0892000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-GRA-001",
        "nombre": "Hospital Amistad Japón-Nicaragua",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS Granada",
        "municipio": "Granada",
        "departamento": "Granada",
        "direccion": "Entrada a Granada sobre carretera Masaya-Granada",
        "telefono": "2552-2555",
        "horario": "Atención continua 24 horas",
        "latitud": 11.9341000,
        "longitud": -85.9620000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-EST-002",
        "nombre": "Casa Materna Luz y Vida",
        "tipo_establecimiento": "casa_materna",
        "silais": "SILAIS Estelí",
        "municipio": "Estelí",
        "departamento": "Estelí",
        "direccion": "Costado este del Centro de Salud Leonel Rugama, Estelí",
        "telefono": "2713-2550",
        "horario": "Albergue y seguimiento prenatal 24 horas",
        "latitud": 13.0911000,
        "longitud": -85.3582000,
        "activo": 1,
    },
    {
        "codigo_minsa": "MINSA-MAT-001",
        "nombre": "Hospital Regional César Amador Molina",
        "tipo_establecimiento": "hospital",
        "silais": "SILAIS Matagalpa",
        "municipio": "Matagalpa",
        "departamento": "Matagalpa",
        "direccion": "Salida a Managua, Matagalpa",
        "telefono": "2772-2051",
        "horario": "Atención gineco-obstétrica 24 horas",
        "latitud": 12.9152000,
        "longitud": -85.9221000,
        "activo": 1,
    },
]


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
        """Puebla la base de datos con centros de Nicaragua y una gestante demo activa."""
        click.echo("Iniciando carga de datos reales para demostración en Nicaragua...")

        # 1. Limpiar centros basura o de prueba (ej: Fail Hospital)
        centros_basura = db.session.scalars(
            db.select(CentroAtencion).where(CentroAtencion.nombre.ilike("%fail%"))
        ).all()
        for cb in centros_basura:
            db.session.delete(cb)
        db.session.flush()

        # 2. Asegurar servicios base
        servicios_def = [
            ("Atención prenatal", "Seguimiento médico y control del embarazo."),
            ("Planificación familiar", "Orientación en salud reproductiva."),
            ("Vacunación", "Esquemas de inmunización materna y neonatal."),
            ("Atención materna y neonatal", "Parto y atención al recién nacido."),
            ("Nutrición y suplementación", "Consejería nutricional, hierro y ácido fólico."),
        ]
        servicios_db = []
        for nombre, desc in servicios_def:
            srv = db.session.scalar(db.select(Servicio).filter_by(nombre=nombre))
            if not srv:
                srv = Servicio(nombre=nombre, descripcion=desc, activo=1)
                db.session.add(srv)
                db.session.flush()
            servicios_db.append(srv)

        # 3. Insertar / Actualizar Centros de Nicaragua
        centros_creados = 0
        for datos in CENTROS_NICARAGUA:
            centro = db.session.scalar(
                db.select(CentroAtencion).filter_by(nombre=datos["nombre"])
            )
            if not centro:
                centro = CentroAtencion(**datos)
                db.session.add(centro)
                db.session.flush()
                centros_creados += 1
            else:
                for k, v in datos.items():
                    setattr(centro, k, v)
                db.session.flush()

            # Vincular servicios al centro
            for srv in servicios_db:
                existe_vinculo = db.session.scalar(
                    db.select(CentroServicio).filter_by(
                        centro_atencion_id=centro.id, servicio_id=srv.id
                    )
                )
                if not existe_vinculo:
                    db.session.add(
                        CentroServicio(
                            centro_atencion_id=centro.id,
                            servicio_id=srv.id,
                            disponible=1,
                            fecha_verificacion=date.today(),
                        )
                    )
        click.echo(f"- Directorio de centros de Nicaragua actualizado ({len(CENTROS_NICARAGUA)} centros/casas maternas asegurados).")

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
        perfil.cedula = "001-150898-1002A"
        perfil.fecha_nacimiento = date(1998, 8, 15)
        perfil.telefono = "8899-7766"
        perfil.municipio = "Managua"
        perfil.departamento = "Managua"
        perfil.direccion_residencia = "Barrio San Judas, del Ceibo 2c al sur, Managua"
        perfil.contacto_emergencia_nombre = "Carlos Alberto López (Esposo)"
        perfil.contacto_emergencia_telefono = "8765-4321"
        perfil.consentimiento_datos = 1
        perfil.fecha_consentimiento = datetime.now()
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

        # 7. Controles prenatales coherentes
        # Obtener centros de referencia para asociarlos
        hosp_bertha = db.session.scalar(
            db.select(CentroAtencion).filter_by(nombre="Hospital Bertha Calderón Roque")
        )
        cs_silvia = db.session.scalar(
            db.select(CentroAtencion).filter_by(nombre="Centro de Salud Silvia Ferrufino")
        )

        # Limpiar controles previos de la cuenta demo para no duplicar
        db.session.execute(
            db.delete(ControlPrenatal).where(ControlPrenatal.embarazo_id == embarazo.id)
        )
        db.session.flush()

        # Control 1: Realizado en semana 8
        c1 = ControlPrenatal(
            embarazo_id=embarazo.id,
            registrado_por_usuario_id=usuario_demo.id,
            numero_control=1,
            fecha_control=fum_calculada + timedelta(days=8 * 7),
            hora_control=time(9, 30),
            edad_gestacional_semanas=8.0,
            estado="realizado",
            centro_atencion_id=cs_silvia.id if cs_silvia else None,
            indicaciones="Captación temprana del embarazo. Se indican exámenes de rutina de primer trimestre (BH, EGO, VDRL, VIH, Glicemia). Se prescribe Ácido Fólico 5mg vía oral diario.",
            notas="Signos vitales normales. PA 110/70 mmHg, peso 58 kg. Paciente refiere náuseas matutinas leves.",
        )
        # Control 2: Realizado en semana 16
        c2 = ControlPrenatal(
            embarazo_id=embarazo.id,
            registrado_por_usuario_id=usuario_demo.id,
            numero_control=2,
            fecha_control=fum_calculada + timedelta(days=16 * 7),
            hora_control=time(10, 0),
            edad_gestacional_semanas=16.0,
            estado="realizado",
            centro_atencion_id=hosp_bertha.id if hosp_bertha else None,
            indicaciones="Ultrasonido estructural del segundo trimestre reporta feto único normoinserto con biometría acorde a edad gestacional. Se prescribe Sulfato Ferroso 300mg diario + Vitamina C.",
            notas="PA 110/70 mmHg, AU 15 cm, FCF 148 lpm. Movimientos fetales percibidos por la madre. Exámenes de laboratorio en rango normal.",
        )
        # Control 3: Programado para dentro de 4 días
        c3 = ControlPrenatal(
            embarazo_id=embarazo.id,
            registrado_por_usuario_id=usuario_demo.id,
            numero_control=3,
            fecha_control=hoy + timedelta(days=4),
            hora_control=time(8, 30),
            edad_gestacional_semanas=24.5,
            estado="programado",
            centro_atencion_id=hosp_bertha.id if hosp_bertha else None,
            indicaciones="Control prenatal del segundo trimestre. Acudir en ayunas para prueba de tolerancia a la glucosa oral (tamizaje de diabetes gestacional) y biometría hemática de control.",
            notas=None,
        )
        db.session.add_all([c1, c2, c3])
        db.session.flush()

        # 8. Recordatorios activos en calendario
        # Limpiar recordatorios previos de la cuenta demo
        db.session.execute(
            db.delete(Recordatorio).where(Recordatorio.usuario_id == usuario_demo.id)
        )
        db.session.flush()

        r1 = Recordatorio(
            usuario_id=usuario_demo.id,
            titulo="Tomar Sulfato Ferroso y Ácido Fólico",
            descripcion="Tomar 1 tableta diaria con agua o jugo de naranja para mejorar la absorción de hierro.",
            tipo="personal",
            fecha_hora=datetime.combine(hoy, time(14, 0)),
            estado="pendiente",
        )
        r2 = Recordatorio(
            usuario_id=usuario_demo.id,
            control_prenatal_id=c3.id,
            titulo="Cita de Control Prenatal #3 y Exámenes",
            descripcion="Asistir en ayunas al Hospital Bertha Calderón Roque para el control y la prueba de glucosa.",
            tipo="control",
            fecha_hora=datetime.combine(hoy + timedelta(days=4), time(7, 30)),
            estado="pendiente",
        )
        db.session.add_all([r1, r2])
        db.session.commit()

        click.echo("- Gestante demo configurada con éxito:")
        click.echo("  * Correo:      maria.demo@aurora.ni")
        click.echo("  * Contraseña:  Password123!")
        click.echo("  * Estado:      Semana 24 (Segundo Trimestre)")
        click.echo("  * Cédula:      001-150898-1002A")
        click.echo("  * Controles:   2 realizados + 1 próximo en Hospital Bertha Calderón")
        click.echo("  * Avisos:      2 recordatorios activos en calendario")
        click.echo("¡Datos de demostración para Nicaragua listos!")

