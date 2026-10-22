"""Consultas y ensamblaje reutilizable de las vistas funcionales del MVP."""

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import OperationalError

from extensions import db
from models.contenido import ContenidoPrenatal, SenalAlerta
from models.directorio import CentroAtencion, CentroServicio, Servicio
from models.gestacion import Embarazo, PerfilGestante
from models.seguimiento import ControlPrenatal, Recordatorio


def _scalar_seguro(stmt):
    try:
        return db.session.scalar(stmt)
    except OperationalError:
        db.session.rollback()
        return None


def _scalars_seguros(stmt) -> list:
    try:
        return db.session.scalars(stmt).all()
    except OperationalError:
        db.session.rollback()
        return []


def perfil_y_embarazo(usuario_id):
    perfil = _scalar_seguro(select(PerfilGestante).where(PerfilGestante.usuario_id == usuario_id))
    embarazo = None
    if perfil:
        embarazo = _scalar_seguro(
            select(Embarazo)
            .where(Embarazo.perfil_gestante_id == perfil.id, Embarazo.estado == "activo")
            .order_by(Embarazo.created_at.desc())
            .limit(1)
        )
    return perfil, embarazo


def ultimo_embarazo_con_nacimiento(perfil_id):
    """Obtiene el último embarazo finalizado con nacimiento registrado del perfil."""
    if not perfil_id:
        return None
    return _scalar_seguro(
        select(Embarazo)
        .where(
            Embarazo.perfil_gestante_id == perfil_id,
            Embarazo.fecha_nacimiento_real.is_not(None),
        )
        .order_by(Embarazo.fecha_nacimiento_real.desc(), Embarazo.id.desc())
        .limit(1)
    )


def controles_activos(embarazo):
    if not embarazo:
        return []
    return _scalars_seguros(
        select(ControlPrenatal)
        .where(ControlPrenatal.embarazo_id == embarazo.id)
        .order_by(ControlPrenatal.fecha_control, ControlPrenatal.hora_control)
    )


def recordatorios_pendientes(usuario_id, limite=10):
    return _scalars_seguros(
        select(Recordatorio)
        .where(
            Recordatorio.usuario_id == usuario_id,
            Recordatorio.estado == "pendiente",
            Recordatorio.fecha_hora >= datetime.now(),
        )
        .order_by(Recordatorio.fecha_hora)
        .limit(limite)
    )


def contenidos_publicados(trimestre=None, categoria=None):
    """Devuelve solamente las orientaciones que administración publicó."""
    query = select(ContenidoPrenatal).where(ContenidoPrenatal.publicado == 1)
    if trimestre in (1, 2, 3):
        query = query.where(
            (ContenidoPrenatal.trimestre.is_(None))
            | (ContenidoPrenatal.trimestre == trimestre)
        )
    if categoria:
        query = query.where(ContenidoPrenatal.categoria == categoria)
    return _scalars_seguros(
        query.order_by(ContenidoPrenatal.updated_at.desc(), ContenidoPrenatal.id.desc())
    )


def ensamblar_orientaciones_guia(publicados) -> list[dict]:
    """Construye la lista de orientaciones revisadas y publicadas por administración."""
    return [
        {
            "id": f"pub-{c.id}",
            "titulo": c.titulo,
            "resumen": c.resumen or "",
            "cuerpo": c.contenido,
            "categoria": c.categoria,
            "trimestre": c.trimestre,
            "fuente_nombre": c.fuente_nombre,
            "fuente_url": c.fuente_url,
            "fecha_revision": c.fecha_revision.strftime("%d/%m/%Y") if c.fecha_revision else None,
        }
        for c in publicados
    ]


def senales_activas():
    """Devuelve las señales que administración dejó activas y ordenadas."""
    return _scalars_seguros(
        select(SenalAlerta)
        .where(SenalAlerta.activo == 1)
        .order_by(SenalAlerta.orden_visual, SenalAlerta.id)
    )


def centro_activo(centro_id):
    return _scalar_seguro(
        select(CentroAtencion).where(CentroAtencion.id == centro_id, CentroAtencion.activo == 1)
    )


def centros_activos(busqueda="", tipo=""):
    query = select(CentroAtencion).where(CentroAtencion.activo == 1)
    if busqueda:
        termino = f"%{busqueda[:80]}%"
        query = query.where(
            or_(CentroAtencion.nombre.ilike(termino), CentroAtencion.municipio.ilike(termino))
        )
    if tipo in {"hospital", "centro_salud", "puesto_salud", "casa_materna", "clinica", "otro"}:
        query = query.where(CentroAtencion.tipo_establecimiento == tipo)
    return _scalars_seguros(query.order_by(CentroAtencion.nombre).limit(1000))


def servicios_disponibles(centro_id):
    return _scalars_seguros(
        select(CentroServicio)
        .join(Servicio)
        .where(
            CentroServicio.centro_atencion_id == centro_id,
            CentroServicio.disponible == 1,
            Servicio.activo == 1,
        )
        .order_by(Servicio.nombre)
    )
