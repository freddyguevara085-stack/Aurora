"""Blueprints compartidos entre los controladores."""

from flask import Blueprint

# Blueprint principal: agrupa las rutas de la gestante y las públicas.
main_bp = Blueprint("main", __name__)
