"""Rutas de los flujos de la gestante (embarazo, controles, apoyo y perfil).

Controlador delgado: recibe la petición, delega las reglas de negocio en
``services/gestacion.py`` y devuelve la plantilla correspondiente.
"""

from datetime import date, datetime, time, timedelta
import re

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from controllers.blueprints import main_bp
from controllers.decorators import usuario_gestante as _usuario_gestante
from extensions import db
from models.gestacion import ContactoComunitario, Embarazo, PerfilGestante, PlanParto
from models.seguimiento import ControlPrenatal, PreguntaConsulta, Recordatorio
from services.gestacion import (
    PLAN_PARTO_TRANSPORTES,
    PREGUNTA_MAX_CARACTERES,
    ROLES_COMUNITARIOS,
    contacto_propio,
    construir_indicaciones,
    fechas_embarazo_desde_edad_gestacional,
    ordenar_centros_por_zona,
    resolver_centro_input,
    seguimiento_fecha_parto,
    validar_contacto_comunitario,
    validar_fecha_control,
    validar_fecha_nacimiento_real,
    validar_fechas_embarazo,
)
from services.home import calcular_semana_gestacional, construir_inicio, fecha_inicio_gestacion
from services.mvp import (
    centros_activos,
    centro_activo,
    controles_activos,
    ultimo_embarazo_con_nacimiento,
    perfil_y_embarazo,
    recordatorios_pendientes,
)


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
        else:
            # La FPP no proviene del formulario: se calcula desde la FUM o se
            # conserva si ya fue registrada mediante otro método de estimación.
            metodo = activo.metodo_fpp if activo and activo.metodo_fpp else ('fum' if fum else None)
            fpp_existente = activo.fpp if activo and activo.metodo_fpp != 'fum' else None
            fum_fecha, fpp_fecha, error = validar_fechas_embarazo(fum, fpp_existente, metodo)
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
    embarazo_mostrado = activo or (ultimo_embarazo_con_nacimiento(perfil.id) if perfil else None)
    controles = controles_activos(embarazo_mostrado)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp) if activo else None
    semana_al_nacimiento = (
        calcular_semana_gestacional(
            embarazo_mostrado.fum,
            embarazo_mostrado.fpp,
            hoy=embarazo_mostrado.fecha_nacimiento_real,
            metodo_fpp=embarazo_mostrado.metodo_fpp,
        )
        if embarazo_mostrado and embarazo_mostrado.fecha_nacimiento_real
        else None
    )
    proximo = next((control for control in controles if activo and control.fecha_control >= date.today() and control.estado in {'programado', 'reprogramado'}), None)
    return render_template(
        'embarazo.html',
        perfil=perfil,
        embarazo=embarazo_mostrado,
        controles=controles,
        proximo=proximo,
        semana=semana,
        semana_al_nacimiento=semana_al_nacimiento,
        editar=editar,
        form_data=form_data,
        date=date.today(),
        min_fum=(date.today() - timedelta(days=42 * 7)).isoformat(),
        min_fpp=(date.today() - timedelta(days=14)).isoformat(),
        max_fpp=(date.today() + timedelta(days=280)).isoformat(),
        seguimiento=seguimiento_fecha_parto(
            embarazo_mostrado.fpp if embarazo_mostrado else None,
            getattr(embarazo_mostrado, 'fecha_nacimiento_real', None),
        ) if embarazo_mostrado else None,
    )


@main_bp.route('/embarazo/nacimiento', methods=['GET', 'POST'])
@login_required
def registrar_nacimiento():
    """Registra o corrige la fecha real sin modificar la FPP estimada."""
    perfil, activo = perfil_y_embarazo(current_user.id)
    embarazo = activo or (ultimo_embarazo_con_nacimiento(perfil.id) if perfil else None)
    if not perfil or not embarazo:
        flash('Necesitas un embarazo registrado para anotar el nacimiento.', 'error')
        return redirect(url_for('main.embarazo'))
    if request.method == 'POST':
        if not _usuario_gestante():
            abort(403)
        fecha_real, error = validar_fecha_nacimiento_real(request.form.get('fecha_nacimiento_real'))
        if error:
            flash(error, 'error')
        else:
            try:
                embarazo.fecha_nacimiento_real = fecha_real
                embarazo.fecha_fin = fecha_real
                embarazo.estado = 'finalizado'
                db.session.commit()
                flash('La fecha real del nacimiento fue guardada. La fecha probable se conserva como estimación.', 'success')
                return redirect(url_for('main.embarazo'))
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible guardar la fecha real del nacimiento.', 'error')
    return render_template(
        'nacimiento_form.html',
        embarazo=embarazo,
        seguimiento=seguimiento_fecha_parto(
            embarazo.fpp,
            getattr(embarazo, 'fecha_nacimiento_real', None),
        ),
        form_data=request.form if request.method == 'POST' else None,
        date=date.today(),
    )


@main_bp.route('/controles')
@login_required
def controles():
    perfil, activo = perfil_y_embarazo(current_user.id)
    embarazo_mostrado = activo or (ultimo_embarazo_con_nacimiento(perfil.id) if perfil else None)
    controles = controles_activos(embarazo_mostrado)
    hoy = date.today()
    proximos = [control for control in controles if activo and control.fecha_control >= hoy and control.estado in {'programado', 'reprogramado'}]
    proximo = min(proximos, key=lambda control: (control.fecha_control, control.hora_control or datetime.min.time()), default=None)
    anteriores = list(reversed(controles)) if not activo else [c for c in reversed(controles) if c.fecha_control < hoy or c.estado in ('realizado', 'cancelado')]
    dias_para_proximo = (proximo.fecha_control - hoy).days if proximo else None
    return render_template('controles.html', embarazo=embarazo_mostrado, puede_agendar=bool(activo), controles=controles, proximo=proximo, anteriores=anteriores, dias_para_proximo=dias_para_proximo)


@main_bp.route('/controles/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_control():
    perfil, activo = perfil_y_embarazo(current_user.id)
    if not perfil and activo and hasattr(activo, 'perfil_gestante'):
        perfil = activo.perfil_gestante
    if not activo:
        flash('Necesitas un embarazo activo para registrar un control.', 'error')
        return redirect(url_for('main.controles'))
    centros = ordenar_centros_por_zona(centros_activos(), perfil)

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

            centro_id, centro_personalizado = resolver_centro_input(centro_input_raw, centros)
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

            indicaciones_final = construir_indicaciones(tipo_control, centro_personalizado, indicaciones_texto)
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

    centros = ordenar_centros_por_zona(centros_activos(), perfil)
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

            centro_id, centro_personalizado = resolver_centro_input(centro_input_raw, centros)
            if estado not in {'programado', 'realizado', 'reprogramado', 'cancelado'}:
                raise ValueError
            error_fecha_control = validar_fecha_control(fecha_control, inicio_gestacion, estado, hoy)
            if error_fecha_control:
                raise ValueError

            tipo_control = (request.form.get('tipo_control') or '').strip()
            indicaciones_texto = (request.form.get('indicaciones') or '').strip()

            indicaciones_final = construir_indicaciones(tipo_control, centro_personalizado, indicaciones_texto)

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
        datos, error = validar_contacto_comunitario(request.form)
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
    contacto = contacto_propio(contacto_id, perfil)
    if not contacto:
        abort(404)
    if request.method == 'POST':
        datos, error = validar_contacto_comunitario(request.form)
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
    contacto = contacto_propio(contacto_id, perfil)
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
