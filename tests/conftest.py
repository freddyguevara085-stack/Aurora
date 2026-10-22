import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key")


def _iniciar_sesion_falsa(client, monkeypatch, rol, usuario_id=7, email=None):
    from app import login_manager

    usuario = SimpleNamespace(
        id=usuario_id,
        is_authenticated=True,
        is_active=True,
        is_anonymous=False,
        email=email,
        rol=SimpleNamespace(nombre=rol),
    )
    monkeypatch.setattr(login_manager, "_user_callback", lambda _user_id: usuario)
    with client.session_transaction() as session:
        session["_user_id"] = str(usuario_id)
        session["_fresh"] = True
    return usuario


@pytest.fixture
def client():
    from app import app

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.test_client() as test_client:
        yield test_client