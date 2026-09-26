"""Datos de Inicio construidos para el usuario autenticado."""

from datetime import date, timedelta

from sqlalchemy import select

from extensions import db
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

    recordatorios = recordatorios_pendientes(usuario_id, limite=3)
    contenidos = []
    senales = []

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
