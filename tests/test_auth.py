"""Pruebas de autenticación, registro, recuperación de contraseña, roles y cabeceras HTTP."""

from conftest import _iniciar_sesion_falsa


def test_registro_publico_renderiza_formulario(client):
    response = client.get("/registro")
    assert response.status_code == 200
    assert b"Crea tu cuenta" in response.data


def test_base_contiene_main_y_forms_post_renderizan(client):
    # Soporte de los estados de carga (app.js): el layout debe exponer #main
    # y los formularios POST deben seguir renderizando con boton de envio.
    response = client.get("/login")
    html = response.data.decode("utf-8")
    assert response.status_code == 200
    assert 'id="main"' in html
    assert 'method="post"' in html
    assert 'type="submit"' in html


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


def test_enmascarar_email_oculta_direccion_completa():
    from controllers.auth import _enmascarar_email

    assert _enmascarar_email("gestante@example.com") == "g***e@example.com"
    assert _enmascarar_email("a@example.com") == "a***@example.com"
    assert _enmascarar_email("ab@example.com") == "a***b@example.com"
    assert "@" not in _enmascarar_email("no-es-correo")


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


def test_login_incluye_skip_link_y_foco_principal(client):
    response = client.get("/login")
    assert b'href="#main"' in response.data
    assert b'id="main"' in response.data
    assert b'aria-hidden="true">lock' in response.data


def test_logout_solo_permite_post(client, monkeypatch):
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    res_get = client.get("/logout")
    assert res_get.status_code == 405

    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    res_post = client.post("/logout")
    assert res_post.status_code == 302
    assert "/login" in res_post.headers["Location"]


def test_logout_en_perfil_usa_post_con_csrf(client, monkeypatch):
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    respuesta = client.get("/perfil")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)
    assert '<form method="post" action="/logout"' in html or 'action="/logout" method="post"' in html
    assert "csrf_token" in html
