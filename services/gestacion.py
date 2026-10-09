"""Reglas de negocio de la gestación reutilizables por los controladores.

Aquí vive la validación y normalización de fechas, la resolución de centros y
los catálogos usados por los formularios de embarazo, controles y red de apoyo.
Sin HTML ni peticiones HTTP.
"""

from datetime import date, timedelta

from extensions import db
from models.gestacion import ContactoComunitario
from services.mvp import centro_activo


PLAN_PARTO_TRANSPORTES = {
    'propio': 'Vehículo propio',
    'familiar_vecino': 'Apoyo de familiar o vecino',
    'publico_colectivo': 'Transporte público / bus / panga',
    'caponera_taxi': 'Taxi o caponera local',
    'ambulancia_minsa': 'Coordinación con ambulancia del MINSA',
    'otro': 'Otro medio acordado',
}

ROLES_COMUNITARIOS = {
    'brigadista': 'Contacto comunitario',
    'partera': 'Acompañante de confianza',
    'promotor_salud': 'Persona de apoyo',
    'traslado_local': 'Transporte',
    'lider_comunitario': 'Referente comunitario',
    'vecino_apoyo': 'Familiar, vecina o vecino',
    'otro': 'Otro contacto',
}

PREGUNTA_MAX_CARACTERES = 500


def seguimiento_fecha_parto(
    fpp: date | None,
    fecha_nacimiento_real: date | None = None,
    hoy: date | None = None,
) -> dict:
    """Resume el seguimiento informativo de una FPP sin valoraciones clínicas."""
    hoy = hoy or date.today()
    if not fpp:
        return {
            "estado": "sin_fecha_probable", "titulo": "Fecha probable pendiente",
            "mensaje": "Registra una fecha de referencia para mostrar el seguimiento estimado.",
            "dias": None, "resultado": None, "nota_destacada": False,
        }
    if fecha_nacimiento_real:
        diferencia = (fecha_nacimiento_real - fpp).days
        resultado = (
            "Antes de la fecha estimada" if diferencia < -7 else
            "Después de la fecha estimada" if diferencia > 7 else
            "Cerca de la fecha estimada"
        )
        return {
            "estado": "nacimiento_registrado", "titulo": "Nacimiento registrado",
            "mensaje": "La fecha probable de parto se conserva como una estimación para tu seguimiento.",
            "dias": diferencia, "resultado": resultado,
            "nota_destacada": abs(diferencia) > 30,
        }
    dias = (hoy - fpp).days
    if dias < 0:
        return {
            "estado": "antes_fecha_probable", "titulo": "Seguimiento de la fecha estimada",
            "mensaje": "La fecha probable de parto es una estimación. Sigue las indicaciones de tu personal de salud.",
            "dias": dias, "resultado": None, "nota_destacada": False,
        }
    if dias == 0:
        return {
            "estado": "fecha_probable_alcanzada", "titulo": "Hoy es la fecha probable de parto",
            "mensaje": "Esta fecha es una estimación. Sigue las indicaciones de tu personal de salud.",
            "dias": 0, "resultado": None, "nota_destacada": False,
        }
    return {
        "estado": "despues_fecha_probable", "titulo": "Seguimiento después de la fecha probable",
        "mensaje": f"Han transcurrido {dias} {'día' if dias == 1 else 'días'} desde la fecha probable. Es una estimación; sigue las indicaciones de tu personal de salud.",
        "dias": dias, "resultado": None, "nota_destacada": False,
    }


def validar_fecha_nacimiento_real(
    fecha_raw: str | None, hoy: date | None = None,
) -> tuple[date | None, str | None]:
    """Valida una fecha de nacimiento registrada por la usuaria."""
    if not fecha_raw:
        return None, "Indica la fecha real del nacimiento."
    try:
        fecha = date.fromisoformat(fecha_raw)
    except ValueError:
        return None, "La fecha real del nacimiento no es válida."
    if fecha > (hoy or date.today()):
        return None, "La fecha real del nacimiento no puede estar en el futuro."
    return fecha, None


def validar_fechas_embarazo(
    fum_raw: str | None,
    fpp_raw: str | None,
    metodo: str | None,
) -> tuple[date | None, date | None, str | None]:
    """Valida fechas de un embarazo activo con un límite visual de 42 semanas."""
    try:
        fum = date.fromisoformat(fum_raw) if fum_raw else None
        fpp = date.fromisoformat(fpp_raw) if fpp_raw else None
    except ValueError:
        return None, None, "Revisa el formato de las fechas."
    if not fum and not fpp:
        return None, None, "Indica la fecha de última menstruación o la fecha probable de parto."
    hoy = date.today()
    if metodo is None:
        metodo = "fum" if fum else "otro"
    if fum and fum > hoy:
        return None, None, "La fecha de última menstruación no puede estar en el futuro."
    if fum and (hoy - fum).days > 42 * 7:
        return None, None, "La FUM corresponde a más de 42 semanas; revisa la fecha del embarazo activo."
    if fpp and fpp < hoy - timedelta(days=14):
        return None, None, "La FPP corresponde a más de 42 semanas; revisa la fecha del embarazo activo."
    if fpp and fpp > hoy + timedelta(days=280):
        return None, None, "La FPP está a más de 40 semanas desde hoy; revisa la fecha."
    if metodo == "fum" and not fum:
        return None, None, "Indica la FUM o selecciona el método con el que se estimó la FPP."
    if metodo in {"ecografia", "profesional", "otro"} and not fpp:
        return None, None, "Indica la FPP según el método de estimación seleccionado."
    if fum and fpp:
        dias = (fpp - fum).days
        if dias < 1 or dias > 322:
            return None, None, "La relación entre las fechas no parece coherente."
    if metodo == "fum" and fum:
        calculada = fum + timedelta(days=280)
        if fpp and fpp != calculada:
            return None, None, "Con método FUM, la FPP se calcula a 280 días de esa fecha. Revisa las fechas o selecciona el método utilizado por tu profesional."
        return fum, calculada, None
    return fum, fpp, None


def fechas_embarazo_desde_edad_gestacional(
    semanas_raw: str | None,
    dias_raw: str | None,
    fecha_raw: str | None,
    hoy: date | None = None,
) -> tuple[date | None, date | None, str | None]:
    """Deriva una fecha probable de parto desde semanas indicadas y su fecha de referencia."""
    if not semanas_raw and not dias_raw:
        return None, None, None
    hoy = hoy or date.today()
    try:
        semanas = int(semanas_raw or 0)
        dias = int(dias_raw or 0)
        referencia = date.fromisoformat(fecha_raw) if fecha_raw else hoy
    except ValueError:
        return None, None, "Revisa las semanas, los días y la fecha en que te indicaron la edad gestacional."
    if not semanas_raw and dias:
        return None, None, "Ingresa primero las semanas completas."
    if semanas < 0 or semanas > 42 or dias < 0 or dias > 6 or (semanas == 42 and dias):
        return None, None, "La edad gestacional debe estar entre 0 y 42 semanas y 0 a 6 días."
    if referencia > hoy:
        return None, None, "La fecha de referencia no puede estar en el futuro."
    if (hoy - referencia).days + semanas * 7 + dias > 42 * 7:
        return None, None, "La fecha y la edad gestacional superan las 42 semanas; revisa los datos."
    inicio_estimado = referencia - timedelta(days=semanas * 7 + dias)
    return None, inicio_estimado + timedelta(days=280), None


def validar_fecha_control(
    fecha_control: date,
    inicio_gestacion: date | None,
    estado: str,
    hoy: date | None = None,
) -> str | None:
    """Evita citas programadas pasadas o fuera de la gestación estimada."""
    hoy = hoy or date.today()
    if estado in {"programado", "reprogramado"} and fecha_control < hoy:
        return "La fecha de una cita programada no puede estar en el pasado."
    if inicio_gestacion:
        dias = (fecha_control - inicio_gestacion).days
        if dias < 0:
            return "La fecha del control es anterior al inicio estimado del embarazo; revisa ambas fechas."
        if dias > 42 * 7:
            return "La fecha del control supera las 42 semanas estimadas; revisa los datos con tu profesional de salud."
    return None


def construir_indicaciones(tipo_control, centro_personalizado, indicaciones_texto):
    """Compone el texto de indicaciones guardando tipo y centro como prefijos.

    Formato: ``[Tipo] [Centro: Nombre] texto libre``. Devuelve ``None`` si no
    hay nada que guardar.
    """
    partes = []
    if tipo_control and tipo_control != 'Control prenatal regular':
        partes.append(f"[{tipo_control}]")
    if centro_personalizado:
        partes.append(f"[Centro: {centro_personalizado}]")
    if indicaciones_texto:
        partes.append(indicaciones_texto)
    return " ".join(partes).strip() or None


def resolver_centro_input(texto, centros):
    """Resuelve un centro a partir del texto ingresado con datalist o texto libre.

    Retorna (centro_id, nombre_personalizado):
    - Coincide con centro registrado: (centro.id, None)
    - Puesto libre o comunitario: (None, texto_limpio)
    - Vacío: (None, None)
    """
    if not texto:
        return None, None
    raw = texto.strip()
    if not raw:
        return None, None

    # Compatibilidad con envíos directos de id numérico
    if raw.isdigit():
        cid = int(raw)
        for c in centros:
            if getattr(c, 'id', None) == cid:
                return cid, None
        if centro_activo(cid):
            return cid, None

    raw_lower = raw.lower()
    for c in centros:
        c_nom = (getattr(c, 'nombre', None) or '').strip()
        c_mun = (getattr(c, 'municipio', None) or '').strip()
        c_dep = (getattr(c, 'departamento', None) or '').strip()
        variantes = {c_nom.lower()}
        if c_mun:
            variantes.add(f"{c_nom} ({c_mun})".lower())
        if c_dep:
            variantes.add(f"{c_nom} ({c_dep})".lower())
            if c_mun:
                variantes.add(f"{c_nom} ({c_mun}, {c_dep})".lower())
        if raw_lower in variantes:
            return getattr(c, 'id', None), None

    return None, raw[:150]


def ordenar_centros_por_zona(centros, perfil):
    """Ordena los centros priorizando el municipio y departamento de la gestante."""
    if not perfil or (not perfil.departamento and not perfil.municipio):
        return list(centros)
    dep_u = (perfil.departamento or '').strip().lower()
    mun_u = (perfil.municipio or '').strip().lower()
    return sorted(
        centros,
        key=lambda c: (
            0 if mun_u and (getattr(c, 'municipio', None) or '').strip().lower() == mun_u else (
                1 if dep_u and (getattr(c, 'departamento', None) or '').strip().lower() == dep_u else 2
            ),
            getattr(c, 'nombre', ''),
        ),
    )


def validar_contacto_comunitario(form):
    """Normaliza y valida los campos de un contacto de la red de apoyo."""
    datos = {
        'nombre': (form.get('nombre') or '').strip(),
        'rol': (form.get('rol') or '').strip(),
        'telefono': (form.get('telefono') or '').strip(),
        'comunidad_barrio': (form.get('comunidad_barrio') or '').strip(),
        'notas': (form.get('notas') or '').strip(),
    }
    if (
        not datos['nombre']
        or len(datos['nombre']) > 150
        or datos['rol'] not in ROLES_COMUNITARIOS
        or len(datos['telefono']) > 30
        or len(datos['comunidad_barrio']) > 150
        or len(datos['notas']) > 255
    ):
        return None, 'Revisa el nombre, el rol y la longitud de los campos del contacto.'
    for campo in ('telefono', 'comunidad_barrio', 'notas'):
        datos[campo] = datos[campo] or None
    return datos, None


def contacto_propio(contacto_id, perfil):
    """Busca un contacto verificando que pertenezca al perfil autenticado."""
    return db.session.scalar(
        db.select(ContactoComunitario).where(
            ContactoComunitario.id == contacto_id,
            ContactoComunitario.perfil_gestante_id == (perfil.id if perfil else None),
        )
    )
