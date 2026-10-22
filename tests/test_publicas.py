"""Pruebas de rutas públicas: inicio, guía, centros, alertas, fuentes y alcance MVP."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace

from conftest import _iniciar_sesion_falsa


def test_alert_fab_visible_para_usuaria_no_en_alertas_ni_visitante(client, monkeypatch):
    from controllers import publicas as routes
    from extensions import db

    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))

    # Visitante sin sesion: no ve el acceso fijo.
    assert b"alert-fab" not in client.get("/login").data

    # Usuaria autenticada: visible en Inicio, ausente en Señales de alerta.
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


def test_inicio_publico_no_requiere_cuenta(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"data-aurora-tutorial" not in response.data
    assert b"Organiza tu" in response.data
    assert b"atenci\xc3\xb3n prenatal." in response.data
    assert b"no es un servicio m\xc3\xa9dico" in response.data


def test_guia_consultable_sin_cuenta(client, monkeypatch):
    from controllers import publicas as routes

    monkeypatch.setattr(routes, "contenidos_publicados", lambda *_args, **_kwargs: [])
    response = client.get("/guia")
    assert response.status_code == 200
    assert b"Gu\xc3\xada prenatal" in response.data


def test_contenido_y_senal_publicados_por_admin_se_muestran(client, monkeypatch):
    from controllers import publicas as publicas_routes
    from extensions import db
    from models.contenido import ContenidoPrenatal, SenalAlerta
    from models.usuario import Usuario
    from services import home as home_service

    etiqueta = "PUBLICADO_POR_ADMIN_4242"
    contenido = ContenidoPrenatal(
        id=4242, titulo=etiqueta, resumen=etiqueta, contenido=etiqueta,
        categoria=etiqueta, fuente_nombre=etiqueta, fecha_revision=date(2026, 1, 1), publicado=1,
    )
    senal = SenalAlerta(
        id=4242, titulo=etiqueta, descripcion=etiqueta, accion_recomendada=etiqueta,
        orden_visual=1, fuente_nombre=etiqueta, fecha_revision=date(2026, 1, 1), activo=1,
    )
    monkeypatch.setattr(publicas_routes, "contenidos_publicados", lambda *_a, **_k: [contenido])
    monkeypatch.setattr(publicas_routes, "senales_activas", lambda: [senal])

    assert etiqueta.encode() in client.get("/guia").data
    assert etiqueta.encode() in client.get("/alertas").data

    monkeypatch.setattr(
        db.session, "get", lambda model, _key: SimpleNamespace(nombres="Demo") if model is Usuario else None,
    )
    monkeypatch.setattr(home_service, "perfil_y_embarazo", lambda _usuario_id: (None, None))
    monkeypatch.setattr(home_service, "contenidos_publicados", lambda *_a, **_k: [contenido])
    monkeypatch.setattr(home_service, "senales_activas", lambda: [senal])

    with client.application.app_context():
        inicio = home_service.construir_inicio(7)

    assert inicio["contenidos"] == [contenido]
    assert inicio["senales"] == [senal]


def test_ruta_de_revision_demo_no_se_publica(client):
    assert client.get("/demo/revision-clinica").status_code == 404


def test_alertas_consultables_sin_cuenta(client, monkeypatch):
    from extensions import db

    monkeypatch.setattr(db.session, "scalars", lambda _query: SimpleNamespace(all=lambda: []))
    response = client.get("/alertas")
    assert response.status_code == 200
    assert b"Se\xc3\xb1ales de alerta" in response.data


def test_alertas_muestra_senales_activas_de_administracion(client, monkeypatch):
    from controllers import publicas as routes

    senales = [
        SimpleNamespace(
            titulo="Señal publicada",
            descripcion="Descripción",
            accion_recomendada="Busca atención profesional.",
            orden_visual=1,
            fuente_nombre="MINSA",
            fuente_url="https://www.minsa.gob.ni/",
            fecha_revision=date(2026, 10, 6),
        )
    ]
    monkeypatch.setattr(routes, "senales_activas", lambda: senales)
    response = client.get("/alertas")
    assert response.status_code == 200
    assert b"Se\xc3\xb1al publicada" in response.data


def test_centros_consultables_sin_cuenta(client, monkeypatch):
    from controllers import publicas as routes

    monkeypatch.setattr(routes, "centros_activos", lambda *_args: [])
    response = client.get("/centros")
    assert response.status_code == 200
    assert b"Directorio de referencia" in response.data


def test_clinica_previsional_se_identifica_y_muestra_requisito_inss(client, monkeypatch):
    from controllers import publicas as routes

    clinica = SimpleNamespace(
        id=7,
        nombre="Puerto Cabezas",
        tipo_establecimiento="clinica",
        municipio="Puerto Cabezas",
        departamento="RACCN",
        fecha_verificacion=None,
        direccion="Barrio El Cocal",
        telefono=None,
        horario=None,
        latitud=None,
        longitud=None,
    )
    monkeypatch.setattr(routes, "centros_activos", lambda: [clinica])
    monkeypatch.setattr(routes, "centro_activo", lambda _centro_id: clinica)
    monkeypatch.setattr(routes, "servicios_disponibles", lambda _centro_id: [])

    listado = client.get("/centros")
    assert listado.status_code == 200
    assert b'data-tipo="clinica"' in listado.data
    assert "Clínicas previsionales".encode() in listado.data

    detalle = client.get("/centros/7")
    assert detalle.status_code == 200
    assert "Clínica Médica Previsional (CMP MINSA)".encode() in detalle.data
    assert b"convenios con el INSS" in detalle.data


def test_centros_estilos_responsivos_no_desbordan():
    with open("static/css/pages.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert "grid-template-columns: minmax(0, 1fr);" in css
    assert "word-break: break-word;" in css


def test_directorio_no_oculta_centros_por_departamento_del_perfil():
    plantilla = (Path(__file__).resolve().parent.parent / "templates" / "centros.html").read_text(encoding="utf-8")

    assert "departamento_usuario" not in plantilla
    assert "Todos los departamentos" in plantilla


def test_seguimientos_clinicos_no_forman_parte_del_mvp(client):
    for ruta in (
        "/preeclampsia",
        "/preeclampsia/seguimiento",
        "/preeclampsia/seguimiento/registros",
        "/puerperio",
        "/puerperio/imprimir",
    ):
        assert client.get(ruta).status_code == 404, ruta


def test_fuentes_muestra_solo_fuentes_minsa_recientes(client):
    respuesta = client.get("/fuentes")
    assert respuesta.status_code == 200
    assert b"Fuentes consultadas" in respuesta.data
    assert b"MINSA - Actividades B\xc3\xa1sicas durante la Atenci\xc3\xb3n Prenatal (2022)" in respuesta.data
    assert b"paho.org" not in respuesta.data
    assert b"revisi" in respuesta.data.lower()


def test_aurora_no_expone_biblioteca_experimental(client):
    respuesta = client.get('/guia')
    assert respuesta.status_code == 200
    for marcador in (b'data-library', b'library.js', b'library.css', b'experience.css', b'workspace-nav'):
        assert marcador not in respuesta.data
    for ruta in ('/guia/tema/ideas-para-tu-mesa', '/guia/tema/nauseas-sin-mitos'):
        assert client.get(ruta).status_code == 404
