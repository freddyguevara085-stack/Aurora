"""Consultas reutilizables de las vistas funcionales del MVP."""

from datetime import date, datetime

from sqlalchemy import and_, or_, select

from extensions import db
from models.contenido import ContenidoPrenatal, SenalAlerta
from models.directorio import CentroAtencion, CentroServicio, Servicio
from models.gestacion import Embarazo, PerfilGestante
from models.seguimiento import ControlPrenatal, Recordatorio


def perfil_y_embarazo(usuario_id):
    perfil = db.session.scalar(select(PerfilGestante).where(PerfilGestante.usuario_id == usuario_id))
    embarazo = None
    if perfil:
        embarazo = db.session.scalar(select(Embarazo).where(Embarazo.perfil_gestante_id == perfil.id, Embarazo.estado == "activo").order_by(Embarazo.created_at.desc()).limit(1))
    return perfil, embarazo


def controles_activos(embarazo):
    if not embarazo:
        return []
    return db.session.scalars(select(ControlPrenatal).where(ControlPrenatal.embarazo_id == embarazo.id).order_by(ControlPrenatal.fecha_control, ControlPrenatal.hora_control)).all()


def recordatorios_pendientes(usuario_id):
    return db.session.scalars(select(Recordatorio).where(Recordatorio.usuario_id == usuario_id, Recordatorio.estado == "pendiente", Recordatorio.fecha_hora >= datetime.now()).order_by(Recordatorio.fecha_hora).limit(10)).all()


def contenidos_publicados(trimestre=None, categoria=None):
    query = select(ContenidoPrenatal).where(ContenidoPrenatal.publicado == 1)
    if trimestre in (1, 2, 3):
        query = query.where(or_(ContenidoPrenatal.trimestre.is_(None), ContenidoPrenatal.trimestre == trimestre))
    if categoria:
        query = query.where(ContenidoPrenatal.categoria == categoria)
    return db.session.scalars(query.order_by(ContenidoPrenatal.fecha_revision.desc()).limit(30)).all()


def centro_activo(centro_id):
    return db.session.scalar(select(CentroAtencion).where(CentroAtencion.id == centro_id, CentroAtencion.activo == 1))


def centros_activos(busqueda="", tipo=""):
    query = select(CentroAtencion).where(CentroAtencion.activo == 1)
    if busqueda:
        termino = f"%{busqueda[:80]}%"
        query = query.where(or_(CentroAtencion.nombre.ilike(termino), CentroAtencion.municipio.ilike(termino)))
    if tipo in {"hospital", "centro_salud", "puesto_salud", "casa_materna", "clinica", "otro"}:
        query = query.where(CentroAtencion.tipo_establecimiento == tipo)
    return db.session.scalars(query.order_by(CentroAtencion.nombre).limit(50)).all()


def servicios_disponibles(centro_id):
    return db.session.scalars(select(Servicio).join(CentroServicio).where(CentroServicio.centro_atencion_id == centro_id, CentroServicio.disponible == 1, Servicio.activo == 1).order_by(Servicio.nombre)).all()
