"""Regresiones de funciones existentes: edición, recordatorios y citas."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from conftest import _iniciar_sesion_falsa


def test_editar_pregunta_carga_el_texto_guardado(client, monkeypatch):
    from extensions import db
    _iniciar_sesion_falsa(client, monkeypatch, 'usuario')
    pregunta = SimpleNamespace(id=4, usuario_id=7, pregunta='¿Qué documentos debo llevar?', estado='pendiente')
    monkeypatch.setattr(db.session, 'scalar', lambda _q: pregunta)
    monkeypatch.setattr(db.session, 'scalars', lambda _q: SimpleNamespace(all=lambda: [pregunta]))
    response = client.get('/preguntas?editar=4')
    assert response.status_code == 200
    html = response.data.decode()
    textarea = html.split('id="edit-question-4"', 1)[1].split('</textarea>', 1)[0]
    assert pregunta.pregunta in textarea


def test_calendario_muestra_recordatorios_sin_embarazo(client, monkeypatch):
    import controllers.gestante as routes
    _iniciar_sesion_falsa(client, monkeypatch, 'usuario')
    monkeypatch.setattr(routes, 'perfil_y_embarazo', lambda _id: (None, None))
    monkeypatch.setattr(routes, 'controles_activos', lambda _emb: [])
    monkeypatch.setattr(routes, 'recordatorios_pendientes', lambda _id: [SimpleNamespace(titulo='Llevar documentos', fecha_hora=datetime.now()+timedelta(days=1))])
    response = client.get('/calendario')
    assert response.status_code == 200
    assert b'Llevar documentos' in response.data
    assert b'id="calendar-reminders-title"' in response.data


def test_calendario_muestra_confirmacion_de_guardado(client, monkeypatch):
    import controllers.gestante as routes
    _iniciar_sesion_falsa(client, monkeypatch, 'usuario')
    monkeypatch.setattr(routes, 'perfil_y_embarazo', lambda _id: (None, None))
    monkeypatch.setattr(routes, 'controles_activos', lambda _emb: [])
    monkeypatch.setattr(routes, 'recordatorios_pendientes', lambda _id: [])
    with client.session_transaction() as session:
        session['_flashes'] = [('success', 'Recordatorio creado correctamente.')]
    assert b'Recordatorio creado correctamente.' in client.get('/calendario').data


def test_controles_muestra_todas_las_citas_futuras(client, monkeypatch):
    import controllers.gestante as routes
    _iniciar_sesion_falsa(client, monkeypatch, 'usuario')
    activo = SimpleNamespace(id=2)
    def control(identificador, dias):
        return SimpleNamespace(id=identificador, numero_control=identificador, fecha_control=date.today()+timedelta(days=dias), hora_control=None, estado='programado', centro_nombre='Centro local', indicaciones=None)
    primero, segundo, tercero = control(11, 1), control(12, 7), control(13, 14)
    monkeypatch.setattr(routes, 'perfil_y_embarazo', lambda _id: (None, activo))
    monkeypatch.setattr(routes, 'controles_activos', lambda _emb: [primero, segundo, tercero])
    response = client.get('/controles')
    assert response.status_code == 200
    for item in (primero, segundo, tercero):
        assert response.data.count(f'href="/controles/{item.id}/editar"'.encode()) == 1
    assert b'Otras citas programadas' in response.data
