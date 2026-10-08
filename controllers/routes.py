from datetime import date, datetime, time, timedelta
import re

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from controllers.admin import admin_required
from demo_nicaragua import BORRADORES, CONTEXTO, CUENTAS_DEMO_EMAILS, FECHA_CONSULTA, FUENTES
from services.home import calcular_semana_gestacional, construir_inicio, fecha_inicio_gestacion
from services.mvp import centros_activos, centro_activo, contenidos_publicados, controles_activos, perfil_y_embarazo, recordatorios_pendientes, servicios_disponibles
from extensions import db
from models.gestacion import ContactoComunitario, Embarazo, PerfilGestante, PlanParto
from models.seguimiento import ControlPrenatal, PreguntaConsulta, Recordatorio

main_bp = Blueprint('main', __name__)

# Ruta principal (la vista HTML)
@main_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('public_home.html')
    home_data = construir_inicio(current_user.id)
    return render_template('index.html', home=home_data)


def _usuario_gestante():
    return current_user.rol and current_user.rol.nombre == "usuario"


def _es_cuenta_demo():
    """True solo para la cuenta ficticia de demostración con DEMO_MODE activo."""
    return (
        current_user.is_authenticated
        and current_app.config.get("DEMO_MODE")
        and (
            getattr(current_user, "email", None) in CUENTAS_DEMO_EMAILS
            or (getattr(current_user, "rol", None) and getattr(current_user.rol, "nombre", None) == "administrador")
        )
    )


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


@main_bp.route('/embarazo', methods=['GET', 'POST'])
@login_required
def embarazo():
    perfil, activo = perfil_y_embarazo(current_user.id)
    editar = (request.args.get('editar') == '1' or request.method == 'POST') and activo is not None
    form_data = None
    if request.method == 'POST':
        if not _usuario_gestante() or not perfil:
            abort(403)
        form_data = request.form
        fum = request.form.get('fum') or None
        fpp = request.form.get('fpp') or None
        metodo = request.form.get('metodo_fpp') or ('fum' if fum else None)
        semanas_raw = request.form.get('semanas_gestacion') or None
        dias_raw = request.form.get('dias_gestacion') or None
        edad_ingresada = semanas_raw is not None or (dias_raw is not None and dias_raw != '0')
        fum_fecha = fpp_fecha = None
        if edad_ingresada:
            fum_fecha, fpp_fecha, error = fechas_embarazo_desde_edad_gestacional(
                semanas_raw, dias_raw, request.form.get('fecha_referencia_gestacion') or None
            )
            metodo = 'profesional'
            if error:
                flash(error, 'error')
        elif metodo and metodo not in {'fum', 'ecografia', 'profesional', 'otro'}:
            flash('Método no válido.', 'error')
        else:
            fum_fecha, fpp_fecha, error = validar_fechas_embarazo(fum, fpp, metodo)
            if error:
                flash(error, 'error')
        if fum_fecha is not None or fpp_fecha is not None:
            try:
                destino = activo or Embarazo(perfil_gestante_id=perfil.id, estado='activo')
                destino.fum, destino.fpp, destino.metodo_fpp = fum_fecha, fpp_fecha, metodo
                if not activo:
                    db.session.add(destino)
                db.session.commit()
                return redirect(url_for('main.embarazo'))
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible guardar la información del embarazo.', 'error')
    controles = controles_activos(activo)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp) if activo else None
    proximo = next((control for control in controles if control.fecha_control >= date.today() and control.estado in {'programado', 'reprogramado'}), None)
    return render_template(
        'embarazo.html',
        perfil=perfil,
        embarazo=activo,
        controles=controles,
        proximo=proximo,
        semana=semana,
        editar=editar,
        form_data=form_data,
        date=date.today(),
        min_fum=(date.today() - timedelta(days=42 * 7)).isoformat(),
        min_fpp=(date.today() - timedelta(days=14)).isoformat(),
        max_fpp=(date.today() + timedelta(days=280)).isoformat(),
    )


@main_bp.route('/controles')
@login_required
def controles():
    perfil, activo = perfil_y_embarazo(current_user.id)
    controles = controles_activos(activo)
    hoy = date.today()
    proximos = [control for control in controles if control.fecha_control >= hoy and control.estado in {'programado', 'reprogramado'}]
    proximo = min(proximos, key=lambda control: (control.fecha_control, control.hora_control or datetime.min.time()), default=None)
    anteriores = [c for c in reversed(controles) if c.fecha_control < hoy or c.estado in ('realizado', 'cancelado')]
    dias_para_proximo = (proximo.fecha_control - hoy).days if proximo else None
    return render_template('controles.html', embarazo=activo, controles=controles, proximo=proximo, anteriores=anteriores, dias_para_proximo=dias_para_proximo)


def _resolver_centro_input(texto, centros):
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


def _ordenar_centros_por_zona(centros, perfil):
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


@main_bp.route('/controles/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_control():
    perfil, activo = perfil_y_embarazo(current_user.id)
    if not perfil and activo and hasattr(activo, 'perfil_gestante'):
        perfil = activo.perfil_gestante
    if not activo:
        flash('Necesitas un embarazo activo para registrar un control.', 'error')
        return redirect(url_for('main.controles'))
    centros = _ordenar_centros_por_zona(centros_activos(), perfil)

    ultimo_numero = db.session.scalar(
        db.select(db.func.max(ControlPrenatal.numero_control)).where(ControlPrenatal.embarazo_id == activo.id)
    ) or 0
    siguiente_numero = ultimo_numero + 1

    semana_actual = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp) if activo else None

    inicio_gestacion = fecha_inicio_gestacion(activo.fum, activo.fpp, activo.metodo_fpp) if activo else None
    inicio_gestacion_iso = inicio_gestacion.isoformat() if inicio_gestacion else ''
    hoy = date.today()
    max_control_date = (inicio_gestacion + timedelta(days=42 * 7)).isoformat() if inicio_gestacion else ''
    error_fecha_control = None

    if request.method == 'POST':
        try:
            numero_raw = (request.form.get('numero_control') or '').strip()
            numero = int(numero_raw) if numero_raw else siguiente_numero
            fecha_control = date.fromisoformat(request.form.get('fecha_control', ''))
            hora_raw = request.form.get('hora_control') or None
            hora_control = time.fromisoformat(hora_raw) if hora_raw else None

            centro_input_raw = (request.form.get('centro_nombre_input') or request.form.get('centro_atencion_id') or '').strip()
            if centro_input_raw == 'otro':
                centro_input_raw = (request.form.get('centro_otro_nombre') or '').strip() or 'Puesto de salud comunitario'

            centro_id, centro_personalizado = _resolver_centro_input(centro_input_raw, centros)
            estado = 'programado'
            error_fecha_control = validar_fecha_control(fecha_control, inicio_gestacion, estado, hoy)
            if error_fecha_control:
                raise ValueError

            edad_calc = calcular_semana_gestacional(
                activo.fum,
                activo.fpp,
                hoy=fecha_control,
                metodo_fpp=activo.metodo_fpp,
            )
            edad = float(edad_calc) if edad_calc is not None else None

            tipo_control = (request.form.get('tipo_control') or '').strip()
            indicaciones_texto = (request.form.get('indicaciones') or '').strip()

            partes_indicaciones = []
            if tipo_control and tipo_control != 'Control prenatal regular':
                partes_indicaciones.append(f"[{tipo_control}]")
            if centro_personalizado:
                partes_indicaciones.append(f"[Centro: {centro_personalizado}]")
            if indicaciones_texto:
                partes_indicaciones.append(indicaciones_texto)

            indicaciones_final = " ".join(partes_indicaciones).strip() or None
            notas_final = (request.form.get('notas') or '').strip() or None

            if numero < 1 or (edad is not None and not 0 <= edad <= 42):
                raise ValueError

            db.session.add(ControlPrenatal(
                embarazo_id=activo.id,
                registrado_por_usuario_id=current_user.id,
                numero_control=numero,
                fecha_control=fecha_control,
                hora_control=hora_control,
                edad_gestacional_semanas=edad,
                centro_atencion_id=centro_id,
                estado=estado,
                indicaciones=indicaciones_final,
                notas=notas_final
            ))
            db.session.commit()
            flash('Control agendado con éxito.', 'success')
            return redirect(url_for('main.controles'))
        except (ValueError, TypeError):
            flash(error_fecha_control or 'Revisa los datos del control.', 'error')
        except SQLAlchemyError:
            db.session.rollback()
            flash('Ya existe ese número de control.', 'error')

    centro_nombre_valor = request.form.get('centro_nombre_input', '') if request.method == 'POST' else ''

    return render_template(
        'control_form.html',
        centros=centros,
        centro_nombre_valor=centro_nombre_valor,
        control=None,
        siguiente_numero=siguiente_numero,
        semana_actual=semana_actual,
        inicio_gestacion_iso=inicio_gestacion_iso,
        tipo_control_actual='Control prenatal regular',
        min_control_date=hoy.isoformat(),
        max_control_date=max_control_date,
        form_data=request.form if request.method == 'POST' else None
    )


@main_bp.route('/controles/<int:control_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_control(control_id):
    perfil, activo = perfil_y_embarazo(current_user.id)
    if not perfil and activo and hasattr(activo, 'perfil_gestante'):
        perfil = activo.perfil_gestante
    control = db.session.scalar(
        db.select(ControlPrenatal).where(
            ControlPrenatal.id == control_id,
            ControlPrenatal.embarazo_id == (activo.id if activo else None),
        )
    )
    if not control:
        abort(404)

    centros = _ordenar_centros_por_zona(centros_activos(), perfil)
    semana_actual = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp) if activo else None

    inicio_gestacion = fecha_inicio_gestacion(
        activo.fum if activo else None,
        activo.fpp if activo else None,
        activo.metodo_fpp if activo else None,
    )
    inicio_gestacion_iso = inicio_gestacion.isoformat() if inicio_gestacion else ''
    hoy = date.today()
    max_control_date = (inicio_gestacion + timedelta(days=42 * 7)).isoformat() if inicio_gestacion else ''
    estado_form = request.form.get('estado', control.estado) if request.method == 'POST' else control.estado
    min_control_date = hoy.isoformat() if estado_form in {'programado', 'reprogramado'} else ''
    error_fecha_control = None

    tipo_control_actual = 'Control prenatal regular'
    indicaciones_limpias = control.indicaciones or ''
    for opcion in ['Ultrasonido / Ecografía', 'Exámenes de laboratorio', 'Control prenatal regular']:
        prefijo = f"[{opcion}]"
        if indicaciones_limpias.startswith(prefijo):
            tipo_control_actual = opcion
            indicaciones_limpias = indicaciones_limpias[len(prefijo):].strip()
            break

    centro_otro_actual = ''
    if '[Centro:' in indicaciones_limpias or '[Centro: ' in indicaciones_limpias:
        m = re.search(r'\[Centro:\s*([^\]]+)\]', indicaciones_limpias)
        if m:
            centro_otro_actual = m.group(1).strip()
            indicaciones_limpias = re.sub(r'\[Centro:\s*[^\]]+\]', '', indicaciones_limpias).strip()

    if request.method == 'POST':
        try:
            fecha_control = date.fromisoformat(request.form.get('fecha_control', ''))
            hora_raw = request.form.get('hora_control') or None
            estado = request.form.get('estado', '')

            centro_input_raw = (request.form.get('centro_nombre_input') or request.form.get('centro_atencion_id') or '').strip()
            if centro_input_raw == 'otro':
                centro_input_raw = (request.form.get('centro_otro_nombre') or '').strip() or 'Puesto de salud comunitario'

            centro_id, centro_personalizado = _resolver_centro_input(centro_input_raw, centros)
            if estado not in {'programado', 'realizado', 'reprogramado', 'cancelado'}:
                raise ValueError
            error_fecha_control = validar_fecha_control(fecha_control, inicio_gestacion, estado, hoy)
            if error_fecha_control:
                raise ValueError

            tipo_control = (request.form.get('tipo_control') or '').strip()
            indicaciones_texto = (request.form.get('indicaciones') or '').strip()

            partes_indicaciones = []
            if tipo_control and tipo_control != 'Control prenatal regular':
                partes_indicaciones.append(f"[{tipo_control}]")
            if centro_personalizado:
                partes_indicaciones.append(f"[Centro: {centro_personalizado}]")
            if indicaciones_texto:
                partes_indicaciones.append(indicaciones_texto)

            indicaciones_final = " ".join(partes_indicaciones).strip() or None

            control.fecha_control = fecha_control
            control.hora_control = time.fromisoformat(hora_raw) if hora_raw else None
            control.estado = estado
            control.centro_atencion_id = centro_id
            control.indicaciones = indicaciones_final
            control.notas = (request.form.get('notas') or '').strip() or None

            if activo and (activo.fum or activo.fpp):
                edad_calc = calcular_semana_gestacional(activo.fum, activo.fpp, hoy=fecha_control, metodo_fpp=activo.metodo_fpp)
                if edad_calc is not None:
                    control.edad_gestacional_semanas = float(edad_calc)

            db.session.commit()
            flash('Control actualizado.', 'success')
            return redirect(url_for('main.controles'))
        except (ValueError, TypeError):
            db.session.rollback()
            flash(error_fecha_control or 'Revisa la fecha, hora, estado y centro del control.', 'error')
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible actualizar el control.', 'error')

    semana_estimada_control = int(control.edad_gestacional_semanas) if control.edad_gestacional_semanas is not None else None

    if request.method == 'POST':
        centro_nombre_valor = request.form.get('centro_nombre_input', '')
    else:
        c_atencion = getattr(control, 'centro_atencion', None)
        if c_atencion:
            c_mun = (getattr(c_atencion, 'municipio', None) or '').strip()
            centro_nombre_valor = f"{c_atencion.nombre} ({c_mun})" if c_mun else c_atencion.nombre
        elif getattr(control, 'centro_atencion_id', None):
            c_obj = centro_activo(control.centro_atencion_id)
            if c_obj:
                c_mun = (getattr(c_obj, 'municipio', None) or '').strip()
                centro_nombre_valor = f"{c_obj.nombre} ({c_mun})" if c_mun else c_obj.nombre
            else:
                centro_nombre_valor = ''
        elif centro_otro_actual:
            centro_nombre_valor = centro_otro_actual
        else:
            centro_nombre_valor = ''

    return render_template(
        'control_form.html',
        centros=centros,
        centro_nombre_valor=centro_nombre_valor,
        control=control,
        siguiente_numero=control.numero_control,
        semana_actual=semana_actual,
        semana_estimada=semana_estimada_control,
        inicio_gestacion_iso=inicio_gestacion_iso,
        min_control_date=min_control_date,
        max_control_date=max_control_date,
        tipo_control_actual=tipo_control_actual,
        indicaciones_limpias=indicaciones_limpias,
        form_data=request.form if request.method == 'POST' else None
    )


@main_bp.get('/consulta/imprimir')
@login_required
def imprimir_consulta():
    """Hoja imprimible con logística y preguntas pendientes de la cuenta."""
    if not _usuario_gestante():
        abort(403)
    control = construir_inicio(current_user.id)["control"]
    if not control:
        flash('No tienes una próxima consulta para preparar.', 'error')
        return redirect(url_for('main.index'))
    preguntas = db.session.scalars(
        db.select(PreguntaConsulta)
        .where(
            PreguntaConsulta.usuario_id == current_user.id,
            PreguntaConsulta.estado == 'pendiente',
        )
        .order_by(PreguntaConsulta.id)
    ).all()
    return render_template('consulta_impresa.html', control=control, preguntas=preguntas)


@main_bp.get('/consulta/preparar')
@login_required
def detalle_consulta():
    if not _usuario_gestante():
        abort(403)
    control = construir_inicio(current_user.id)["control"]
    if not control:
        flash('No tienes una próxima consulta para preparar.', 'error')
        return redirect(url_for('main.index'))
    return render_template('consulta_detalle.html', control=control)


PLAN_PARTO_TRANSPORTES = {
    'propio': 'Vehículo propio',
    'familiar_vecino': 'Apoyo de familiar o vecino',
    'publico_colectivo': 'Transporte público / bus / panga',
    'caponera_taxi': 'Taxi o caponera local',
    'ambulancia_minsa': 'Coordinación con ambulancia del MINSA',
    'otro': 'Otro medio acordado',
}


@main_bp.route('/plan-parto', methods=['GET', 'POST'])
@login_required
def plan_parto():
    """Visualización y edición de la logística familiar para acudir a la atención."""
    if not _usuario_gestante():
        abort(403)

    perfil, activo = perfil_y_embarazo(current_user.id)
    if not activo:
        flash('Necesitas un embarazo registrado para organizar tu traslado y apoyo.', 'error')
        return redirect(url_for('main.embarazo'))

    plan = activo.plan_parto
    centros = centros_activos()
    modo_editar = request.args.get('editar') == '1' or not plan or request.method == 'POST'

    if request.method == 'POST':
        centro_raw = (request.form.get('centro_atencion_id') or '').strip()
        centro_id = request.form.get('centro_atencion_id', type=int)
        casa_materna = 1 if request.form.get('requiere_casa_materna') in ('1', 'on', 'true') else 0
        acompanante_nombre = (request.form.get('acompanante_nombre') or '').strip()[:150] or None
        acompanante_tel = (request.form.get('acompanante_telefono') or '').strip()[:30] or None
        cuidador = (request.form.get('cuidador_hijos') or '').strip()[:150] or None
        transporte = request.form.get('transporte_tipo') or 'familiar_vecino'
        transporte_contacto = (request.form.get('transporte_contacto') or '').strip()[:150] or None
        transporte_telefono = (request.form.get('transporte_telefono') or '').strip()[:30] or None
        if transporte_contacto and transporte_telefono:
            transporte_contacto = f'{transporte_contacto} - {transporte_telefono}'[:150]
        bulto = 1 if request.form.get('bulto_listo') in ('1', 'on', 'true') else 0
        recursos = 1 if request.form.get('recursos_traslado_listos') in ('1', 'on', 'true') else 0
        notas = (request.form.get('notas') or '').strip()[:500] or None

        if transporte not in PLAN_PARTO_TRANSPORTES:
            flash('Selecciona un medio de transporte válido.', 'error')
            return render_template('plan_parto.html', plan=plan, embarazo=activo, centros=centros, contactos=perfil.contactos_comunitarios if perfil else [], roles=ROLES_COMUNITARIOS, transportes=PLAN_PARTO_TRANSPORTES, editar=True, form_data=request.form)

        if (centro_raw and centro_id is None) or (centro_id and not centro_activo(centro_id)):
            flash('El centro de atención seleccionado no es válido.', 'error')
            return render_template('plan_parto.html', plan=plan, embarazo=activo, centros=centros, contactos=perfil.contactos_comunitarios if perfil else [], roles=ROLES_COMUNITARIOS, transportes=PLAN_PARTO_TRANSPORTES, editar=True, form_data=request.form)

        try:
            if not plan:
                plan = PlanParto(embarazo_id=activo.id)
                db.session.add(plan)

            plan.centro_atencion_id = centro_id
            plan.requiere_casa_materna = casa_materna
            plan.acompanante_nombre = acompanante_nombre
            plan.acompanante_telefono = acompanante_tel
            plan.cuidador_hijos = cuidador
            plan.transporte_tipo = transporte
            plan.transporte_contacto = transporte_contacto
            plan.bulto_listo = bulto
            plan.recursos_traslado_listos = recursos
            plan.notas = notas

            db.session.commit()
            flash('Plan de traslado y apoyo guardado.', 'success')
            return redirect(url_for('main.plan_parto'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible guardar el plan de traslado y apoyo.', 'error')
            return render_template('plan_parto.html', plan=plan, embarazo=activo, centros=centros, contactos=perfil.contactos_comunitarios if perfil else [], roles=ROLES_COMUNITARIOS, transportes=PLAN_PARTO_TRANSPORTES, editar=True, form_data=request.form)

    return render_template(
        'plan_parto.html',
        plan=plan,
        embarazo=activo,
        centros=centros,
        contactos=perfil.contactos_comunitarios if perfil else [],
        roles=ROLES_COMUNITARIOS,
        transportes=PLAN_PARTO_TRANSPORTES,
        editar=modo_editar and (not plan or request.args.get('editar') == '1'),
    )


@main_bp.get('/plan-parto/imprimir')
@login_required
def imprimir_plan_parto():
    """Ficha imprimible con la logística y contactos elegidos por la usuaria."""
    if not _usuario_gestante():
        abort(403)

    perfil, activo = perfil_y_embarazo(current_user.id)
    if not activo or not activo.plan_parto:
        flash('Registra primero tu plan de traslado y apoyo para poder imprimirlo.', 'error')
        return redirect(url_for('main.plan_parto'))

    semana = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp)
    return render_template(
        'plan_parto_impreso.html',
        plan=activo.plan_parto,
        embarazo=activo,
        perfil=perfil,
        semana=semana,
        transportes=PLAN_PARTO_TRANSPORTES,
        roles=ROLES_COMUNITARIOS,
    )


ROLES_COMUNITARIOS = {
    'brigadista': 'Contacto comunitario',
    'partera': 'Acompañante de confianza',
    'promotor_salud': 'Persona de apoyo',
    'traslado_local': 'Transporte',
    'lider_comunitario': 'Referente comunitario',
    'vecino_apoyo': 'Familiar, vecina o vecino',
    'otro': 'Otro contacto',
}


def _validar_contacto_comunitario(form):
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


def _contacto_propio(contacto_id, perfil):
    """Busca un contacto verificando que pertenezca al perfil autenticado."""
    return db.session.scalar(
        db.select(ContactoComunitario).where(
            ContactoComunitario.id == contacto_id,
            ContactoComunitario.perfil_gestante_id == (perfil.id if perfil else None),
        )
    )


@main_bp.get('/red-comunitaria')
@login_required
def red_comunitaria():
    """Contactos personales elegidos por la usuaria para acompañamiento y traslado."""
    if not _usuario_gestante():
        abort(403)
    perfil, activo = perfil_y_embarazo(current_user.id)
    contactos = perfil.contactos_comunitarios if perfil else []
    return render_template(
        'red_comunitaria.html',
        perfil=perfil,
        embarazo=activo,
        contactos=contactos,
        roles=ROLES_COMUNITARIOS,
    )


@main_bp.route('/red-comunitaria/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_contacto_comunitario():
    if not _usuario_gestante():
        abort(403)
    perfil, _ = perfil_y_embarazo(current_user.id)
    if not perfil:
        flash('Necesitas un perfil gestante para registrar tu red de apoyo.', 'error')
        return redirect(url_for('main.embarazo'))
    if request.method == 'POST':
        datos, error = _validar_contacto_comunitario(request.form)
        if error:
            flash(error, 'error')
        else:
            try:
                db.session.add(ContactoComunitario(perfil_gestante_id=perfil.id, **datos))
                db.session.commit()
                flash('Contacto de apoyo agregado.', 'success')
                return redirect(url_for('main.red_comunitaria'))
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible guardar el contacto.', 'error')
    return render_template(
        'contacto_comunitario_form.html',
        contacto=None,
        roles=ROLES_COMUNITARIOS,
        form_data=request.form if request.method == 'POST' else None,
    )


@main_bp.route('/red-comunitaria/<int:contacto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_contacto_comunitario(contacto_id):
    if not _usuario_gestante():
        abort(403)
    perfil, _ = perfil_y_embarazo(current_user.id)
    contacto = _contacto_propio(contacto_id, perfil)
    if not contacto:
        abort(404)
    if request.method == 'POST':
        datos, error = _validar_contacto_comunitario(request.form)
        if error:
            flash(error, 'error')
        else:
            contacto.nombre = datos['nombre']
            contacto.rol = datos['rol']
            contacto.telefono = datos['telefono']
            contacto.comunidad_barrio = datos['comunidad_barrio']
            contacto.notas = datos['notas']
            try:
                db.session.commit()
                flash('Contacto actualizado.', 'success')
                return redirect(url_for('main.red_comunitaria'))
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible actualizar el contacto.', 'error')
    return render_template(
        'contacto_comunitario_form.html',
        contacto=contacto,
        roles=ROLES_COMUNITARIOS,
        form_data=request.form if request.method == 'POST' else None,
    )


@main_bp.post('/red-comunitaria/<int:contacto_id>/eliminar')
@login_required
def eliminar_contacto_comunitario(contacto_id):
    if not _usuario_gestante():
        abort(403)
    perfil, _ = perfil_y_embarazo(current_user.id)
    contacto = _contacto_propio(contacto_id, perfil)
    if not contacto:
        abort(404)
    try:
        db.session.delete(contacto)
        db.session.commit()
        flash('Contacto eliminado.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('No fue posible eliminar el contacto.', 'error')
    return redirect(url_for('main.red_comunitaria'))


PREGUNTA_MAX_CARACTERES = 500


def _renderizar_preguntas(pregunta_borrador="", editar_id=None, error=None, status=200, preguntas=None):
    if preguntas is None:
        preguntas = db.session.scalars(
            db.select(PreguntaConsulta)
            .where(PreguntaConsulta.usuario_id == current_user.id)
            .order_by(PreguntaConsulta.estado, PreguntaConsulta.id)
        ).all()
    return render_template(
        'preguntas.html',
        preguntas=preguntas,
        pregunta_borrador=pregunta_borrador,
        editar_id=editar_id,
        pregunta_error=error,
        max_caracteres=PREGUNTA_MAX_CARACTERES,
    ), status


@main_bp.route('/preguntas', methods=['GET', 'POST'])
@login_required
def preguntas_consulta():
    if not _usuario_gestante():
        abort(403)
    if request.method == 'GET':
        editar_id = request.args.get('editar', type=int)
        if editar_id is not None:
            pregunta = db.session.scalar(
                db.select(PreguntaConsulta).where(
                    PreguntaConsulta.id == editar_id,
                    PreguntaConsulta.usuario_id == current_user.id,
                    PreguntaConsulta.estado == 'pendiente',
                )
            )
            if pregunta is None:
                abort(404)
        return _renderizar_preguntas(editar_id=editar_id)

    pregunta = (request.form.get('pregunta') or '').strip()
    if not pregunta or len(pregunta) > PREGUNTA_MAX_CARACTERES:
        return _renderizar_preguntas(
            pregunta,
            error=f'Escribe una pregunta de hasta {PREGUNTA_MAX_CARACTERES} caracteres.',
            status=400,
        )
    try:
        db.session.add(PreguntaConsulta(usuario_id=current_user.id, pregunta=pregunta, estado='pendiente'))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return _renderizar_preguntas(
            pregunta,
            error='No fue posible guardar. Conservamos el texto para que puedas intentarlo de nuevo.',
            status=503,
        )
    flash('Pregunta guardada para una próxima consulta.', 'success')
    return redirect(url_for('main.preguntas_consulta'))


@main_bp.post('/preguntas/<int:pregunta_id>')
@login_required
def actualizar_pregunta(pregunta_id):
    if not _usuario_gestante():
        abort(403)
    pregunta_guardada = db.session.scalar(
        db.select(PreguntaConsulta).where(
            PreguntaConsulta.id == pregunta_id,
            PreguntaConsulta.usuario_id == current_user.id,
        )
    )
    if not pregunta_guardada:
        abort(404)

    accion = request.form.get('accion')
    if accion == 'editar':
        pregunta = (request.form.get('pregunta') or '').strip()
        if not pregunta or len(pregunta) > PREGUNTA_MAX_CARACTERES:
            return _renderizar_preguntas(
                pregunta,
                editar_id=pregunta_id,
                error=f'Escribe una pregunta de hasta {PREGUNTA_MAX_CARACTERES} caracteres.',
                status=400,
            )
        pregunta_guardada.pregunta = pregunta
    elif accion == 'estado':
        estado = request.form.get('estado')
        if estado not in {'pendiente', 'conversada'}:
            abort(400)
        pregunta_guardada.estado = estado
    elif accion == 'eliminar':
        db.session.delete(pregunta_guardada)
    else:
        abort(400)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        draft = request.form.get('pregunta', '') if accion == 'editar' else ''
        return _renderizar_preguntas(
            draft,
            editar_id=pregunta_id if accion == 'editar' else None,
            error='No fue posible guardar el cambio. Inténtalo de nuevo.',
            status=503,
        )
    flash('Pregunta eliminada.' if accion == 'eliminar' else 'Pregunta actualizada.', 'success')
    return redirect(url_for('main.preguntas_consulta'))


@main_bp.route('/calendario')
@login_required
def calendario():
    _, activo = perfil_y_embarazo(current_user.id)
    recordatorios = recordatorios_pendientes(current_user.id)
    return render_template('calendario.html', embarazo=activo, controles=controles_activos(activo), recordatorios=recordatorios)


@main_bp.route('/recordatorios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_recordatorio():
    if not _usuario_gestante():
        abort(403)

    _, activo = perfil_y_embarazo(current_user.id)
    controles = controles_activos(activo)
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip() or None
        tipo = request.form.get('tipo', 'personal')
        fecha_hora_raw = request.form.get('fecha_hora', '').strip()
        control_raw = request.form.get('control_prenatal_id', '').strip()

        try:
            fecha_hora = datetime.fromisoformat(fecha_hora_raw)
            control_id = int(control_raw) if control_raw else None
            if (
                not titulo
                or len(titulo) > 150
                or len(descripcion or '') > 500
                or fecha_hora <= datetime.now()
                or tipo not in {'control', 'personal', 'informativo'}
            ):
                raise ValueError
            if control_id is not None and not activo:
                raise ValueError
            control = None
            if control_id is not None:
                control = db.session.scalar(
                    db.select(ControlPrenatal).where(
                        ControlPrenatal.id == control_id,
                        ControlPrenatal.embarazo_id == activo.id,
                    )
                )
                if not control:
                    raise ValueError

            db.session.add(
                Recordatorio(
                    usuario_id=current_user.id,
                    control_prenatal_id=control.id if control else None,
                    titulo=titulo,
                    descripcion=descripcion,
                    tipo=tipo,
                    fecha_hora=fecha_hora,
                    estado='pendiente',
                )
            )
            db.session.commit()
            flash('Recordatorio creado correctamente.', 'success')
            return redirect(url_for('main.calendario'))
        except (ValueError, TypeError):
            db.session.rollback()
            flash('Revisa el título, la fecha, el tipo y el control asociado.', 'error')
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible guardar el recordatorio.', 'error')

    return render_template('recordatorio_form.html', controles=controles, form_data=request.form if request.method == 'POST' else None)


@main_bp.route('/guia')
def guia():
    activo = None
    if current_user.is_authenticated:
        _, activo = perfil_y_embarazo(current_user.id)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp) if activo else None

    publicados = contenidos_publicados()
    orientaciones = [
        {
            "id": f"pub-{c.id}",
            "titulo": c.titulo,
            "resumen": c.resumen or "",
            "cuerpo": c.contenido,
            "categoria": c.categoria,
            "trimestre": c.trimestre,
            "fuente_nombre": c.fuente_nombre,
            "fuente_url": c.fuente_url,
            "fecha_revision": c.fecha_revision.strftime('%d/%m/%Y') if c.fecha_revision else None,
            "es_borrador": False,
        }
        for c in publicados
    ]

    borradores = []
    if _es_cuenta_demo():
        borradores = [
            {
                **item,
                "fuente_nombre": FUENTES.get(item["fuente"], {}).get("nombre", "Fuente sin registrar"),
                "fuente_url": FUENTES.get(item["fuente"], {}).get("url", "#"),
            }
            for item in BORRADORES
        ]
        for item in borradores:
            orientaciones.append({
                "id": f"demo-{item['id']}",
                "titulo": item["titulo"],
                "resumen": item["texto"][:120] + ("…" if len(item["texto"]) > 120 else ""),
                "cuerpo": item["texto"],
                "categoria": item["categoria"].capitalize(),
                "trimestre": item.get("trimestre"),
                "fuente_nombre": item["fuente_nombre"],
                "fuente_url": item["fuente_url"],
                "fecha_revision": f"consultada {FECHA_CONSULTA}",
                "es_borrador": True,
            })

    return render_template(
        'guia.html',
        orientaciones=orientaciones,
        contenidos=publicados,
        borradores=borradores,
        fecha_consulta=FECHA_CONSULTA,
        semana=semana,
    )


@main_bp.route('/guia/<int:contenido_id>')
def detalle_guia(contenido_id):
    abort(404)


@main_bp.route('/alertas')
def alertas():
    senales = []
    if _es_cuenta_demo():
        from demo_nicaragua import SENALES_ALERTA
        senales = SENALES_ALERTA
    return render_template('alertas.html', senales=senales)


@main_bp.route('/centros')
def centros():
    centros = centros_activos()
    departamentos = sorted(list(set(c.departamento for c in centros if getattr(c, "departamento", None))))

    departamento_usuario = None
    if current_user.is_authenticated:
        perfil, _ = perfil_y_embarazo(current_user.id)
        if perfil and perfil.departamento:
            departamento_usuario = perfil.departamento

    return render_template(
        'centros.html',
        centros=centros,
        departamentos=departamentos,
        departamento_usuario=departamento_usuario,
        es_demo=_es_cuenta_demo(),
        q=(request.args.get('q') or '').strip()[:80],
        tipo=(request.args.get('tipo') or '').strip(),
        departamento=(request.args.get('departamento') or '').strip()[:100],
    )


@main_bp.route('/centros/<int:centro_id>')
def detalle_centro(centro_id):
    centro = centro_activo(centro_id)
    if not centro: abort(404)
    return render_template('centro_detalle.html', centro=centro, servicios=servicios_disponibles(centro.id))


@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    perfil_actual, embarazo_actual = perfil_y_embarazo(current_user.id)
    if request.method == 'POST':
        if not _usuario_gestante():
            abort(403)
        consentimiento = request.form.get('consentimiento_datos', '0')
        if consentimiento not in {'0', '1'}:
            abort(400)
        nacimiento_raw = request.form.get('fecha_nacimiento') or None
        fecha_invalida = False
        try:
            nacimiento = date.fromisoformat(nacimiento_raw) if nacimiento_raw else None
        except ValueError:
            nacimiento = None
            fecha_invalida = True
            flash('La fecha de nacimiento no es válida.', 'error')
        if nacimiento and nacimiento > date.today():
            flash('La fecha de nacimiento no puede estar en el futuro.', 'error')
            nacimiento = None
            fecha_invalida = True
        if fecha_invalida:
            semana = calcular_semana_gestacional(embarazo_actual.fum, embarazo_actual.fpp, metodo_fpp=embarazo_actual.metodo_fpp) if embarazo_actual else None
            return render_template(
                'perfil.html',
                perfil=perfil_actual,
                embarazo=embarazo_actual,
                semana=semana,
                cedula=None,
                es_gestante=True,
                form_data=request.form,
                date=date.today(),
            )
        perfil_actual = perfil_actual or PerfilGestante(usuario_id=current_user.id)
        nueva_cedula = (request.form.get('cedula') or '').strip()[:20] or None
        if nueva_cedula is not None or not perfil_actual.cedula:
            perfil_actual.cedula = nueva_cedula
        perfil_actual.fecha_nacimiento = nacimiento
        perfil_actual.telefono = (request.form.get('telefono') or '').strip()[:30] or None
        perfil_actual.direccion_residencia = (request.form.get('direccion_residencia') or '').strip() or None
        perfil_actual.municipio = (request.form.get('municipio') or '').strip()[:100] or None
        perfil_actual.departamento = (request.form.get('departamento') or '').strip()[:100] or None
        perfil_actual.contacto_emergencia_nombre = (request.form.get('contacto_emergencia_nombre') or '').strip()[:150] or None
        perfil_actual.contacto_emergencia_telefono = (request.form.get('contacto_emergencia_telefono') or '').strip()[:30] or None
        nuevo_consentimiento = int(consentimiento)
        if nuevo_consentimiento == 1 and not perfil_actual.consentimiento_datos:
            perfil_actual.fecha_consentimiento = datetime.now()
        elif nuevo_consentimiento == 0:
            perfil_actual.fecha_consentimiento = None
        perfil_actual.consentimiento_datos = nuevo_consentimiento
        if not perfil_actual.id: db.session.add(perfil_actual)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible actualizar el perfil.', 'error')
        else:
            flash('Perfil actualizado.', 'success')
            return redirect(url_for('main.perfil'))
    cedula = None
    if perfil_actual and perfil_actual.cedula:
        cedula = '*' * max(0, len(perfil_actual.cedula) - 4) + perfil_actual.cedula[-4:]
    semana = calcular_semana_gestacional(embarazo_actual.fum, embarazo_actual.fpp, metodo_fpp=embarazo_actual.metodo_fpp) if embarazo_actual else None
    return render_template(
        'perfil.html',
        perfil=perfil_actual,
        embarazo=embarazo_actual,
        semana=semana,
        cedula=cedula,
        es_gestante=_usuario_gestante(),
        form_data=None,
        date=date.today(),
    )

@main_bp.post('/perfil/cambiar-password')
@login_required
def cambiar_password():
    actual = request.form.get('password_actual', '')
    nueva = request.form.get('password_nueva', '')
    confirmacion = request.form.get('password_confirm', '')
    if not current_user.verificar_password(actual):
        flash('La contraseña actual no es correcta.', 'error')
    elif len(nueva) < 8 or nueva != confirmacion:
        flash('La nueva contraseña debe tener al menos 8 caracteres y coincidir.', 'error')
    else:
        current_user.password_hash = generate_password_hash(nueva)
        try:
            db.session.commit()
            flash('Contraseña actualizada.', 'success')
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible actualizar la contraseña.', 'error')
    return redirect(url_for('main.perfil'))


# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


@main_bp.route('/offline.html')
def offline():
    return send_from_directory('static', 'offline.html')


@main_bp.route('/fuentes')
def fuentes():
    return render_template(
        'informacion.html',
        titulo='Fuentes de información',
        icono='menu_book',
        contenido=[
            'Aurora organiza información de acompañamiento prenatal para fines educativos.',
            'Las señales de alerta y recomendaciones deben revisarse con profesionales de la salud antes de usarse en un contexto real.',
            'El contenido publicado incluye la fuente y la fecha de revisión registrada por el equipo administrador.',
        ],
        contexto=CONTEXTO,
        fuentes=FUENTES,
        fecha_consulta=FECHA_CONSULTA,
    )


@main_bp.route('/privacidad')
def privacidad():
    return render_template(
        'informacion.html',
        titulo='Privacidad',
        icono='shield',
        contenido=[
            'Aurora utiliza los datos del perfil y del embarazo para mostrar el seguimiento de la cuenta autenticada.',
            'No compartas datos clínicos reales en esta versión de demostración.',
            'Antes de un uso real deben definirse la política de privacidad, la retención y la eliminación de datos.',
        ],
    )


@main_bp.route('/acerca')
def acerca():
    return render_template(
        'informacion.html',
        titulo='Acerca de Aurora',
        icono='help',
        contenido=[
            'Aurora es un puente organizativo entre la vida diaria de una gestante y su atención prenatal.',
            'Ayuda a recordar controles, preparar preguntas y coordinar el traslado y las personas de apoyo elegidas por la usuaria.',
            'No interpreta síntomas, diagnostica, prescribe, recomienda tratamientos ni reemplaza al personal o a los servicios de salud.',
            'Es una demostración para validar si estas tareas simples ayudan a llegar mejor preparada y acompañada a la atención profesional.',
        ],
    )


@main_bp.route('/demo/revision-clinica')
@admin_required
def revision_clinica():
    return render_template(
        'revision_clinica.html',
        fuentes=FUENTES,
        borradores=BORRADORES,
        contexto=CONTEXTO,
        fecha_consulta=FECHA_CONSULTA,
    )
