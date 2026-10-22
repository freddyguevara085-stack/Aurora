"""Pruebas del panel administrativo, validación de recursos y confirmación accesible."""

from pathlib import Path
from types import SimpleNamespace

from werkzeug.datastructures import MultiDict


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


def test_servicio_admin_acepta_centros_para_mostrarlo_en_sus_fichas(monkeypatch):
    from controllers.admin.servicios import validar_datos_servicio
    from extensions import db

    monkeypatch.setattr(db.session, "scalar", lambda _query: None)
    datos, centros_ids, errores = validar_datos_servicio(
        MultiDict(
            [
                ("nombre", "VacunaciÃ³n"),
                ("descripcion", "Servicio de ejemplo"),
                ("activo", "1"),
                ("centros_ids", "2"),
                ("centros_ids", "7"),
            ]
        )
    )

    assert errores == []
    assert datos["activo"] == 1
    assert centros_ids == [2, 7]


def test_fuente_solo_acepta_http_o_https():
    from controllers.admin import _url_fuente_valida

    assert _url_fuente_valida(None)
    assert _url_fuente_valida("https://salud.example.ni/guia")
    assert not _url_fuente_valida("javascript:alert(1)")
    assert not _url_fuente_valida("//example.ni/guia")
    assert not _url_fuente_valida("https://[invalid")


def test_confirmacion_eliminar_usa_dialogo_accesible():
    raiz = Path(__file__).resolve().parent.parent
    base = (raiz / "templates" / "layouts" / "base.html").read_text(encoding="utf-8")
    base_admin = (raiz / "templates" / "admin" / "base_admin.html").read_text(encoding="utf-8")
    assert "<dialog" in base
    assert 'id="aurora-confirm"' in base
    assert 'id="aurora-confirm"' not in base_admin
    assert "static', filename='js/app.js'" not in base_admin
    for nombre in ("centros", "contenidos", "senales", "servicios"):
        html = (raiz / "templates" / "admin" / nombre / "index.html").read_text(encoding="utf-8")
        assert "confirm(" not in html, nombre
        assert "data-confirm=" in html, nombre
