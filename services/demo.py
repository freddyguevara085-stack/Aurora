"""Cuenta sintética de presentación; nunca incorpora datos de personas reales."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from werkzeug.security import generate_password_hash

from extensions import db
from models.acceso import Rol
from models.directorio import CentroAtencion
from models.gestacion import ContactoComunitario, Embarazo, PerfilGestante, PlanParto
from models.seguimiento import ControlPrenatal, PreguntaConsulta, Recordatorio
from models.usuario import Usuario

DEMO_EMAIL = 'maria.demo@example.com'


def crear_demo(password, hoy=None):
    """No duplica ni restablece una cuenta existente. El llamador confirma la transacción."""
    if len(password) < 12:
        raise ValueError('La contraseña de demostración debe tener al menos 12 caracteres.')
    existente = db.session.scalar(db.select(Usuario).filter_by(email=DEMO_EMAIL))
    if existente:
        return existente, False
    hoy = hoy or datetime.now(ZoneInfo('America/Managua')).date()
    rol = db.session.scalar(db.select(Rol).filter_by(nombre='usuario'))
    if not rol:
        rol = Rol(nombre='usuario', descripcion='Seguimiento prenatal personal')
        db.session.add(rol)
        db.session.flush()
    usuario = Usuario(rol_id=rol.id, nombres='María', apellidos='López (demostración)',
                      email=DEMO_EMAIL, password_hash=generate_password_hash(password), activo=1)
    db.session.add(usuario)
    db.session.flush()
    perfil = PerfilGestante(usuario_id=usuario.id, fecha_nacimiento=date(1999, 5, 14),
                            departamento='Managua', municipio='Managua',
                            direccion_residencia='Barrio de ejemplo · datos ficticios',
                            contacto_emergencia_nombre='Ana López · hermana (demo)',
                            consentimiento_datos=1, fecha_consentimiento=datetime.now())
    db.session.add(perfil)
    db.session.flush()
    fum = hoy - timedelta(weeks=24, days=2)
    embarazo = Embarazo(perfil_gestante_id=perfil.id, fum=fum, fpp=fum+timedelta(days=280),
                        metodo_fpp='fum', estado='activo', notas_personales='Datos ficticios para presentación.')
    db.session.add(embarazo)
    db.session.flush()
    centro = db.session.scalar(db.select(CentroAtencion).where(
        CentroAtencion.activo == 1, CentroAtencion.municipio == 'Managua',
        CentroAtencion.tipo_establecimiento == 'centro_salud').order_by(CentroAtencion.id))
    centro_id = centro.id if centro else None
    for numero, dias, estado in [(1, -84, 'realizado'), (2, -56, 'realizado'),
                                 (3, -28, 'realizado'), (4, 1, 'programado')]:
        db.session.add(ControlPrenatal(embarazo_id=embarazo.id, registrado_por_usuario_id=usuario.id,
            numero_control=numero, fecha_control=hoy+timedelta(days=dias), hora_control=time(9, 0),
            estado=estado, centro_atencion_id=centro_id,
            edad_gestacional_semanas=(170+dias)//7,
            notas='Cita ficticia para la presentación.'))
    for pregunta in ['¿Qué documentos llevo a mi próxima consulta?',
                     '¿Cómo organizo mis próximas citas?',
                     '¿Qué debo preparar para el traslado al centro?']:
        db.session.add(PreguntaConsulta(usuario_id=usuario.id, pregunta=pregunta, estado='pendiente'))
    db.session.add(ContactoComunitario(perfil_gestante_id=perfil.id,
        nombre='Ana López (demostración)', rol='vecino_apoyo', comunidad_barrio='Barrio de ejemplo',
        notas='Hermana y acompañante. Contacto ficticio; sin número telefónico.'))
    db.session.add(PlanParto(embarazo_id=embarazo.id, centro_atencion_id=centro_id,
        acompanante_nombre='Ana López (demostración)', transporte_tipo='familiar_vecino',
        transporte_contacto='Traslado familiar de ejemplo', bulto_listo=1, recursos_traslado_listos=1,
        notas='Documentos y bolso organizados. Plan ficticio para la presentación.'))
    db.session.add(Recordatorio(usuario_id=usuario.id, titulo='Preparar documentos para mi consulta',
        descripcion='Revisar mis preguntas y confirmar el traslado. Ejemplo de presentación.',
        fecha_hora=datetime.combine(hoy, time(18, 0)), tipo='personal', estado='pendiente'))
    db.session.flush()
    return usuario, True
