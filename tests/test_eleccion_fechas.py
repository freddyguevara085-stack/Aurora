"""La opción visible del formulario determina qué datos se usan al guardar."""
from datetime import date, timedelta
from types import SimpleNamespace

from conftest import _iniciar_sesion_falsa


def preparar(client, monkeypatch, metodo='profesional'):
    from controllers import gestante
    from extensions import db
    hoy = date.today()
    activo = SimpleNamespace(id=11, fum=hoy-timedelta(weeks=24), fpp=hoy+timedelta(weeks=16), metodo_fpp=metodo, fecha_nacimiento_real=None)
    _iniciar_sesion_falsa(client, monkeypatch, 'usuario')
    monkeypatch.setattr(gestante, 'perfil_y_embarazo', lambda _id: (SimpleNamespace(id=1), activo))
    monkeypatch.setattr(gestante, 'controles_activos', lambda _emb: [])
    commits=[]
    monkeypatch.setattr(db.session, 'commit', lambda: commits.append(True))
    return activo, commits


def test_cambiar_a_periodo_recalcula_sin_usar_semanas_ocultas(client, monkeypatch):
    activo, commits = preparar(client, monkeypatch)
    fecha = date.today()-timedelta(weeks=10)
    response = client.post('/embarazo?editar=1', data={'fuente_fecha':'periodo', 'fum':fecha.isoformat(), 'semanas_gestacion':'999', 'dias_gestacion':'99'})
    assert response.status_code == 302
    assert activo.fum == fecha
    assert activo.fpp == fecha+timedelta(days=280)
    assert activo.metodo_fpp == 'fum'
    assert len(commits) == 1


def test_guardar_consulta_sin_cambios_conserva_las_fechas(client, monkeypatch):
    activo, commits = preparar(client, monkeypatch)
    originales=(activo.fum, activo.fpp, activo.metodo_fpp)
    response=client.post('/embarazo?editar=1', data={'fuente_fecha':'consulta', 'semanas_gestacion':'', 'dias_gestacion':'0'})
    assert response.status_code == 302
    assert (activo.fum, activo.fpp, activo.metodo_fpp) == originales
    assert len(commits) == 1


def test_semanas_elegidas_no_usan_la_fecha_del_otro_panel(client, monkeypatch):
    activo, commits = preparar(client, monkeypatch, 'fum')
    response=client.post('/embarazo?editar=1', data={'fuente_fecha':'consulta', 'fum':'no-es-fecha', 'semanas_gestacion':'20', 'dias_gestacion':'3', 'fecha_referencia_gestacion':date.today().isoformat()})
    assert response.status_code == 302
    assert activo.metodo_fpp == 'profesional'
    assert activo.fum is None
    assert activo.fpp == date.today()+timedelta(days=280-143)
    assert len(commits) == 1


def test_opcion_invalida_no_guarda_y_muestra_ayuda(client, monkeypatch):
    activo, commits = preparar(client, monkeypatch)
    response=client.post('/embarazo?editar=1', data={'fuente_fecha':'inventada', 'fum':activo.fum.isoformat()})
    assert response.status_code == 200
    assert 'Elige la fecha de tu período'.encode() in response.data
    assert not commits
