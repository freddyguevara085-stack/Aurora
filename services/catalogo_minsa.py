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

__all__ = [
    "CENTROS",
    "FECHA_CONSULTA",
    "FUENTES",
]
