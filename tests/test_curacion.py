from datetime import date

from app import app
from extensions import db
from models.contenido import ContenidoPrenatal, SenalAlerta
from services.curacion import RETIRADOS, consolidar_contenido
from services.exploracion import organizar_guia


def fake_catalogo(monkeypatch, *rows):
    registros = {(type(r), r.titulo): r for r in rows}
    def scalar(query):
        modelo = query.column_descriptions[0]['entity']
        return registros.get((modelo, query.compile().params['titulo_1']))
    monkeypatch.setattr(db.session, 'scalar', scalar)
    monkeypatch.setattr(db.session, 'add', lambda row: registros.setdefault((type(row), row.titulo), row))
    monkeypatch.setattr(db.session, 'flush', lambda: None)
    return registros


def test_consolidacion_publica_y_no_duplica_al_repetirse(monkeypatch):
    with app.app_context():
        filas = fake_catalogo(monkeypatch)
        resultado = consolidar_contenido()
        assert resultado['alertas_nuevas'] == 9
        assert resultado['lecturas_nuevas'] == 4
        assert all(r.activo for (modelo, _), r in filas.items() if modelo is SenalAlerta)
        assert sum(consolidar_contenido().values()) == 0
        assert len(filas) == 13


def test_limpieza_solo_retira_firmas_exactas_y_conserva_ediciones(monkeypatch):
    with app.app_context():
        categoria, cuerpo = RETIRADOS['1']
        prueba = ContenidoPrenatal(titulo='1', categoria=categoria, contenido=cuerpo, publicado=1)
        titulo = 'Primer trimestre: organiza tu atención prenatal'
        editado = ContenidoPrenatal(titulo=titulo, categoria=RETIRADOS[titulo][0], contenido='Texto actualizado por administración', publicado=1)
        fake_catalogo(monkeypatch, prueba, editado)
        resultado = consolidar_contenido()
        assert resultado['lecturas_retiradas'] == 1
        assert prueba.publicado == 0
        assert editado.publicado == 1


def test_alerta_inactiva_editada_por_admin_no_se_reactiva(monkeypatch):
    with app.app_context():
        alerta = SenalAlerta(titulo='Dificultad para respirar o dolor en el pecho',
                            descripcion='Edición clínica local', fuente_url='https://www.minsa.gob.ni/', activo=0)
        fake_catalogo(monkeypatch, alerta)
        resultado = consolidar_contenido()
        assert resultado['alertas_actualizadas'] == 0
        assert alerta.activo == 0
        assert alerta.descripcion == 'Edición clínica local'


def test_tres_categorias_canonicas_son_independientes_del_titulo():
    fichas, temas = organizar_guia([
        {'categoria': 'Controles prenatales', 'titulo': 'A'},
        {'categoria': 'Preparación para el parto', 'titulo': 'B'},
        {'categoria': 'Acceso a la atención', 'titulo': 'C'},
    ])
    assert [f['tema'] for f in fichas] == ['controles', 'preparacion', 'atencion']
    assert [t['id'] for t in temas] == ['controles', 'preparacion', 'atencion']


def test_accion_de_alertas_se_lee_sin_expandir_y_sin_sesion(client, monkeypatch):
    from controllers import publicas
    alerta = SenalAlerta(titulo='Señal publicada', descripcion='Descripción educativa',
                        accion_recomendada='Busca atención médica de inmediato.',
                        fuente_nombre='Fuente oficial', fecha_revision=date(2026, 10, 21))
    monkeypatch.setattr(publicas, 'senales_activas', lambda: [alerta])
    response = client.get('/alertas')
    assert response.status_code == 200
    html = response.text
    assert html.index('Qué hacer') < html.index('<details class="alert-card__source"')
    assert 'Esta lista no incluye todas las situaciones posibles.' in html
    assert 'href="/centros"' in html
