import pytest

from controllers import gestante as gestante_mod, publicas as publicas_mod
from test_routes import _iniciar_sesion_falsa


RUTAS_GESTANTE = [
    "/",
    "/embarazo",
    "/perfil",
    "/calendario",
    "/guia",
    "/centros",
    "/alertas",
    "/preguntas",
    "/plan-parto",
    "/plan-parto/imprimir",
    "/red-comunitaria",
    "/red-comunitaria/nuevo",
    "/consulta/preparar",
    "/consulta/imprimir",
]

RUTAS_PUBLICAS = ["/", "/fuentes", "/acerca", "/guia", "/centros"]


@pytest.fixture
def gestante(client, monkeypatch):
    """Sesión de gestante sin embarazo: las páginas nuevas deben renderizar igual."""
    monkeypatch.setitem(client.application.config, "DEMO_MODE", False)
    usuario = _iniciar_sesion_falsa(client, monkeypatch, "usuario")
    usuario.nombres = "Ana"
    usuario.apellidos = "Ruiz"
    monkeypatch.setattr(gestante_mod, "perfil_y_embarazo", lambda _id: (None, None))
    monkeypatch.setattr(gestante_mod, "construir_inicio", lambda _id: {"control": None})
    monkeypatch.setattr(gestante_mod, "centros_activos", lambda *_a, **_k: [])
    monkeypatch.setattr(gestante_mod, "controles_activos", lambda *_a, **_k: [])
    monkeypatch.setattr(gestante_mod, "recordatorios_pendientes", lambda *_a, **_k: [])
    monkeypatch.setattr(publicas_mod, "perfil_y_embarazo", lambda _id: (None, None))
    monkeypatch.setattr(publicas_mod, "construir_inicio", lambda _id: {"control": None})
    monkeypatch.setattr(publicas_mod, "contenidos_publicados", lambda *_a, **_k: [])
    monkeypatch.setattr(publicas_mod, "senales_activas", lambda: [])
    monkeypatch.setattr(publicas_mod, "centros_activos", lambda *_a, **_k: [])
    return client


@pytest.mark.parametrize("ruta", RUTAS_GESTANTE)
def test_ruta_gestante_responde(gestante, ruta):
    respuesta = gestante.get(ruta)
    assert respuesta.status_code in (200, 302), f"{ruta} -> {respuesta.status_code}"


@pytest.mark.parametrize("ruta", RUTAS_PUBLICAS)
def test_ruta_publica_responde(client, ruta):
    respuesta = client.get(ruta)
    assert respuesta.status_code in (200, 302), f"{ruta} -> {respuesta.status_code}"


def test_nav_conserva_los_cinco_del_diseno(gestante):
    html = gestante.get("/embarazo").get_data(as_text=True)
    assert html.count('class="nav-item') == 5


def test_perfil_conserva_los_campos_revertidos(gestante):
    html = gestante.get("/perfil").get_data(as_text=True)
    for campo in ("cedula", "fecha_nacimiento", "direccion_residencia", "departamento"):
        assert f'name="{campo}"' in html, campo


def test_indice_conserva_alertas_y_guia(gestante):
    html = gestante.get("/").get_data(as_text=True)
    assert 'href="/alertas"' in html
    assert 'href="/guia"' in html


def test_admin_carga_el_script_de_confirmacion():
    html = open("templates/admin/base_admin.html", encoding="utf-8").read()
    base = open("templates/layouts/base.html", encoding="utf-8").read()
    assert "js/app.js" not in html
    assert 'id="aurora-confirm"' not in html
    assert "js/app.js" in base
    assert 'id="aurora-confirm"' in base
