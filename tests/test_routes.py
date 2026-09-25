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
    assert response.status_code == 400
    assert b"Ingresa tu correo" in response.data


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