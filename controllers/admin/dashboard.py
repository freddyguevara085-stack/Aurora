"""Dashboard del panel de administración."""

from flask import render_template
from sqlalchemy import func, select

from controllers.admin import admin_bp
from controllers.decorators import admin_required
from extensions import db
from models.auditoria import HistorialAuditoria
from models.contenido import ContenidoPrenatal, SenalAlerta
from models.directorio import CentroAtencion, Servicio


@admin_bp.route("/")
@admin_required
def dashboard():
    """Vista principal del panel administrativo con métricas y accesos rápidos."""
    total_contenidos = db.session.scalar(select(func.count(ContenidoPrenatal.id))) or 0
    total_publicados = db.session.scalar(select(func.count(ContenidoPrenatal.id)).where(ContenidoPrenatal.publicado == 1)) or 0
    total_senales = db.session.scalar(select(func.count(SenalAlerta.id))) or 0
    total_senales_activas = db.session.scalar(select(func.count(SenalAlerta.id)).where(SenalAlerta.activo == 1)) or 0
    total_centros = db.session.scalar(select(func.count(CentroAtencion.id))) or 0
    total_centros_activos = db.session.scalar(select(func.count(CentroAtencion.id)).where(CentroAtencion.activo == 1)) or 0
    total_servicios = db.session.scalar(select(func.count(Servicio.id))) or 0

    ultimos_eventos = db.session.scalars(
        select(HistorialAuditoria)
        .order_by(HistorialAuditoria.created_at.desc())
        .limit(6)
    ).all()

    metricas = {
        "contenidos": total_contenidos,
        "contenidos_publicados": total_publicados,
        "senales": total_senales,
        "senales_activas": total_senales_activas,
        "centros": total_centros,
        "centros_activos": total_centros_activos,
        "servicios": total_servicios,
    }

    return render_template("admin/dashboard.html", metricas=metricas, eventos=ultimos_eventos)
