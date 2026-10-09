"""Paquete del panel de administración de Aurora.

El blueprint ``admin_bp`` se define aquí y cada recurso registra sus rutas en un
módulo propio (dashboard, contenidos, señales, centros, servicios).
"""

from flask import Blueprint

from controllers.decorators import admin_required  # noqa: F401  (reexportado)
from controllers.admin._common import _url_fuente_valida  # noqa: F401  (reexportado)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Importar al final para que las rutas queden registradas en ``admin_bp``.
from controllers.admin import (  # noqa: E402,F401
    centros,
    contenidos,
    dashboard,
    senales,
    servicios,
)
