"""Servicios de negocio, validaciones y consultas del panel administrativo."""

from datetime import date
from urllib.parse import urlsplit

from sqlalchemy import func, select

from extensions import db
from models.auditoria import HistorialAuditoria
from models.contenido import ContenidoPrenatal, SenalAlerta
from models.directorio import CentroAtencion, CentroServicio, Servicio

TIPOS_ESTABLECIMIENTO_VALIDOS = {
    "hospital",
    "centro_salud",
    "puesto_salud",
    "casa_materna",
    "clinica",
    "otro",
}


def _url_fuente_valida(url: str | None) -> bool:
    """True si la URL está vacía o usa http/https con dominio."""
    if not url:
        return True
    try:
        partes = urlsplit(url)
    except ValueError:
        return False
    return partes.scheme in {"http", "https"} and bool(partes.netloc)


def obtener_metricas_dashboard(limite_eventos: int = 6) -> tuple[dict[str, int], list[HistorialAuditoria]]:
    """Calcula las métricas de resumen y últimos eventos para el dashboard administrativo."""
    total_contenidos = db.session.scalar(select(func.count(ContenidoPrenatal.id))) or 0
    total_publicados = (
        db.session.scalar(
            select(func.count(ContenidoPrenatal.id)).where(ContenidoPrenatal.publicado == 1)
        )
        or 0
    )
    total_senales = db.session.scalar(select(func.count(SenalAlerta.id))) or 0
    total_senales_activas = (
        db.session.scalar(
            select(func.count(SenalAlerta.id)).where(SenalAlerta.activo == 1)
        )
        or 0
    )
    total_centros = db.session.scalar(select(func.count(CentroAtencion.id))) or 0
    total_centros_activos = (
        db.session.scalar(
            select(func.count(CentroAtencion.id)).where(CentroAtencion.activo == 1)
        )
        or 0
    )
    total_servicios = db.session.scalar(select(func.count(Servicio.id))) or 0

    ultimos_eventos = db.session.scalars(
        select(HistorialAuditoria)
        .order_by(HistorialAuditoria.created_at.desc())
        .limit(limite_eventos)
    ).all()

    metricas = {
        "contenidos": total_contenidos,
        "contenidos_publicados": total_publicados,
        "senales": total_senales,
        "senales_activas": total_senales_activas,
        "centros": total_centros,
        "centros_activos": total_centros_activos,
        "servicios": total_servicios,
    }
    return metricas, ultimos_eventos


def validar_datos_centro(form_data, centro_actual_id=None):
    """Valida y limpia los datos del formulario de centro de salud."""
    errores = []

    nombre = (form_data.get("nombre") or "").strip()
    if not nombre:
        errores.append("El nombre del centro de salud es obligatorio.")
    elif len(nombre) > 150:
        errores.append("El nombre no puede exceder 150 caracteres.")

    codigo_minsa = (form_data.get("codigo_minsa") or "").strip() or None
    if codigo_minsa:
        if len(codigo_minsa) > 20:
            errores.append("El código MINSA no puede exceder 20 caracteres.")
        else:
            existente = db.session.scalar(
                select(CentroAtencion).where(CentroAtencion.codigo_minsa == codigo_minsa)
            )
            if existente and (not centro_actual_id or existente.id != centro_actual_id):
                errores.append("Ya existe otro centro registrado con ese código MINSA.")

    tipo = (form_data.get("tipo_establecimiento") or "").strip()
    if tipo not in TIPOS_ESTABLECIMIENTO_VALIDOS:
        errores.append("El tipo de establecimiento seleccionado no es válido.")

    silais = (form_data.get("silais") or "").strip() or None
    if silais and len(silais) > 100:
        errores.append("El SILAIS no puede exceder 100 caracteres.")

    municipio = (form_data.get("municipio") or "").strip()
    if not municipio:
        errores.append("El municipio es obligatorio.")
    elif len(municipio) > 100:
        errores.append("El municipio no puede exceder 100 caracteres.")

    departamento = (form_data.get("departamento") or "").strip()
    if not departamento:
        errores.append("El departamento es obligatorio.")
    elif len(departamento) > 100:
        errores.append("El departamento no puede exceder 100 caracteres.")

    direccion = (form_data.get("direccion") or "").strip() or None
    telefono = (form_data.get("telefono") or "").strip() or None
    if telefono and len(telefono) > 30:
        errores.append("El teléfono no puede exceder 30 caracteres.")

    horario = (form_data.get("horario") or "").strip() or None
    if horario and len(horario) > 255:
        errores.append("El horario no puede exceder 255 caracteres.")

    latitud_raw = (form_data.get("latitud") or "").strip()
    latitud = None
    if latitud_raw:
        try:
            latitud = float(latitud_raw)
            if not (-90.0 <= latitud <= 90.0):
                errores.append("La latitud debe estar entre -90 y 90 grados.")
        except ValueError:
            errores.append("La latitud debe ser un número decimal válido.")

    longitud_raw = (form_data.get("longitud") or "").strip()
    longitud = None
    if longitud_raw:
        try:
            longitud = float(longitud_raw)
            if not (-180.0 <= longitud <= 180.0):
                errores.append("La longitud debe estar entre -180 y 180 grados.")
        except ValueError:
            errores.append("La longitud debe ser un número decimal válido.")

    fecha_ver_raw = (form_data.get("fecha_verificacion") or "").strip()
    fecha_verificacion = None
    if fecha_ver_raw:
        try:
            fecha_verificacion = date.fromisoformat(fecha_ver_raw)
            if fecha_verificacion > date.today():
                errores.append("La fecha de revisión no puede estar en el futuro.")
        except ValueError:
            errores.append("La fecha de verificación debe tener formato AAAA-MM-DD válido.")

    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0

    servicios_ids = []
    for sid in form_data.getlist("servicios_ids"):
        try:
            servicios_ids.append(int(sid))
        except (ValueError, TypeError):
            pass

    datos = {
        "codigo_minsa": codigo_minsa,
        "nombre": nombre,
        "tipo_establecimiento": tipo,
        "silais": silais,
        "municipio": municipio,
        "departamento": departamento,
        "direccion": direccion,
        "telefono": telefono,
        "horario": horario,
        "latitud": latitud,
        "longitud": longitud,
        "fecha_verificacion": fecha_verificacion,
        "activo": activo,
    }

    return datos, servicios_ids, errores


def _sincronizar_servicios_centro(centro_id: int, servicios_ids: list[int], fecha_verificacion: date | None) -> None:
    """Reemplaza las asignaciones de servicios para un centro de atención."""
    db.session.execute(
        db.delete(CentroServicio).where(CentroServicio.centro_atencion_id == centro_id)
    )
    for sid in servicios_ids:
        if db.session.get(Servicio, sid):
            db.session.add(
                CentroServicio(
                    centro_atencion_id=centro_id,
                    servicio_id=sid,
                    disponible=1,
                    fecha_verificacion=fecha_verificacion,
                )
            )


def validar_datos_contenido(form_data):
    """Valida y limpia los datos del formulario de contenido prenatal."""
    errores = []

    titulo = (form_data.get("titulo") or "").strip()
    if not titulo:
        errores.append("El título es obligatorio.")
    elif len(titulo) > 180:
        errores.append("El título no puede exceder 180 caracteres.")

    resumen = (form_data.get("resumen") or "").strip() or None
    if resumen and len(resumen) > 500:
        errores.append("El resumen no puede exceder 500 caracteres.")

    contenido = (form_data.get("contenido") or "").strip()
    if not contenido:
        errores.append("El cuerpo del contenido no puede estar vacío.")

    categoria = (form_data.get("categoria") or "").strip()
    if not categoria:
        errores.append("La categoría es obligatoria.")
    elif len(categoria) > 80:
        errores.append("La categoría no puede exceder 80 caracteres.")

    fuente_nombre = (form_data.get("fuente_nombre") or "").strip()
    if not fuente_nombre:
        errores.append("El nombre de la fuente es obligatorio.")
    elif len(fuente_nombre) > 180:
        errores.append("El nombre de la fuente no puede exceder 180 caracteres.")

    fuente_url = (form_data.get("fuente_url") or "").strip() or None
    if fuente_url and len(fuente_url) > 500:
        errores.append("La URL de la fuente no puede exceder 500 caracteres.")
    if not _url_fuente_valida(fuente_url):
        errores.append("La URL de la fuente debe usar HTTP o HTTPS.")

    fecha_rev_raw = (form_data.get("fecha_revision") or "").strip()
    fecha_revision = None
    if not fecha_rev_raw:
        errores.append("La fecha de revisión es obligatoria.")
    else:
        try:
            fecha_revision = date.fromisoformat(fecha_rev_raw)
        except ValueError:
            errores.append("La fecha de revisión debe tener formato AAAA-MM-DD válido.")

    trimestre_raw = (form_data.get("trimestre") or "").strip()
    trimestre = None
    if trimestre_raw:
        try:
            trimestre = int(trimestre_raw)
            if trimestre not in (1, 2, 3):
                errores.append("El trimestre debe ser 1, 2 o 3.")
        except ValueError:
            errores.append("El trimestre debe ser numérico.")

    sem_desde_raw = (form_data.get("semana_desde") or "").strip()
    sem_hasta_raw = (form_data.get("semana_hasta") or "").strip()
    semana_desde = None
    semana_hasta = None

    if sem_desde_raw or sem_hasta_raw:
        if not (sem_desde_raw and sem_hasta_raw):
            errores.append("Debes especificar tanto la semana inicial como la final, o dejar ambas vacías.")
        else:
            try:
                semana_desde = int(sem_desde_raw)
                semana_hasta = int(sem_hasta_raw)
                if not (1 <= semana_desde <= 42):
                    errores.append("La semana inicial debe estar entre 1 y 42.")
                if not (1 <= semana_hasta <= 42):
                    errores.append("La semana final debe estar entre 1 y 42.")
                if semana_desde > semana_hasta:
                    errores.append("La semana inicial no puede ser mayor que la semana final.")
            except ValueError:
                errores.append("Las semanas de gestación deben ser números enteros.")

    publicado = 1 if form_data.get("publicado") in ("1", "true", "on") else 0

    datos = {
        "titulo": titulo,
        "resumen": resumen,
        "contenido": contenido,
        "categoria": categoria,
        "semana_desde": semana_desde,
        "semana_hasta": semana_hasta,
        "trimestre": trimestre,
        "fuente_nombre": fuente_nombre,
        "fuente_url": fuente_url,
        "fecha_revision": fecha_revision,
        "publicado": publicado,
    }

    return datos, errores


def validar_datos_senal(form_data):
    """Valida y limpia los datos del formulario de señal de alerta."""
    errores = []

    titulo = (form_data.get("titulo") or "").strip()
    if not titulo:
        errores.append("El título es obligatorio.")
    elif len(titulo) > 180:
        errores.append("El título no puede exceder 180 caracteres.")

    descripcion = (form_data.get("descripcion") or "").strip()
    if not descripcion:
        errores.append("La descripción de la señal es obligatoria.")

    accion_recomendada = (form_data.get("accion_recomendada") or "").strip()
    if not accion_recomendada:
        errores.append("La acción recomendada es obligatoria.")

    orden_raw = (form_data.get("orden_visual") or "0").strip()
    orden_visual = 0
    try:
        orden_visual = int(orden_raw)
        if not (0 <= orden_visual <= 65535):
            errores.append("El orden visual debe ser un número entero entre 0 y 65535.")
    except ValueError:
        errores.append("El orden visual debe ser un número entero.")

    fuente_nombre = (form_data.get("fuente_nombre") or "").strip()
    if not fuente_nombre:
        errores.append("El nombre de la fuente es obligatorio.")
    elif len(fuente_nombre) > 180:
        errores.append("El nombre de la fuente no puede exceder 180 caracteres.")

    fuente_url = (form_data.get("fuente_url") or "").strip() or None
    if fuente_url and len(fuente_url) > 500:
        errores.append("La URL de la fuente no puede exceder 500 caracteres.")
    if not _url_fuente_valida(fuente_url):
        errores.append("La URL de la fuente debe usar HTTP o HTTPS.")

    fecha_rev_raw = (form_data.get("fecha_revision") or "").strip()
    fecha_revision = None
    if not fecha_rev_raw:
        errores.append("La fecha de revisión médica es obligatoria.")
    else:
        try:
            fecha_revision = date.fromisoformat(fecha_rev_raw)
        except ValueError:
            errores.append("La fecha de revisión debe tener formato AAAA-MM-DD válido.")

    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0

    datos = {
        "titulo": titulo,
        "descripcion": descripcion,
        "accion_recomendada": accion_recomendada,
        "orden_visual": orden_visual,
        "fuente_nombre": fuente_nombre,
        "fuente_url": fuente_url,
        "fecha_revision": fecha_revision,
        "activo": activo,
    }

    return datos, errores


def validar_datos_servicio(form_data, servicio_actual_id=None):
    """Valida y limpia los datos del formulario de servicio."""
    errores = []

    nombre = (form_data.get("nombre") or "").strip()
    if not nombre:
        errores.append("El nombre del servicio es obligatorio.")
    elif len(nombre) > 120:
        errores.append("El nombre del servicio no puede exceder 120 caracteres.")
    else:
        existente = db.session.scalar(
            select(Servicio).where(Servicio.nombre == nombre)
        )
        if existente and (not servicio_actual_id or existente.id != servicio_actual_id):
            errores.append("Ya existe otro servicio registrado con ese nombre.")

    descripcion = (form_data.get("descripcion") or "").strip() or None
    if descripcion and len(descripcion) > 500:
        errores.append("La descripción no puede exceder 500 caracteres.")

    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0
    centros_ids = []
    for centro_id in form_data.getlist("centros_ids"):
        try:
            centros_ids.append(int(centro_id))
        except (TypeError, ValueError):
            continue

    datos = {
        "nombre": nombre,
        "descripcion": descripcion,
        "activo": activo,
    }

    return datos, centros_ids, errores


def _centros_visibles_para_asignar():
    """Obtiene los centros de atención activos ordenados por departamento, municipio y nombre."""
    return db.session.scalars(
        select(CentroAtencion)
        .where(CentroAtencion.activo == 1)
        .order_by(CentroAtencion.departamento, CentroAtencion.municipio, CentroAtencion.nombre)
    ).all()


def _sincronizar_centros_servicio(servicio_id, centros_ids):
    """Reemplaza las asignaciones del servicio por los centros elegidos."""
    db.session.execute(
        db.delete(CentroServicio).where(CentroServicio.servicio_id == servicio_id)
    )
    for centro_id in set(centros_ids):
        centro = db.session.get(CentroAtencion, centro_id)
        if centro and centro.activo:
            db.session.add(
                CentroServicio(
                    centro_atencion_id=centro.id,
                    servicio_id=servicio_id,
                    disponible=1,
                )
            )
