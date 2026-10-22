"""Dashboard del panel de administración."""

from flask import render_template

from controllers.admin import admin_bp
from controllers.decorators import admin_required
from services.admin import obtener_metricas_dashboard


@admin_bp.route("/")
@admin_required
def dashboard():
    """Vista principal del panel administrativo con métricas y accesos rápidos."""
    metricas, ultimos_eventos = obtener_metricas_dashboard()
    return render_template("admin/dashboard.html", metricas=metricas, eventos=ultimos_eventos)
