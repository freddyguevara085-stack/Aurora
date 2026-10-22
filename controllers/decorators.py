"""Decoradores y ayudantes de control de acceso compartidos.

Evita que los controladores dependan entre sí (antes ``routes`` importaba
``admin_required`` desde ``admin``). Aquí viven las reglas de rol comunes.
"""

from functools import wraps

from flask import abort
from flask_login import current_user, login_required


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
