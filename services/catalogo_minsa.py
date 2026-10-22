"""Catálogo de fuentes oficiales y establecimientos del MINSA.

Carga los conjuntos de datos estáticos desde ``database/seeds/*.json`` para
mantener el código Python desacoplado de catálogos extensos.
"""

import json
from pathlib import Path

_SEEDS_DIR = Path(__file__).resolve().parent.parent / "database" / "seeds"


def _cargar_json(nombre_archivo: str):
    ruta = _SEEDS_DIR / nombre_archivo
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


FECHA_CONSULTA = "2026-10-06"

FUENTES: dict[str, dict[str, str]] = _cargar_json("fuentes_minsa.json")
CENTROS: list[dict] = _cargar_json("centros_minsa.json")


def referencia_centro(centro):
    """Procedencia documental del catálogo; no equivale a verificación institucional."""
    from services.exploracion import normalizar
    for item in CENTROS:
        if (normalizar(item['nombre']) == normalizar(centro.nombre)
                and normalizar(item['municipio']) == normalizar(centro.municipio)
                and item['departamento'] == centro.departamento):
            fuente = FUENTES[item['fuente']]
            return {'nombre': fuente['nombre'], 'url': item.get('fuente_url', fuente['url']),
                    'fecha_consulta': item.get('fecha_consulta', FECHA_CONSULTA)}
    return None

__all__ = [
    "CENTROS",
    "FECHA_CONSULTA",
    "FUENTES",
]
