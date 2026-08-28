"""Servicio para registrar eventos de auditoría en la base de datos."""

import json
from extensions import db
from models.auditoria import HistorialAuditoria


def registrar_auditoria(usuario_id, accion, entidad, registro_id=None, detalles=None, ip=None):
    """Registra una acción en la tabla historial_auditoria (añade a la sesión actual)."""
    # Excluir cualquier contraseña o dato extremadamente sensible si por accidente llega aquí
    if isinstance(detalles, dict):
        detalles = {k: v for k, v in detalles.items() if 'password' not in k.lower()}

    entrada = HistorialAuditoria(
        usuario_id=usuario_id,
        accion=accion[:50],
        entidad=entidad[:80],
        registro_id=registro_id,
        detalles=detalles if isinstance(detalles, (dict, list)) else (json.loads(detalles) if isinstance(detalles, str) else None),
        direccion_ip=ip[:45] if ip else None
    )
    db.session.add(entrada)
    return entrada
