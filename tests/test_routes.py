from types import SimpleNamespace

from flask_login import login_user


def test_admin_requiere_autenticacion(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_usuario_comun_no_accede_a_admin(client, monkeypatch):
    from app import login_manager

    usuario = SimpleNamespace(
        id=7,
        is_authenticated=True,
        is_active=True,
        is_anonymous=False,
        rol=SimpleNamespace(nombre="usuario"),
    )
    monkeypatch.setattr(login_manager, "_user_callback", lambda _user_id: usuario)
    with client.session_transaction() as session:
        session["_user_id"] = "7"
        session["_fresh"] = True

    response = client.get("/admin/")
    assert response.status_code == 403
    assert b"Acceso denegado" in response.data


def test_registro_publico_renderiza_formulario(client):
    response = client.get("/registro")
    assert response.status_code == 200
    assert b"Crea tu cuenta" in response.data


def test_nuevo_recordatorio_requiere_autenticacion(client):
    response = client.get("/recordatorios/nuevo")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_recuperar_password_renderiza_formulario(client):
    response = client.get("/recuperar-password")
    assert response.status_code == 200
    assert b"Recupera tu contrase" in response.data


def test_recuperar_password_rechaza_correo_vacio(client):
    response = client.post("/recuperar-password", data={"email": ""})
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with client.session_transaction() as session:
        assert "Si el correo está registrado" in " ".join(session["_flashes"][0])


def test_token_de_recuperacion_reutilizado_es_rechazado(client, monkeypatch):
    from controllers.auth import _serializador_recuperacion
    from extensions import db

    usuario = type("UsuarioPrueba", (), {})()
    usuario.email = "gestante@example.com"
    usuario.password_hash = "a" * 60
    usuario.activo = 1
    monkeypatch.setattr(db.session, "scalar", lambda _query: usuario)
    monkeypatch.setattr(db.session, "commit", lambda: None)
    with client.application.app_context():
        token = _serializador_recuperacion().dumps(
            {"email": usuario.email, "pwd_stamp": usuario.password_hash[-12:]}
        )

    primera_respuesta = client.post(
        f"/restablecer-password/{token}",
        data={"password": "nueva-clave-123", "password_confirm": "nueva-clave-123"},
    )
    segunda_respuesta = client.get(f"/restablecer-password/{token}")

    assert primera_respuesta.status_code == 302
    assert segunda_respuesta.status_code == 302
    assert "/recuperar-password" in segunda_respuesta.headers["Location"]


def test_cabeceras_de_seguridad_y_hsts(client):
    response = client.get("/login")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"

    client.application.config["SESSION_COOKIE_SECURE"] = True
    secure_response = client.get("/login")
    assert secure_response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    client.application.config["SESSION_COOKIE_SECURE"] = False


def test_restablecer_password_token_invalido_redirige(client):
    response = client.get("/restablecer-password/no-es-un-token")
    assert response.status_code == 302
    assert "/recuperar-password" in response.headers["Location"]


def test_cambiar_password_requiere_autenticacion(client):
    response = client.post(
        "/perfil/cambiar-password",
        data={
            "password_actual": "secreto123",
            "password_nueva": "nuevo12345",
            "password_confirm": "nuevo12345",
        },
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]