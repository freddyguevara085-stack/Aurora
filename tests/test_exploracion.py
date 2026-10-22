from types import SimpleNamespace

from services.exploracion import filtrar_centros, organizar_guia


def centro(i, departamento='León', municipio='León'):
    return SimpleNamespace(id=i, nombre=f'Centro número {i}', departamento=departamento,
                           municipio=municipio, tipo_establecimiento='centro_salud')


def test_busqueda_ignora_acentos_y_combina_filtros():
    centros = [centro(1), centro(2, 'Managua', 'Tipitapa')]
    assert filtrar_centros(centros, q='leon') == [centros[0]]
    assert filtrar_centros(centros, departamento='Managua', municipio='Tipitapa', q='numero 2') == [centros[1]]
    assert filtrar_centros(centros, tipo='hospital') == []


def test_guia_muestra_solo_temas_publicados_y_conserva_contenido():
    originales = [{'categoria': 'Preparación para el parto', 'titulo': 'Traslado'},
                  {'categoria': 'Puerperio y postparto', 'titulo': 'Consulta'}]
    fichas, temas = organizar_guia(originales)
    assert [f['tema'] for f in fichas] == ['preparacion', 'puerperio']
    assert {t['id'] for t in temas} == {'preparacion', 'puerperio'}
    assert all(t['cantidad'] == 1 for t in temas)
    assert 'tema' not in originales[0]
    assert organizar_guia([]) == ([], [])


def test_directorio_pagina_y_conserva_filtros_sin_javascript(client, monkeypatch):
    from controllers import publicas
    monkeypatch.setattr(publicas, 'centros_activos', lambda: [centro(i) for i in range(25)])
    response = client.get('/centros?departamento=Le%C3%B3n&pagina=2')
    assert response.status_code == 200
    assert response.data.count(b'class="centro-card ') == 12
    assert b'/centros/12' in response.data
    assert b'/centros/0"' not in response.data
    assert b'pagina=3' in response.data
    response = client.get('/centros?pagina=999')
    assert response.data.count(b'class="centro-card ') == 1
    assert client.get('/centros?pagina=invalida').status_code == 200
