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


def test_base_contiene_main_y_forms_post_renderizan(client):
    # Soporte de los estados de carga (app.js): el layout debe exponer #main
    # y los formularios POST deben seguir renderizando con boton de envio.
    response = client.get("/login")
    html = response.data.decode("utf-8")
    assert response.status_code == 200
    assert 'id="main"' in html
    assert 'method="post"' in html
    assert 'type="submit"' in html


def test_nuevo_recordatorio_requiere_autenticacion(client):
    response = client.get("/recordatorios/nuevo")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_preguntas_requiere_sesion_y_rol_de_gestante(client, monkeypatch):
    assert client.get("/preguntas").status_code == 302
    _iniciar_sesion_falsa(client, monkeypatch, "administrador")
    assert client.get("/preguntas").status_code == 403


def test_alert_fab_visible_para_usuaria_no_en_alertas_ni_visitante(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))

    # Visitante sin sesion: no ve el acceso fijo.
    assert b"alert-fab" not in client.get("/login").data

    # Usuaria autenticada: visible en Inicio, ausente en Señales de alerta.
    monkeypatch.setitem(client.application.config, "DEMO_MODE", False)
    monkeypatch.setattr(
        routes,
        "construir_inicio",
        lambda _user_id: {
            "user_name": "María",
            "week": 24,
            "trimester": 2,
            "progress": 57,
            "control": None,
            "dias_para_control": None,
            "recordatorios": [],
            "contenidos": [],
            "senales": [],
            "consentimiento_pendiente": False,
            "empty_message": None,
        },
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    inicio = client.get("/")
    assert inicio.status_code == 200
    assert b"alert-fab" not in inicio.data
    assert b'href="/alertas"' in inicio.data

    alertas = client.get("/alertas")
    assert alertas.status_code == 200
    assert b"alert-fab" not in alertas.data


def test_preguntas_lista_solo_datos_de_la_cuenta(client, monkeypatch):
    from controllers import routes
    from extensions import db

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    preguntas = [
        SimpleNamespace(id=3, pregunta="¿Qué documentos llevo?", estado="pendiente"),
        SimpleNamespace(id=4, pregunta="¿Cómo consulto mi próxima cita?", estado="conversada"),
        SimpleNamespace(id=5, pregunta="<script>alert(1)</script>", estado="pendiente"),
    ]
    consultas = []

    class Resultado:
        def all(self):
            return preguntas

    def consultar(query):
        consultas.append(str(query))
        return Resultado()

    monkeypatch.setattr(db.session, "scalars", consultar)

    respuesta = client.get("/preguntas")

    assert respuesta.status_code == 200
    assert b"Qu\xc3\xa9 documentos llevo?" in respuesta.data
    assert b"C\xc3\xb3mo consulto mi pr\xc3\xb3xima cita?" in respuesta.data
    assert b"Marcar como conversada" in respuesta.data
    assert b"Volver a pendientes" in respuesta.data
    assert b"<script>alert(1)</script>" not in respuesta.data
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in respuesta.data
    assert "preguntas_consulta.usuario_id =" in consultas[0]


def test_preguntas_guardar_valida_y_asigna_la_cuenta(client, monkeypatch):
    from controllers import routes
    from extensions import db

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    agregadas = []
    monkeypatch.setattr(db.session, "add", agregadas.append)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    respuesta = client.post("/preguntas", data={"pregunta": "  ¿Qué debo recordar?  "})

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/preguntas")
    assert len(agregadas) == 1
    assert agregadas[0].usuario_id == 7
    assert agregadas[0].pregunta == "¿Qué debo recordar?"
    assert agregadas[0].estado == "pendiente"

    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))
    invalida = client.post("/preguntas", data={"pregunta": " "})
    larga = client.post("/preguntas", data={"pregunta": "x" * (routes.PREGUNTA_MAX_CARACTERES + 1)})
    assert invalida.status_code == larga.status_code == 400
    assert len(agregadas) == 1
    assert b"Escribe una pregunta" in invalida.data


def test_preguntas_conserva_el_texto_si_falla_el_guardado(client, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    from extensions import db

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)

    def fallar():
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(db.session, "commit", fallar)
    monkeypatch.setattr(db.session, "rollback", lambda: None)
    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))

    respuesta = client.post("/preguntas", data={"pregunta": "  Retomar mi próxima consulta  "})

    assert respuesta.status_code == 503
    assert b"Retomar mi pr\xc3\xb3xima consulta" in respuesta.data
    assert b"Conservamos el texto" in respuesta.data


def test_preguntas_muestra_vacio_distinto_de_pendientes_resueltas(client, monkeypatch):
    from extensions import db

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    preguntas = []
    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: preguntas))
    inicial = client.get("/preguntas")
    assert b"A\xc3\xbAn no tienes preguntas" in inicial.data

    preguntas.append(SimpleNamespace(id=4, pregunta="Pregunta resuelta", estado="conversada"))
    al_dia = client.get("/preguntas")
    assert b"Est\xc3\xa1s al d\xc3\xada" in al_dia.data
    assert b"No te quedan preguntas pendientes" in al_dia.data


def test_preguntas_no_permite_editar_pregunta_de_otra_cuenta(client, monkeypatch):
    from extensions import db

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    consultas = []

    def consultar(query):
        consultas.append(str(query))
        return None

    monkeypatch.setattr(db.session, "scalar", consultar)

    respuesta = client.post("/preguntas/99", data={"accion": "estado", "estado": "conversada"})

    assert respuesta.status_code == 404
    assert "preguntas_consulta.id =" in consultas[0]
    assert "preguntas_consulta.usuario_id =" in consultas[0]


def test_preguntas_se_pueden_marcar_y_eliminar(client, monkeypatch):
    from extensions import db

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    pregunta = SimpleNamespace(id=4, usuario_id=7, pregunta="Pregunta privada", estado="pendiente")
    monkeypatch.setattr(db.session, "scalar", lambda _query: pregunta)
    monkeypatch.setattr(db.session, "commit", lambda: None)
    eliminadas = []
    monkeypatch.setattr(db.session, "delete", eliminadas.append)

    marcada = client.post("/preguntas/4", data={"accion": "estado", "estado": "conversada"})
    assert marcada.status_code == 302
    assert pregunta.estado == "conversada"

    editada = client.post(
        "/preguntas/4",
        data={"accion": "editar", "pregunta": "  Una pregunta revisada.  "},
    )
    assert editada.status_code == 302
    assert pregunta.pregunta == "Una pregunta revisada."

    eliminada = client.post("/preguntas/4", data={"accion": "eliminar"})
    assert eliminada.status_code == 302
    assert eliminadas == [pregunta]


def test_inicio_muestra_preparacion_de_proxima_consulta(client, monkeypatch):
    from datetime import date, time, timedelta
    from types import SimpleNamespace

    from controllers import routes

    control = SimpleNamespace(
        id=4,
        fecha_control=date.today() + timedelta(days=7),
        hora_control=None,
        centro_atencion=None,
    )
    monkeypatch.setitem(client.application.config, "DEMO_MODE", False)
    monkeypatch.setattr(
        routes,
        "construir_inicio",
        lambda _user_id: {
            "user_name": "María",
            "week": 24,
            "trimester": 2,
            "progress": 57,
            "control": control,
            "dias_para_control": 7,
            "recordatorios": [],
            "contenidos": [],
            "senales": [],
            "consentimiento_pendiente": False,
            "empty_message": None,
        },
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert b"Prepara tu pr\xc3\xb3xima consulta" in respuesta.data
    assert b"/preguntas" in respuesta.data
    assert b"/consulta/preparar" in respuesta.data
    assert b"En 7 d\xc3\xadas" in respuesta.data
    assert b"Ver detalles y preparar consulta" in respuesta.data
    assert b"data-appointment-share" not in respuesta.data
    assert b"Guardar nota para mi consulta" not in respuesta.data
    assert b"Compartir es voluntario" not in respuesta.data
    assert respuesta.data.count(b'href="/calendario"') <= 1

    # Verificaciones de refactorización UI/UX en Inicio
    html = respuesta.get_data(as_text=True)
    assert "coco" in html
    assert "Semana 42" in html
    assert "Segundo trimestre" in html
    assert "Trimestre 2" not in html
    assert "Estás avanzando en la semana" not in html
    assert "home-actions" not in html
    assert "home-shortcuts-grid" in html
    assert "No hay orientación publicada por el momento" not in html
    assert "offline-note" not in html


    control.hora_control = time(9, 30)
    control.centro_atencion = SimpleNamespace(nombre="Centro Esperanza")
    respuesta = client.get("/")
    assert b"09:30" in respuesta.data
    assert b"Centro Esperanza" in respuesta.data


def test_inicio_sin_proxima_consulta_no_muestra_compartir(client, monkeypatch):
    from controllers import routes

    monkeypatch.setitem(client.application.config, "DEMO_MODE", False)
    monkeypatch.setattr(
        routes,
        "construir_inicio",
        lambda _user_id: {
            "user_name": "María",
            "week": 24,
            "trimester": 2,
            "progress": 57,
            "control": None,
            "dias_para_control": None,
            "recordatorios": [],
            "contenidos": [],
            "senales": [],
            "consentimiento_pendiente": False,
            "empty_message": None,
        },
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert b"data-appointment-share" not in respuesta.data
    assert b"data-share-action" not in respuesta.data
    assert b"data-copy-action" not in respuesta.data
    assert b"/consulta/preparar" not in respuesta.data


def test_consulta_imprimir_requiere_autenticacion(client):
    respuesta = client.get("/consulta/imprimir")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_detalle_consulta_muestra_compartir_y_acceso_a_preguntas(client, monkeypatch):
    from datetime import date, time
    from types import SimpleNamespace

    from controllers import routes

    control = SimpleNamespace(
        fecha_control=date(2026, 10, 12),
        hora_control=time(9, 30),
        centro_atencion=SimpleNamespace(nombre="Centro Esperanza"),
    )
    monkeypatch.setattr(routes, "construir_inicio", lambda _user_id: {"control": control})
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    respuesta = client.get("/consulta/preparar")

    assert respuesta.status_code == 200
    assert b"12/10/2026" in respuesta.data
    assert b"09:30" in respuesta.data
    assert b"Centro Esperanza" in respuesta.data
    assert b"data-appointment-share" in respuesta.data
    assert b"Compartir cita" in respuesta.data
    assert b"Copiar datos de la cita" in respuesta.data
    assert b"Tus preguntas personales no se incluyen" in respuesta.data
    assert b"/preguntas" in respuesta.data
    assert b"/consulta/imprimir" in respuesta.data


def test_detalle_consulta_requiere_autenticacion(client):
    respuesta = client.get("/consulta/preparar")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_hoja_impresa_incluye_logistica_y_preguntas_pendientes(client, monkeypatch):
    from datetime import date, time
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    control = SimpleNamespace(
        fecha_control=date(2026, 10, 12),
        hora_control=time(9, 30),
        centro_atencion=SimpleNamespace(nombre="Centro Esperanza"),
        notas="SECRETO_NOTA_4242",
    )
    preguntas = [SimpleNamespace(pregunta="¿Qué debo llevar a la consulta?")]
    monkeypatch.setattr(routes, "construir_inicio", lambda _user_id: {"control": control})
    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: preguntas))
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    respuesta = client.get("/consulta/imprimir")

    assert respuesta.status_code == 200
    assert b"12/10/2026" in respuesta.data
    assert b"09:30" in respuesta.data
    assert b"Centro Esperanza" in respuesta.data
    assert b"Qu\xc3\xa9 debo llevar a la consulta?" in respuesta.data
    assert b"SECRETO_NOTA_4242" not in respuesta.data
    assert b"data-print-action" in respuesta.data
    assert b"puede imprimirlas o guardarlas" in respuesta.data
    assert b"data-appointment-share" not in respuesta.data
    assert b"data-share-action" not in respuesta.data
    assert b"Se\xc3\xb1ales de alerta" not in respuesta.data


def test_hoja_impresa_sin_cita_redirige(client, monkeypatch):
    from controllers import routes

    monkeypatch.setitem(client.application.config, "DEMO_MODE", False)
    monkeypatch.setattr(
        routes,
        "construir_inicio",
        lambda _user_id: {
            "user_name": "María",
            "week": 24,
            "trimester": 2,
            "progress": 57,
            "control": None,
            "dias_para_control": None,
            "recordatorios": [],
            "contenidos": [],
            "senales": [],
            "consentimiento_pendiente": False,
            "empty_message": None,
        },
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    respuesta = client.get("/consulta/imprimir", follow_redirects=True)

    assert respuesta.status_code == 200
    assert b"/consulta/imprimir" not in respuesta.data
    assert b"data-print-action" not in respuesta.data


def test_hoja_impresa_no_incluye_notas_de_control_ni_parametros(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    control = SimpleNamespace(
        fecha_control=date(2026, 10, 12),
        hora_control=None,
        centro_atencion=None,
        notas="SECRETO_REAL_7979",
    )
    monkeypatch.setattr(routes, "construir_inicio", lambda _user_id: {"control": control})
    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")

    respuesta = client.get("/consulta/imprimir?nota=INYECTADA")

    assert respuesta.status_code == 200
    assert b"INYECTADA" not in respuesta.data
    assert b"SECRETO_REAL_7979" not in respuesta.data


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


def test_inicio_publico_no_requiere_cuenta(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Organiza tu" in response.data
    assert b"atenci\xc3\xb3n prenatal." in response.data
    assert b"no es un servicio m\xc3\xa9dico" in response.data


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


def test_seed_demo_bloqueado_sin_modo_demo(client, monkeypatch):
    monkeypatch.setitem(client.application.config, "DEMO_MODE", False)
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


def test_seguimientos_clinicos_no_forman_parte_del_mvp(client):
    for ruta in (
        "/preeclampsia",
        "/preeclampsia/seguimiento",
        "/preeclampsia/seguimiento/registros",
        "/puerperio",
        "/puerperio/imprimir",
    ):
        assert client.get(ruta).status_code == 404, ruta


def test_calendario_oculta_nuevo_recordatorio_a_administradores(client, monkeypatch):
    from controllers import routes

    _iniciar_sesion_falsa(client, monkeypatch, "administrador")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, None))
    monkeypatch.setattr(routes, "recordatorios_pendientes", lambda *_args, **_kwargs: [])

    respuesta = client.get("/calendario")

    assert respuesta.status_code == 200
    assert b"/recordatorios/nuevo" not in respuesta.data


def test_guia_muestra_borradores_solo_a_cuentas_demo(client, monkeypatch):
    from controllers import routes
    from demo_nicaragua import BORRADORES, CUENTA_DEMO_EMAIL, CUENTAS_DEMO_EMAILS

    monkeypatch.setitem(client.application.config, "DEMO_MODE", True)
    assert all(item["fuente"].startswith("minsa_") for item in BORRADORES)

    publica = client.get("/guia")
    assert b"Borrador de demostraci" not in publica.data

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", email=CUENTA_DEMO_EMAIL)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, None))
    demo = client.get("/guia")
    assert "Borrador de demostraci".encode() in demo.data
    assert b'data-trimestre="1"' in demo.data
    assert b'data-trimestre="3"' in demo.data
    for borrador in BORRADORES:
        assert borrador["titulo"].encode() in demo.data
        assert borrador["texto"].encode() in demo.data

    email_demo_adicional = next(email for email in CUENTAS_DEMO_EMAILS if email != CUENTA_DEMO_EMAIL)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=8, email=email_demo_adicional)
    assert b"Borrador de demostraci" in client.get("/guia").data

    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=9, email="persona@example.com")
    normal = client.get("/guia")
    assert "Borrador de demostraci".encode() not in normal.data


def test_fuentes_muestra_solo_fuentes_minsa_recientes(client):
    respuesta = client.get("/fuentes")
    assert respuesta.status_code == 200
    assert b"Fuentes consultadas" in respuesta.data
    assert b"MINSA - Actividades B\xc3\xa1sicas durante la Atenci\xc3\xb3n Prenatal (2022)" in respuesta.data
    assert b"paho.org" not in respuesta.data
    assert b"revisi" in respuesta.data.lower()


def test_confirmacion_eliminar_usa_dialogo_accesible():
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    base = (raiz / "templates" / "admin" / "base_admin.html").read_text(encoding="utf-8")
    assert "<dialog" in base
    assert 'id="aurora-confirm"' in base
    for nombre in ("centros", "contenidos", "senales", "servicios"):
        html = (raiz / "templates" / "admin" / nombre / "index.html").read_text(encoding="utf-8")
        assert "confirm(" not in html, nombre
        assert "data-confirm=" in html, nombre


def test_plan_parto_requiere_autenticacion_y_rol_gestante(client, monkeypatch):
    sin_sesion = client.get("/plan-parto")
    assert sin_sesion.status_code == 302
    assert "/login" in sin_sesion.headers["Location"]

    _iniciar_sesion_falsa(client, monkeypatch, "administrador")
    assert client.get("/plan-parto").status_code == 403


def test_plan_parto_sin_embarazo_redirige(client, monkeypatch):
    from controllers import routes

    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, None))

    respuesta = client.get("/plan-parto")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/embarazo")


def test_guardar_y_editar_plan_parto(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    embarazo = SimpleNamespace(id=11, plan_parto=None)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda *_args: [])
    agregados = []
    monkeypatch.setattr(db.session, "add", agregados.append)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    respuesta = client.post(
        "/plan-parto",
        data={
            "acompanante_nombre": "  Rosa Guevara  ",
            "transporte_tipo": "caponera_taxi",
            "transporte_contacto": "Don Carlos - 8777-1111",
            "bulto_listo": "1",
            "notas": "  Llevar tarjeta del MINSA  ",
        },
    )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/plan-parto")
    assert len(agregados) == 1
    plan = agregados[0]
    assert plan.embarazo_id == 11
    assert plan.acompanante_nombre == "Rosa Guevara"
    assert plan.transporte_tipo == "caponera_taxi"
    assert plan.bulto_listo == 1
    assert plan.recursos_traslado_listos == 0
    assert plan.notas == "Llevar tarjeta del MINSA"

    embarazo.plan_parto = plan
    vista = client.get("/plan-parto")
    assert vista.status_code == 200
    assert b"Rosa Guevara" in vista.data
    assert b"Don Carlos" in vista.data
    assert b"Taxi o caponera local" in vista.data


def test_plan_parto_rechaza_transporte_invalido(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes

    embarazo = SimpleNamespace(id=11, plan_parto=None)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda *_args: [])

    respuesta = client.post("/plan-parto", data={"transporte_tipo": "avion"})

    assert respuesta.status_code == 200
    assert "Selecciona un medio de transporte válido".encode() in respuesta.data


def test_plan_parto_rechaza_centro_invalido_sin_error_500(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes

    embarazo = SimpleNamespace(id=11, plan_parto=None)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda *_args: [])
    monkeypatch.setattr(routes, "centro_activo", lambda _centro_id: None)

    malformado = client.post("/plan-parto", data={"centro_atencion_id": "no-es-id"})
    inexistente = client.post("/plan-parto", data={"centro_atencion_id": "999"})

    assert malformado.status_code == 200
    assert inexistente.status_code == 200
    assert "El centro de atención seleccionado no es válido".encode() in malformado.data
    assert "El centro de atención seleccionado no es válido".encode() in inexistente.data


def test_plan_parto_resumen_elementos_tactiles_y_preparativos(client, monkeypatch):
    from types import SimpleNamespace
    from controllers import routes

    plan = SimpleNamespace(
        centro_atencion=SimpleNamespace(nombre="Centro de Salud Demo"),
        requiere_casa_materna=0,
        acompanante_nombre="Rosa Guevara",
        acompanante_telefono="8888-1234",
        cuidador_hijos="Vecina Julia",
        transporte_tipo="ambulancia",
        transporte_contacto="8777-5678",
        bulto_listo=1,
        recursos_traslado_listos=1,
        notas="Documentos listos",
    )
    embarazo = SimpleNamespace(id=11, plan_parto=plan)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, embarazo))

    vista = client.get("/plan-parto")

    assert vista.status_code == 200
    assert b'href="tel:8888-1234"' in vista.data
    assert b'href="tel:8777-5678"' in vista.data
    assert b"btn-call-action" in vista.data
    assert b"card-icon-box" in vista.data
    assert b"badge-familiar" in vista.data
    assert b"badge-transporte" in vista.data
    assert b"plan-checklist" in vista.data
    assert "Tarjeta de control prenatal del MINSA y ropa de recién nacido limpia".encode() in vista.data
    assert "Bulto o mochila listo".encode() in vista.data
    assert "Recursos para el traslado disponibles".encode() in vista.data
    assert b"Editar plan" in vista.data
    assert "Ver ficha para el hogar / Imprimir".encode() in vista.data


def test_imprimir_plan_parto_muestra_ficha_familiar(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    from controllers import routes

    plan = SimpleNamespace(
        centro_atencion=SimpleNamespace(nombre="Hospital Demo"),
        acompanante_nombre="Rosa Guevara",
        acompanante_telefono="8888-0000",
        transporte_tipo="caponera_taxi",
        transporte_contacto="Don Carlos - 8777-1111",
        cuidador_hijos="Abuela materna",
        requiere_casa_materna=1,
        bulto_listo=1,
        recursos_traslado_listos=1,
        notas="Llevar tarjeta del MINSA",
    )
    embarazo = SimpleNamespace(
        id=11,
        plan_parto=plan,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, embarazo))

    respuesta = client.get("/plan-parto/imprimir")

    assert respuesta.status_code == 200
    assert b"Rosa Guevara" in respuesta.data
    assert b"8888-0000" in respuesta.data
    assert b"Taxi o caponera local" in respuesta.data
    assert b"Hospital Demo" in respuesta.data
    assert b"documentos de control prenatal" in respuesta.data
    assert b"data-print-action" in respuesta.data


def test_imprimir_plan_parto_sin_plan_redirige(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes

    embarazo = SimpleNamespace(id=11, plan_parto=None, fum=None, fpp=None)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (None, embarazo))

    respuesta = client.get("/plan-parto/imprimir")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/plan-parto")


# --- Red personal de apoyo -------------------------------------------------


def test_red_comunitaria_requiere_autenticacion_y_rol_gestante(client, monkeypatch):
    sin_sesion = client.get("/red-comunitaria")
    assert sin_sesion.status_code == 302
    assert "/login" in sin_sesion.headers["Location"]

    _iniciar_sesion_falsa(client, monkeypatch, "administrador")
    assert client.get("/red-comunitaria").status_code == 403
    assert client.get("/red-comunitaria/nuevo").status_code == 403
    assert client.post("/red-comunitaria/1/eliminar").status_code == 403


def test_red_comunitaria_renderiza_solo_contactos_confirmados(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes

    contactos = [
        SimpleNamespace(
            id=1,
            nombre="Doña Silvia Martínez",
            rol="brigadista",
            telefono="8888-2345",
            comunidad_barrio="Barrio Jorge Smith",
            notas="Enlace con el centro de salud municipal",
        ),
    ]
    perfil = SimpleNamespace(id=5, contactos_comunitarios=contactos)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))

    respuesta = client.get("/red-comunitaria")

    assert respuesta.status_code == 200
    assert "Doña Silvia Martínez".encode() in respuesta.data
    assert b"Contacto comunitario" in respuesta.data
    assert b"tel:8888-2345" in respuesta.data
    assert b"Barrio Jorge Smith" in respuesta.data
    assert b"Enlace con el centro de salud municipal" in respuesta.data
    assert b"Luz Divina" not in respuesta.data
    assert b"tel:102" not in respuesta.data
    assert b"/red-comunitaria/nuevo" in respuesta.data
    assert b"/red-comunitaria/1/editar" in respuesta.data
    assert b"/red-comunitaria/1/eliminar" in respuesta.data


def test_red_comunitaria_estado_vacio_guia_a_registrar(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes

    perfil = SimpleNamespace(id=5, contactos_comunitarios=[])
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))
    respuesta = client.get("/red-comunitaria")

    assert respuesta.status_code == 200
    assert "Aún no registras tu red de apoyo".encode() in respuesta.data
    assert b"Agregar mi primer contacto" in respuesta.data


def test_crear_contacto_comunitario_exitoso(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    perfil = SimpleNamespace(id=5)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))
    agregados = []
    monkeypatch.setattr(db.session, "add", agregados.append)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    respuesta = client.post(
        "/red-comunitaria/nuevo",
        data={
            "nombre": "  Don Pedro Fonseca  ",
            "rol": "traslado_local",
            "telefono": "8765-4321",
            "comunidad_barrio": "Sector San Antonio",
            "notas": "  Camioneta disponible para traslado  ",
        },
    )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/red-comunitaria")
    assert len(agregados) == 1
    contacto = agregados[0]
    assert contacto.perfil_gestante_id == 5
    assert contacto.nombre == "Don Pedro Fonseca"
    assert contacto.rol == "traslado_local"
    assert contacto.telefono == "8765-4321"
    assert contacto.comunidad_barrio == "Sector San Antonio"
    assert contacto.notas == "Camioneta disponible para traslado"


def test_crear_contacto_comunitario_valida_campos(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    perfil = SimpleNamespace(id=5)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))
    agregados = []
    monkeypatch.setattr(db.session, "add", agregados.append)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    vacio = client.post("/red-comunitaria/nuevo", data={"nombre": "  ", "rol": "brigadista"})
    rol_invalido = client.post(
        "/red-comunitaria/nuevo", data={"nombre": "Ana", "rol": "inventado"}
    )
    nombre_largo = client.post(
        "/red-comunitaria/nuevo", data={"nombre": "x" * 151, "rol": "brigadista"}
    )
    tel_largo = client.post(
        "/red-comunitaria/nuevo",
        data={"nombre": "Ana", "rol": "brigadista", "telefono": "9" * 31},
    )

    for respuesta in (vacio, rol_invalido, nombre_largo, tel_largo):
        assert respuesta.status_code == 200
        assert b"Revisa el nombre" in respuesta.data
    assert agregados == []


def test_editar_contacto_comunitario_propio(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    contacto = SimpleNamespace(
        id=3,
        nombre="Doña Silvia",
        rol="brigadista",
        telefono="8888-2345",
        comunidad_barrio="Barrio Jorge Smith",
        notas="Enlace",
    )
    perfil = SimpleNamespace(id=5)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))
    monkeypatch.setattr(db.session, "scalar", lambda _query: contacto)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    respuesta = client.post(
        "/red-comunitaria/3/editar",
        data={
            "nombre": "  Doña Silvia Martínez  ",
            "rol": "partera",
            "telefono": "8888-1111",
            "comunidad_barrio": "Barrio Nuevo",
            "notas": " ",
        },
    )

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/red-comunitaria")
    assert contacto.nombre == "Doña Silvia Martínez"
    assert contacto.rol == "partera"
    assert contacto.telefono == "8888-1111"
    assert contacto.comunidad_barrio == "Barrio Nuevo"
    assert contacto.notas is None


def test_editar_contacto_de_otra_cuenta_da_404(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    perfil = SimpleNamespace(id=5)
    consultas = []
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))

    def consultar(query):
        consultas.append(str(query))
        return None

    monkeypatch.setattr(db.session, "scalar", consultar)

    respuesta = client.get("/red-comunitaria/99/editar")

    assert respuesta.status_code == 404
    assert "contactos_comunitarios.id =" in consultas[0]
    assert "contactos_comunitarios.perfil_gestante_id =" in consultas[0]


def test_eliminar_contacto_comunitario(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    contacto = SimpleNamespace(id=3, nombre="Doña Silvia")
    perfil = SimpleNamespace(id=5)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))
    monkeypatch.setattr(db.session, "scalar", lambda _query: contacto)
    eliminados = []
    monkeypatch.setattr(db.session, "delete", eliminados.append)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    respuesta = client.post("/red-comunitaria/3/eliminar")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/red-comunitaria")
    assert eliminados == [contacto]


def test_eliminar_contacto_de_otra_cuenta_da_404(client, monkeypatch):
    from types import SimpleNamespace

    from controllers import routes
    from extensions import db

    perfil = SimpleNamespace(id=5)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, None))
    monkeypatch.setattr(db.session, "scalar", lambda _query: None)

    respuesta = client.post("/red-comunitaria/99/eliminar")

    assert respuesta.status_code == 404


def test_ficha_impreso_incluye_contactos_comunitarios(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    from controllers import routes

    plan = SimpleNamespace(
        centro_atencion=None,
        acompanante_nombre="Rosa Guevara",
        acompanante_telefono="8888-0000",
        transporte_tipo="caponera_taxi",
        transporte_contacto="Don Carlos - 8777-1111",
        cuidador_hijos="Abuela materna",
        requiere_casa_materna=0,
        bulto_listo=1,
        recursos_traslado_listos=1,
        notas=None,
    )
    contacto = SimpleNamespace(
        nombre="Doña Silvia Martínez",
        rol="brigadista",
        telefono="8888-2345",
    )
    perfil = SimpleNamespace(contactos_comunitarios=[contacto])
    embarazo = SimpleNamespace(
        id=11,
        plan_parto=plan,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, embarazo))

    respuesta = client.get("/plan-parto/imprimir")

    assert respuesta.status_code == 200
    assert "Contactos de apoyo".encode() in respuesta.data
    assert "Doña Silvia Martínez".encode() in respuesta.data
    assert b"Contacto comunitario" in respuesta.data
    assert b"8888-2345" in respuesta.data


def test_ficha_impresa_sin_contactos_no_muestra_red_de_apoyo(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    from controllers import routes

    plan = SimpleNamespace(
        centro_atencion=None,
        acompanante_nombre=None,
        acompanante_telefono=None,
        transporte_tipo="propio",
        transporte_contacto=None,
        cuidador_hijos=None,
        requiere_casa_materna=0,
        bulto_listo=0,
        recursos_traslado_listos=0,
        notas=None,
    )
    perfil = SimpleNamespace(contactos_comunitarios=[])
    embarazo = SimpleNamespace(
        id=11,
        plan_parto=plan,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, embarazo))

    respuesta = client.get("/plan-parto/imprimir")

    assert respuesta.status_code == 200
    assert "Contactos de apoyo".encode() not in respuesta.data


def test_embarazo_vista_refactorizada_ui(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    from controllers import routes

    perfil = SimpleNamespace(id=1, contactos_comunitarios=[])
    embarazo = SimpleNamespace(
        id=11,
        perfil_gestante_id=1,
        plan_parto=None,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, embarazo))
    monkeypatch.setattr(routes, "controles_activos", lambda _embarazo: [])

    respuesta = client.get("/embarazo")

    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # 1. Cabecera limpia sin flecha de retroceso
    assert 'class="pregnancy-header"' in html
    assert '<h1>Mi embarazo</h1>' not in html or 'pregnancy-header__title">Mi embarazo</h1>' in html
    assert 'arrow_back' not in html

    # 2. Anillo SVG de progreso gestacional y escala a 42 semanas
    assert 'class="gestational-ring"' in html
    assert 'aria-valuemax="42"' in html
    assert 'Semana 42' in html
    assert 'de 42' not in html

    # 3. Enlace integrado "Editar datos" en la tarjeta y sin botón huérfano
    assert "card-header__link" in html
    assert "Editar datos ›" in html
    assert "pregnancy-edit-link" not in html
    assert "Tu etapa" not in html

    # 4. Jerarquía de acciones táctiles y enlaces ghost
    assert "Registrar control" in html
    assert "action-ghost" in html
    assert "Ver historial" in html
    assert "Mis preguntas" in html

    # En modo edición, debe conservar la navegación de cancelación
    respuesta_edit = client.get("/embarazo?editar=1")
    assert respuesta_edit.status_code == 200
    html_edit = respuesta_edit.get_data(as_text=True)
    assert "arrow_back" in html_edit
    assert "Editar embarazo" in html_edit


def test_perfil_vista_refactorizada_ui(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes

    perfil = SimpleNamespace(
        id=1,
        cedula="001-010190-0001A",
        municipio="Matagalpa",
        departamento="Matagalpa",
        fecha_nacimiento=date(1995, 5, 20),
        telefono="8888-1234",
        direccion_residencia="Barrio San José",
        contacto_emergencia_nombre="Carlos Ruiz",
        contacto_emergencia_telefono="8765-4321",
        consentimiento_datos=1,
    )
    embarazo = SimpleNamespace(
        id=11,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    usuario = _iniciar_sesion_falsa(client, monkeypatch, "usuario", email="maria.demo@aurora.ni")
    usuario.nombres = "María"
    usuario.apellidos = "González"
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _usuario_id: (perfil, embarazo))

    respuesta = client.get("/perfil")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # 1. Cabecera limpia sin flecha de retroceso (es vista raíz del Bottom Navigation)
    assert "arrow_back" not in html
    assert 'class="profile-avatar"' in html
    assert 'class="profile-name"' in html
    assert 'class="profile-email"' in html

    # 2. Ficha de la gestante: datos clave y acción única de edición al pie
    assert "Ficha de la gestante" in html
    assert "Cédula" in html
    assert "Municipio / Depto." in html
    assert "Semana de gestación" in html
    assert "Editar información personal y médica" in html

    # 3. Tarjetas de Ajustes estándar (Grouped lists)
    assert "Cuenta y accesibilidad" in html
    assert "Cambiar contraseña" in html
    assert "Tamaño de texto" in html
    assert "Información y legal" in html
    assert "Fuentes oficiales" in html
    assert "Privacidad de datos" in html
    assert "Acerca de Aurora" in html

    # 4. Botón de cerrar sesión seguro y ergonómico
    assert 'class="btn-logout"' in html
    assert "Cerrar sesión" in html


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


def test_nuevo_control_vista_refactorizada_ui(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes

    embarazo = SimpleNamespace(
        id=11,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: [])

    respuesta = client.get("/controles/nuevo")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # 1. Cabecera y salida accesible
    assert "Volver a mis controles" in html
    assert "Agendar nuevo control" in html

    # 2. Número correlativo y tipo de control visual
    assert "Control N.º" in html
    assert "Control prenatal regular" in html
    assert "Ultrasonido / Ecografía" in html
    assert "Exámenes de laboratorio" in html

    # 3. Fecha y hora en 2 columnas, y nota gestacional reactiva
    assert 'id="fecha_control"' in html
    assert 'id="hora_control"' in html
    assert 'id="calc-gestacional-note"' in html

    # 4. Empatía en notas: preguntas previas, SIN notas post-consulta en creación
    assert "Preguntas o notas para la consulta" in html
    assert "Anota aquí dudas sobre síntomas o alimentos" in html
    assert "Notas post-consulta" not in html

    # 5. Jerarquía de acciones al pie
    assert "Guardar control" in html
    assert "Cancelar" in html


def test_nuevo_control_creacion_automatiza_numero_y_edad(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes
    from extensions import db

    embarazo = SimpleNamespace(
        id=11,
        fum=date(2026, 4, 1),
        fpp=date(2027, 1, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario", usuario_id=7)
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: [])

    agregados = []
    monkeypatch.setattr(db.session, "add", agregados.append)
    monkeypatch.setattr(db.session, "commit", lambda: None)
    monkeypatch.setattr(db.session, "scalar", lambda _q: 2)  # último número existente = 2

    respuesta = client.post("/controles/nuevo", data={
        "fecha_control": "2026-10-15",
        "hora_control": "09:00",
        "tipo_control": "Ultrasonido / Ecografía",
        "indicaciones": "¿El bebé está en buena posición?",
    })

    assert respuesta.status_code == 302
    assert len(agregados) == 1
    control = agregados[0]
    # Número sugerido automático = último número (2) + 1 = 3, sin huecos
    assert control.numero_control == 3
    # Tipo guardado como prefijo
    assert "[Ultrasonido / Ecografía]" in control.indicaciones
    assert "¿El bebé está en buena posición?" in control.indicaciones
    # Edad gestacional calculada automáticamente
    assert control.edad_gestacional_semanas is not None
    assert control.edad_gestacional_semanas > 0


def test_editar_control_muestra_notas_post_consulta_solo_si_realizado(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes

    embarazo = SimpleNamespace(id=11, fum=date(2026, 4, 1), fpp=date(2027, 1, 6), metodo_fpp="fum")
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: [])

    # Control programado
    control_prog = SimpleNamespace(
        id=5,
        embarazo_id=11,
        numero_control=2,
        fecha_control=date(2026, 10, 20),
        hora_control=None,
        estado="programado",
        centro_atencion_id=None,
        indicaciones="[Ultrasonido / Ecografía] Dudas",
        notas=None,
        edad_gestacional_semanas=28.0,
    )
    from extensions import db
    monkeypatch.setattr(db.session, "scalar", lambda _q: control_prog)

    res_prog = client.get("/controles/5/editar")
    assert res_prog.status_code == 200
    html_prog = res_prog.get_data(as_text=True)
    assert "Notas post-consulta" not in html_prog

    # Control realizado
    control_real = SimpleNamespace(
        id=6,
        embarazo_id=11,
        numero_control=1,
        fecha_control=date(2026, 8, 10),
        hora_control=None,
        estado="realizado",
        centro_atencion_id=None,
        indicaciones="Control inicial",
        notas="Se recomendó ácido fólico",
        edad_gestacional_semanas=18.0,
    )
    monkeypatch.setattr(db.session, "scalar", lambda _q: control_real)

    res_real = client.get("/controles/6/editar")
    assert res_real.status_code == 200
    html_real = res_real.get_data(as_text=True)
    assert "Notas post-consulta" in html_real


def test_nuevo_control_datalist_centros_ui(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes

    perfil = SimpleNamespace(id=1, departamento="Matagalpa", municipio="Matagalpa")
    embarazo = SimpleNamespace(id=11, fum=date(2026, 4, 1), fpp=date(2027, 1, 6), metodo_fpp="fum")
    centros = [
        SimpleNamespace(id=101, nombre="Centro de Salud San Juan", departamento="Matagalpa", municipio="Matagalpa"),
        SimpleNamespace(id=102, nombre="Hospital Escuela César Amador Molina", departamento="Matagalpa", municipio="Matagalpa"),
        SimpleNamespace(id=201, nombre="Hospital Bertha Calderón", departamento="Managua", municipio="Managua"),
    ]

    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (perfil, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: centros)

    respuesta = client.get("/controles/nuevo")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # 1. Campo de texto asistido con datalist nativo y placeholder conciso
    assert 'id="centro_atencion_input"' in html
    assert 'name="centro_nombre_input"' in html
    assert 'list="centros_sugeridos"' in html
    assert '<datalist id="centros_sugeridos">' in html
    assert 'placeholder="Buscar centro o puesto local..."' in html
    assert 'class="form-hint">Escribe tu puesto local si no aparece en la lista.</span>' in html

    # 2. Opciones sugeridas con nombre y municipio
    assert 'value="Centro de Salud San Juan (Matagalpa)"' in html
    assert 'value="Hospital Bertha Calderón (Managua)"' in html

    # 3. Se eliminó el <select> rígido y el contenedor condicional huérfano
    assert '<select id="centro_atencion_id"' not in html
    assert 'id="wrap-otro-centro"' not in html

    # 4. Botón secundario Cancelar con estilo ghost y redirección a controles
    assert 'button--ghost' in html
    assert 'href="/controles"' in html


def test_nuevo_control_guarda_centro_registrado_por_nombre(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes
    from extensions import db

    embarazo = SimpleNamespace(id=11, fum=date(2026, 4, 1), fpp=date(2027, 1, 6), metodo_fpp="fum")
    centros = [
        SimpleNamespace(id=101, nombre="Centro de Salud San Juan", departamento="Matagalpa", municipio="Matagalpa"),
    ]

    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: centros)

    agregados = []
    monkeypatch.setattr(db.session, "add", lambda item: agregados.append(item))
    monkeypatch.setattr(db.session, "commit", lambda: None)
    monkeypatch.setattr(db.session, "scalar", lambda _q: 0)

    respuesta = client.post("/controles/nuevo", data={
        "fecha_control": "2026-10-25",
        "hora_control": "10:00",
        "tipo_control": "Control prenatal regular",
        "centro_nombre_input": "Centro de Salud San Juan (Matagalpa)",
        "indicaciones": "¿Qué exámenes necesito?",
    })

    assert respuesta.status_code == 302
    assert len(agregados) == 1
    control = agregados[0]
    # Se vinculó automáticamente al ID del centro existente
    assert control.centro_atencion_id == 101
    assert "[Centro:" not in (control.indicaciones or "")
    assert "¿Qué exámenes necesito?" in control.indicaciones


def test_nuevo_control_guardar_puesto_comunitario_libre(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes
    from extensions import db

    embarazo = SimpleNamespace(id=11, fum=date(2026, 4, 1), fpp=date(2027, 1, 6), metodo_fpp="fum")
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: [])

    agregados = []
    monkeypatch.setattr(db.session, "add", lambda item: agregados.append(item))
    monkeypatch.setattr(db.session, "commit", lambda: None)
    monkeypatch.setattr(db.session, "scalar", lambda _q: 0)

    respuesta = client.post("/controles/nuevo", data={
        "fecha_control": "2026-10-25",
        "hora_control": "10:00",
        "tipo_control": "Control prenatal regular",
        "centro_nombre_input": "Puesto de Salud El Chile",
        "indicaciones": "¿Es normal tener dolor en la espalda baja?",
    })

    assert respuesta.status_code == 302
    assert len(agregados) == 1
    control = agregados[0]
    # No viola clave foránea al guardar None en centro_atencion_id
    assert control.centro_atencion_id is None
    # Guarda el nombre personalizado en indicaciones con formato limpio
    assert "[Centro: Puesto de Salud El Chile]" in control.indicaciones
    assert "¿Es normal tener dolor en la espalda baja?" in control.indicaciones
    # La propiedad helper centro_nombre lo resuelve perfectamente
    assert control.centro_nombre == "Puesto de Salud El Chile"


def test_editar_control_con_puesto_comunitario_prellena_input_y_limpia_textarea(client, monkeypatch):
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes
    from extensions import db
    from models.seguimiento import ControlPrenatal

    embarazo = SimpleNamespace(id=11, fum=date(2026, 4, 1), fpp=date(2027, 1, 6), metodo_fpp="fum")
    control = ControlPrenatal(
        id=7,
        embarazo_id=11,
        numero_control=2,
        fecha_control=date(2026, 11, 5),
        hora_control=None,
        estado="programado",
        centro_atencion_id=None,
        indicaciones="[Ultrasonido / Ecografía] [Centro: Puesto de Salud Comunitario San Rafael] Revisar crecimiento fetal",
        notas=None,
        edad_gestacional_semanas=31.0,
    )

    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "centros_activos", lambda: [])
    monkeypatch.setattr(db.session, "scalar", lambda _q: control)

    respuesta = client.get("/controles/7/editar")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # Prellena el nombre del puesto en el campo de texto asistido
    assert 'value="Puesto de Salud Comunitario San Rafael"' in html
    # El textarea de preguntas no debe tener los prefijos técnicos repetidos
    assert "Revisar crecimiento fetal" in html
    assert "[Centro: Puesto de Salud Comunitario San Rafael]" not in html
    # centro_nombre lo expone directamente
    assert control.centro_nombre == "Puesto de Salud Comunitario San Rafael"


def test_red_apoyo_refactor_ui_ux(client, monkeypatch):
    """Verifica el rediseño accesible y ergonómico de Red de apoyo."""
    from types import SimpleNamespace
    from controllers import routes

    contactos = [
        SimpleNamespace(
            id=10,
            nombre="María Elena Gómez",
            rol="traslado_local",
            telefono="8888-1234",
            comunidad_barrio="Sector Los Cedros",
            notas="Camioneta 4x4 disponible de noche",
        ),
    ]
    perfil = SimpleNamespace(id=5, contactos_comunitarios=contactos)
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (perfil, None))

    respuesta = client.get("/red-comunitaria")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # 1. Cabecera limpia y compacta sin subtítulo repetitivo
    assert "Personas con quienes puedo contar" in html
    assert "Familiares, personas de confianza y transporte confirmados para el parto." in html
    assert "Mis contactos de apoyo" not in html
    assert "add-contact-btn" in html
    assert "Agregar contacto" in html

    # 2. Jerarquía de tarjetas de contacto
    assert "contact-card__name" in html
    assert "María Elena Gómez" in html
    assert "role-badge" in html
    assert "Transporte" in html
    assert "contact-location" in html
    assert "Sector Los Cedros" in html

    # 3. Chip de marcación rápida ergonómica para emergencias (canónico Aurora)
    assert "btn-aurora-chip-action" in html
    assert 'href="tel:8888-1234"' in html
    assert "Llamar al 8888-1234" in html

    # 4. Acciones de gestión al pie sin botón rojo invasivo en la tarjeta
    assert "Editar datos" in html
    assert "contact-action-link--edit" in html
    assert "contact-action-link--delete" in html
    assert 'data-confirm="¿Eliminar este contacto de tu red de apoyo?"' in html
    card_html = html[html.find("contact-card"):html.find("</article>")]
    assert "button--danger" not in card_html


def test_mis_controles_refactor_ui_ux(client, monkeypatch):
    """Verifica el rediseño y reorganización lógica de Mis controles."""
    from datetime import date, time
    from types import SimpleNamespace
    from controllers import routes

    embarazo = SimpleNamespace(
        id=12,
        fum=date(2026, 3, 1),
        fpp=date(2026, 12, 6),
        metodo_fpp="fum",
    )
    proximo_control = SimpleNamespace(
        id=21,
        numero_control=3,
        fecha_control=date(2026, 10, 6),
        hora_control=time(9, 30),
        estado="programado",
        centro_nombre="Centro de Salud Masaya",
        indicaciones="[Ultrasonido / Ecografía] Revisar ultrasonido",
    )
    control_pasado = SimpleNamespace(
        id=20,
        numero_control=2,
        fecha_control=date(2026, 9, 1),
        hora_control=time(10, 0),
        estado="realizado",
        centro_nombre="Puesto Comunitario El Arenal",
        indicaciones="[Exámenes de laboratorio] Rutina",
    )

    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "controles_activos", lambda _emb: [control_pasado, proximo_control])

    respuesta = client.get("/controles")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # 1. Acción de nuevo control en cabecera superior y sin botón FAB flotante
    assert "controls-hero__add-btn" in html
    assert "Registrar nuevo control" in html
    assert "controls-fab" not in html

    # 2. Próximo control: badge de proximidad, fecha humana, subtítulo y metadatos
    assert "corner-glow" not in html
    assert "next-appointment-card" in html
    assert "next-appointment__badge" in html
    assert "Control N.º 3 de tu embarazo" in html
    assert "06 de Octubre de 2026" in html
    assert "06/10/2026" not in html
    assert "Fecha programada" not in html
    assert "card-icon-box" in html
    assert "next-appointment__subtitle" in html
    assert "09:30" in html
    assert "Centro de Salud Masaya" in html

    # 3. Fila horizontal limpia al pie (.card-footer-links) con enlaces y chevron
    assert "card-actions" in html
    assert "card-footer-links" in html
    assert "card-link" in html
    assert "btn-card-action" in html
    assert "Modificar cita" in html
    assert "btn-ghost-sm" in html
    assert 'href="/controles/21/editar"' in html
    assert "Calendario" in html
    assert "link-calendar" in html
    assert 'href="/calendario"' in html

    # 4. Controles anteriores en tarjetas compactas con tipo y badge
    assert "history-card" in html
    assert "Laboratorio" in html
    assert "status-chip--realizado" in html
    assert "Realizado" in html
    assert "01/09/2026" in html


def test_mis_controles_estado_vacio_historial(client, monkeypatch):
    """Verifica el estado vacío sobrio de controles anteriores y próximo control."""
    from datetime import date
    from types import SimpleNamespace
    from controllers import routes

    embarazo = SimpleNamespace(
        id=12,
        fum=date(2026, 3, 1),
        fpp=date(2026, 12, 6),
        metodo_fpp="fum",
    )
    _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    monkeypatch.setattr(routes, "perfil_y_embarazo", lambda _uid: (None, embarazo))
    monkeypatch.setattr(routes, "controles_activos", lambda _emb: [])

    respuesta = client.get("/controles")
    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    assert "empty-history-card" in html
    assert "Sin controles anteriores" in html
    assert "empty-next-card" in html
    assert "No hay un próximo control agendado" in html
