"""Utilidades compartidas por los módulos del panel de administración."""

from urllib.parse import urlsplit

from flask import flash, redirect, request, url_for
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from services.auditoria import registrar_auditoria


def _url_fuente_valida(url):
    """True si la URL vacía o usa http/https con dominio."""
    if not url:
        return True
    try:
        partes = urlsplit(url)
    except ValueError:
        return False
    return partes.scheme in {"http", "https"} and bool(partes.netloc)


def _alternar(instancia, campo, entidad, etiqueta_exito, redirect_endpoint, **kwargs):
    """Cambia un campo booleano (0/1), registra auditoría y confirma."""
    nuevo_estado = 0 if getattr(instancia, campo) == 1 else 1
    setattr(instancia, campo, nuevo_estado)
    if hasattr(instancia, "actualizado_por_usuario_id"):
        instancia.actualizado_por_usuario_id = current_user.id
    try:
        registrar_auditoria(
            usuario_id=current_user.id,
            accion="cambiar_estado",
            entidad=entidad,
            registro_id=instancia.id,
            detalles={campo: nuevo_estado},
            ip=request.remote_addr,
        )
        db.session.commit()
        flash(etiqueta_exito[nuevo_estado], "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash(kwargs.get("mensaje_error", "No se pudo cambiar el estado."), "error")
    return redirect(url_for(redirect_endpoint))
