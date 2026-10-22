"""Consolidación editorial explícita; se ejecuta por CLI, nunca al abrir una página.

Solo retira registros con título y cuerpo conocidos. Conserva cambios posteriores
hechos por administración y no borra filas ni altera otros módulos.
"""
import json
from datetime import date
from pathlib import Path

from extensions import db
from models.contenido import ContenidoPrenatal, SenalAlerta

SEEDS = Path(__file__).resolve().parent.parent / 'database' / 'seeds'
RETIRADOS = {
    '1': ('3', '.......m.'),
    'Primer trimestre: organiza tu atención prenatal': (
        'atención prenatal',
        'La atención prenatal ayuda a acompañar el embarazo con el equipo de salud. Puedes anotar preguntas, compartir cambios que te preocupen y asistir a los controles indicados. Esta información es educativa y no sustituye la orientación profesional.'),
    'Segundo trimestre: continúa el acompañamiento': (
        'bienestar',
        'El segundo trimestre puede ser un buen momento para revisar tus próximas citas y conversar con el equipo de salud sobre tus necesidades. Busca orientación profesional para cualquier duda o cambio relacionado con tu embarazo.'),
}


def consolidar_contenido():
    """Aplica el catálogo respaldado por fuentes y devuelve cambios sin confirmar la transacción."""
    resultado = dict(lecturas_nuevas=0, lecturas_reclasificadas=0, lecturas_retiradas=0,
                     alertas_nuevas=0, alertas_actualizadas=0)
    lecturas = json.loads((SEEDS / 'orientaciones_madriz.json').read_text(encoding='utf-8'))
    for datos in lecturas:
        actual = db.session.scalar(db.select(ContenidoPrenatal).filter_by(titulo=datos['titulo']))
        categoria = datos['categoria']
        if actual is None:
            datos['fecha_revision'] = date.fromisoformat(datos['fecha_revision'])
            db.session.add(ContenidoPrenatal(**{**datos, 'categoria': categoria}, publicado=1))
            resultado['lecturas_nuevas'] += 1
        elif actual.contenido == datos['contenido'] and actual.fuente_url == datos['fuente_url'] and actual.categoria != categoria:
            actual.categoria = categoria
            resultado['lecturas_reclasificadas'] += 1
    for titulo, (categoria, cuerpo) in RETIRADOS.items():
        actual = db.session.scalar(db.select(ContenidoPrenatal).filter_by(titulo=titulo))
        if actual and actual.categoria == categoria and actual.contenido == cuerpo and actual.publicado:
            actual.publicado = 0
            resultado['lecturas_retiradas'] += 1
    alertas = json.loads((SEEDS / 'senales_alerta_oficiales.json').read_text(encoding='utf-8'))
    for datos in alertas:
        actual = db.session.scalar(db.select(SenalAlerta).filter_by(titulo=datos['titulo']))
        datos['fecha_revision'] = date.fromisoformat(datos['fecha_revision'])
        if actual is None:
            db.session.add(SenalAlerta(**datos, activo=1))
            resultado['alertas_nuevas'] += 1
        elif (actual.titulo == 'Dificultad para respirar o dolor en el pecho'
              and actual.descripcion == 'La dificultad para respirar o el dolor en el pecho requieren atención urgente.'
              and actual.fuente_url == 'https://www.paho.org/es/temas/salud-materna'):
            # Sustituye únicamente el borrador antiguo identificado por la fuente específica consultada.
            for campo, valor in datos.items():
                setattr(actual, campo, valor)
            actual.activo = 1
            resultado['alertas_actualizadas'] += 1
    db.session.flush()
    return resultado
