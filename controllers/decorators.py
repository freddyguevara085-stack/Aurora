"""Decoradores y ayudantes de control de acceso compartidos.

Evita que los controladores dependan entre sí (antes ``routes`` importaba
``admin_required`` desde ``admin``). Aquí viven las reglas de rol comunes.
"""

from functools import wraps

from flask import abort, current_app
from flask_login import current_user, login_required

from demo_nicaragua import CUENTAS_DEMO_EMAILS


def admin_required(f):
    """Protege rutas exclusivas del rol administrador."""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.rol and current_user.rol.nombre == "administrador"):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def usuario_gestante() -> bool:
    """True si la cuenta autenticada tiene el rol ``usuario`` (gestante)."""
    return bool(current_user.rol and current_user.rol.nombre == "usuario")


def es_cuenta_demo() -> bool:
    """True solo para las cuentas ficticias de demostración con DEMO_MODE activo."""
    return bool(
        current_user.is_authenticated
        and current_app.config.get("DEMO_MODE")
        and (
            getattr(current_user, "email", None) in CUENTAS_DEMO_EMAILS
            or (
                getattr(current_user, "rol", None)
                and getattr(current_user.rol, "nombre", None) == "administrador"
            )
        )
    )
