from types import SimpleNamespace


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


def test_login_incluye_skip_link_y_foco_principal(client):
    response = client.get("/login")
    assert b'href="#main"' in response.data
    assert b'id="main"' in response.data
    assert b'aria-hidden="true">lock' in response.data


def test_inicio_publico_no_requiere_cuenta(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Informaci\xc3\xb3n p\xc3\xbablica" in response.data


def test_guia_consultable_sin_cuenta(client, monkeypatch):
    from controllers import routes

    monkeypatch.setattr(routes, "contenidos_publicados", lambda *_args, **_kwargs: [])
    response = client.get("/guia")
    assert response.status_code == 200
    assert b"Gu\xc3\xada prenatal" in response.data


def test_contenido_clinico_publicado_queda_oculto_sin_revision(client, monkeypatch):
    from datetime import date

    from extensions import db
    from models.contenido import ContenidoPrenatal, SenalAlerta

    etiqueta = "FUGA_CLINICA_DEMO_4242"
    contenido = ContenidoPrenatal(
        id=4242,
        titulo=etiqueta,
        resumen=etiqueta,
        contenido=etiqueta,
        categoria=etiqueta,
        fuente_nombre=etiqueta,
        fecha_revision=date(2026, 1, 1),
        publicado=1,
    )
    senal = SenalAlerta(
        id=4242,
        titulo=etiqueta,
        descripcion=etiqueta,
        accion_recomendada=etiqueta,
        orden_visual=1,
        fuente_nombre=etiqueta,
        fecha_revision=date(2026, 1, 1),
        activo=1,
    )
    # Simula que la base de datos contiene contenido publicado y señales activas.
    monkeypatch.setattr(
        db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: [contenido, senal])
    )
    monkeypatch.setattr(db.session, "scalar", lambda _query: contenido)

    for ruta in ("/", "/guia", f"/guia/{contenido.id}", "/alertas"):
        respuesta = client.get(ruta)
        assert respuesta.status_code in (200, 404), ruta
        assert etiqueta.encode() not in respuesta.data, ruta

    assert client.get(f"/guia/{contenido.id}").status_code == 404

    # Inicio autenticado: construir_inicio() tampoco debe devolver las filas publicadas.
    from models.usuario import Usuario
    from services import home as home_service

    monkeypatch.setattr(
        db.session,
        "get",
        lambda model, _key: SimpleNamespace(nombres="Demo") if model is Usuario else None,
    )
    monkeypatch.setattr(home_service, "perfil_y_embarazo", lambda _usuario_id: (None, None))
    monkeypatch.setattr(home_service, "recordatorios_pendientes", lambda *_args, **_kwargs: [])

    with client.application.app_context():
        inicio = home_service.construir_inicio(7)

    assert inicio["contenidos"] == []
    assert inicio["senales"] == []
    titulos_inicio = [getattr(item, "titulo", "") for item in inicio["contenidos"] + inicio["senales"]]
    assert etiqueta not in titulos_inicio

    # Las filas publicadas/activas no se modifican ni se eliminan.
    assert contenido.publicado == 1
    assert senal.activo == 1


def test_revision_clinica_requiere_cuenta(client):
    response = client.get("/demo/revision-clinica")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def _iniciar_sesion_falsa(client, monkeypatch, rol):
    from app import login_manager

    usuario = SimpleNamespace(
        id=7,
        is_authenticated=True,
        is_active=True,
        is_anonymous=False,
        rol=SimpleNamespace(nombre=rol),
    )
    monkeypatch.setattr(login_manager, "_user_callback", lambda _user_id: usuario)
    with client.session_transaction() as session:
        session["_user_id"] = "7"
        session["_fresh"] = True
    return usuario


def test_revision_clinica_rechaza_cuenta_usuario(client, monkeypatch):
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    response = client.get("/demo/revision-clinica")
    assert response.status_code == 403
    assert b"Acceso denegado" in response.data


def test_revision_clinica_permite_administrador(client, monkeypatch):
    _iniciar_sesion_falsa(client, monkeypatch, "administrador")
    response = client.get("/demo/revision-clinica")
    assert response.status_code == 200
    assert b"PENDIENTE DE REVISI\xc3\x93N CL\xc3\x8dNICA" in response.data
    assert b"NO USAR PARA ATENCI\xc3\x93N" in response.data


def test_seed_demo_bloqueado_sin_modo_demo(client):
    resultado = client.application.test_cli_runner().invoke(args=["seed-demo"])
    assert resultado.exit_code != 0
    assert "AURORA_DEMO" in resultado.output


def test_alertas_consultables_sin_cuenta(client, monkeypatch):
    from extensions import db

    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))
    response = client.get("/alertas")
    assert response.status_code == 200
    assert b"Se\xc3\xb1ales de alerta" in response.data


def test_centros_consultables_sin_cuenta(client, monkeypatch):
    from controllers import routes

    monkeypatch.setattr(routes, "centros_activos", lambda *_args: [])
    response = client.get("/centros")
    assert response.status_code == 200
    assert b"Directorio de demostraci\xc3\xb3n" in response.data


def test_fuente_solo_acepta_http_o_https():
    from controllers.admin import _url_fuente_valida

    assert _url_fuente_valida(None)
    assert _url_fuente_valida("https://salud.example.ni/guia")
    assert not _url_fuente_valida("javascript:alert(1)")
    assert not _url_fuente_valida("//example.ni/guia")
    assert not _url_fuente_valida("https://[invalid")
