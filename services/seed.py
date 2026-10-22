"""Sincronización idempotente del directorio MINSA."""

from extensions import db
from models.directorio import CentroAtencion
from services.catalogo_minsa import CENTROS as CENTROS_VERIFICADOS


def sincronizar_centros_minsa(retirar_no_listados: bool = False, departamento: str | None = None) -> dict[str, int]:
    """Inserta o actualiza los centros oficiales del MINSA de forma idempotente."""
    nuevos = 0
    actualizados = 0
    catalogo = [c for c in CENTROS_VERIFICADOS if not departamento or c['departamento'] == departamento]
    if departamento and not catalogo:
        raise ValueError('No hay centros en el catálogo para ese departamento.')
    claves_canonicas = {(datos["nombre"], datos["municipio"]) for datos in catalogo}

    for datos in catalogo:
        existente = db.session.scalar(
            db.select(CentroAtencion).where(
                CentroAtencion.nombre == datos["nombre"],
                CentroAtencion.municipio == datos["municipio"],
            )
        )
        if existente:
            existente.tipo_establecimiento = datos["tipo_establecimiento"]
            existente.subtipo = datos.get("subtipo")
            existente.silais = datos["silais"]
            existente.departamento = datos["departamento"]
            existente.direccion = datos["direccion"]
            existente.zona = datos.get("zona")
            existente.activo = 1
            actualizados += 1
        else:
            db.session.add(
                CentroAtencion(
                    nombre=datos["nombre"],
                    tipo_establecimiento=datos["tipo_establecimiento"],
                    subtipo=datos.get("subtipo"),
                    zona=datos.get("zona"),
                    silais=datos["silais"],
                    departamento=datos["departamento"],
                    municipio=datos["municipio"],
                    direccion=datos["direccion"],
                    telefono=None,
                    horario=None,
                    latitud=None,
                    longitud=None,
                    fecha_verificacion=None,
                    activo=1,
                )
            )
            nuevos += 1

    retirados = 0
    if retirar_no_listados:
        for centro in db.session.scalars(
            db.select(CentroAtencion).where(CentroAtencion.activo == 1)
        ):
            if (not departamento or centro.departamento == departamento) and (centro.nombre, centro.municipio) not in claves_canonicas:
                centro.activo = 0
                retirados += 1

    db.session.flush()
    return {
        "total": len(catalogo),
        "nuevos": nuevos,
        "actualizados": actualizados,
        "retirados": retirados,
    }
