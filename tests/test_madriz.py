from collections import Counter
from types import SimpleNamespace

from services.catalogo_minsa import CENTROS, referencia_centro


def test_madriz_cubre_los_nueve_municipios_con_fuentes_por_establecimiento():
    centros = [c for c in CENTROS if c['departamento'] == 'Madriz']
    assert len(centros) == 30
    assert len({c['municipio'] for c in centros}) == 9
    assert Counter(c['tipo_establecimiento'] for c in centros) == {
        'hospital': 2, 'casa_materna': 9, 'centro_salud': 8, 'clinica': 1, 'puesto_salud': 10}
    assert all(c['fuente_url'].startswith('https://www.minsa.gob.ni/') for c in centros)
    assert all(c['fecha_consulta'] == '2026-10-21' for c in centros)


def test_referencia_acepta_nombre_sin_tilde_sin_afirmar_verificacion():
    ref = referencia_centro(SimpleNamespace(nombre='Aurelia Hernandez', municipio='Somoto', departamento='Madriz'))
    assert ref['url'].endswith('/aurelia-hernandez')
    assert 'fecha_verificacion' not in ref
    assert referencia_centro(SimpleNamespace(nombre='Centro desconocido', municipio='Somoto', departamento='Madriz')) is None


def test_publicacion_es_idempotente_y_no_sobrescribe_ediciones(client, monkeypatch):
    from app import app
    from extensions import db
    existentes = {}
    monkeypatch.setattr(db.session, 'scalar', lambda query: existentes.get(query.compile().params['titulo_1']))
    monkeypatch.setattr(db.session, 'add', lambda row: existentes.setdefault(row.titulo, row))
    monkeypatch.setattr(db.session, 'commit', lambda: None)
    result = app.test_cli_runner().invoke(args=['publish-madriz-info'])
    assert result.exit_code == 0, result.output
    assert len(existentes) == 4
    assert all(c.publicado == 1 for c in existentes.values())
    first = next(iter(existentes.values()))
    first.resumen = 'Edición posterior del administrador'
    result = app.test_cli_runner().invoke(args=['publish-madriz-info'])
    assert result.exit_code == 0
    assert 'publicadas: 0' in result.output
    assert first.resumen == 'Edición posterior del administrador'
