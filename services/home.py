"""Datos de Inicio construidos para el usuario autenticado."""

from datetime import date, timedelta

from sqlalchemy import and_, or_, select

from extensions import db
from models.contenido import ContenidoPrenatal, SenalAlerta
from models.seguimiento import ControlPrenatal
from models.usuario import Usuario
from services.mvp import perfil_y_embarazo, recordatorios_pendientes


def calcular_semana_gestacional(
    fum: date | None,
    fpp: date | None,
    hoy: date | None = None,
) -> int | None:
    """Calcula una semana visual de 0 a 42 sin valor clínico adicional."""
    hoy = hoy or date.today()
    inicio = fum or (fpp - timedelta(days=280) if fpp else None)
    if not inicio:
        return None
    return min(42, max(0, (hoy - inicio).days // 7))


def calcular_trimestre(semana: int | None) -> int | None:
    if semana is None or semana < 1:
        return None
    if semana <= 13:
        return 1
    if semana <= 27:
        return 2
    return 3


def construir_inicio(usuario_id: int) -> dict:
    """Obtiene solo los datos de Inicio asociados al usuario autenticado."""
    usuario = db.session.get(Usuario, usuario_id)
    perfil, embarazo = perfil_y_embarazo(usuario_id)

    semana = calcular_semana_gestacional(
        embarazo.fum if embarazo else None,
        embarazo.fpp if embarazo else None,
    )
    trimestre = calcular_trimestre(semana)
    hoy = date.today()
    control = None
    if embarazo:
        control = db.session.scalar(
            select(ControlPrenatal)
            .where(
                ControlPrenatal.embarazo_id == embarazo.id,
                ControlPrenatal.estado.in_(("programado", "reprogramado")),
                ControlPrenatal.fecha_control >= hoy,
            )
            .order_by(ControlPrenatal.fecha_control, ControlPrenatal.hora_control)
            .limit(1)
        )

    etapa = [ContenidoPrenatal.publicado == 1]
    if semana is None:
        etapa.extend(
            (
                ContenidoPrenatal.semana_desde.is_(None),
                ContenidoPrenatal.semana_hasta.is_(None),
                ContenidoPrenatal.trimestre.is_(None),
            )
        )
    else:
        etapa.append(
            or_(
                and_(
                    ContenidoPrenatal.semana_desde.is_(None),
                    ContenidoPrenatal.semana_hasta.is_(None),
                ),
                and_(
                    ContenidoPrenatal.semana_desde <= semana,
                    ContenidoPrenatal.semana_hasta >= semana,
                ),
            )
        )
        etapa.append(
            or_(ContenidoPrenatal.trimestre.is_(None), ContenidoPrenatal.trimestre == trimestre)
        )

    recordatorios = recordatorios_pendientes(usuario_id, limite=3)
    contenidos = db.session.scalars(
        select(ContenidoPrenatal)
        .where(*etapa)
        .order_by(ContenidoPrenatal.fecha_revision.desc())
        .limit(3)
    ).all()
    senales = db.session.scalars(
        select(SenalAlerta)
        .where(SenalAlerta.activo == 1)
        .order_by(SenalAlerta.orden_visual, SenalAlerta.id)
        .limit(3)
    ).all()

    return {
        "user_name": usuario.nombres.split()[0] if usuario and usuario.nombres else "",
        "week": semana,
        "trimester": trimestre,
        "progress": round((semana or 0) / 42 * 100) if semana is not None else None,
        "control": control,
        "recordatorios": recordatorios,
        "contenidos": contenidos,
        "senales": senales,
        "consentimiento_pendiente": bool(perfil and not perfil.consentimiento_datos),
        "empty_message": "No hay un embarazo activo asociado a esta cuenta." if not embarazo else None,
    }
