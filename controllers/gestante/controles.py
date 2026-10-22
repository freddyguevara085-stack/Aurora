"""Rutas de controles prenatales y preparación de próxima consulta."""

from datetime import date, time, timedelta

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.seguimiento import ControlPrenatal, PreguntaConsulta
from services.gestacion import (
    construir_indicaciones,
    descomponer_indicaciones,
    ordenar_centros_por_zona,
    proximo_control_activo,
    resolver_centro_input,
    validar_fecha_control,
)


@main_bp.route('/controles')
@login_required
def controles():
    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
    embarazo_mostrado = activo or (_pkg.ultimo_embarazo_con_nacimiento(perfil.id) if perfil else None)
    lista_controles = _pkg.controles_activos(embarazo_mostrado)
    hoy = _pkg.date.today()
    proximo = proximo_control_activo(lista_controles, hoy=hoy) if activo else None
    anteriores = (
        list(reversed(lista_controles))
        if not activo
        else [
            c
            for c in reversed(lista_controles)
            if c.fecha_control < hoy or c.estado in ('realizado', 'cancelado')
        ]
    )
    dias_para_proximo = (proximo.fecha_control - hoy).days if proximo else None
    return render_template(
        'controles.html',
        embarazo=embarazo_mostrado,
        puede_agendar=bool(activo),
        controles=lista_controles,
        proximo=proximo,
        anteriores=anteriores,
        siguientes=[c for c in lista_controles
                    if activo and c.estado in ('programado', 'reprogramado')
                    and c.fecha_control >= hoy and (not proximo or c.id != proximo.id)],
        dias_para_proximo=dias_para_proximo,
    )


@main_bp.route('/controles/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_control():
    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
    if not perfil and activo and hasattr(activo, 'perfil_gestante'):
        perfil = activo.perfil_gestante
    if not activo:
        flash('Necesitas un embarazo activo para registrar un control.', 'error')
        return redirect(url_for('main.controles'))
    centros = ordenar_centros_por_zona(_pkg.centros_activos(), perfil)

    try:
        ultimo_numero = db.session.scalar(
            db.select(db.func.max(ControlPrenatal.numero_control)).where(ControlPrenatal.embarazo_id == activo.id)
        ) or 0
    except SQLAlchemyError:
        db.session.rollback()
        ultimo_numero = 0
    siguiente_numero = ultimo_numero + 1

    hoy = _pkg.date.today()
    semana_actual = (
        _pkg.calcular_semana_gestacional(activo.fum, activo.fpp, hoy=hoy, metodo_fpp=activo.metodo_fpp)
        if activo
        else None
    )
    inicio_gestacion = _pkg.fecha_inicio_gestacion(activo.fum, activo.fpp, activo.metodo_fpp) if activo else None
    inicio_gestacion_iso = inicio_gestacion.isoformat() if inicio_gestacion else ''
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

            edad_calc = _pkg.calcular_semana_gestacional(
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
                notas=notas_final,
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
        form_data=request.form if request.method == 'POST' else None,
    )


@main_bp.route('/controles/<int:control_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_control(control_id):
    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
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

    centros = ordenar_centros_por_zona(_pkg.centros_activos(), perfil)
    hoy = _pkg.date.today()
    semana_actual = (
        _pkg.calcular_semana_gestacional(activo.fum, activo.fpp, hoy=hoy, metodo_fpp=activo.metodo_fpp)
        if activo
        else None
    )

    inicio_gestacion = _pkg.fecha_inicio_gestacion(
        activo.fum if activo else None,
        activo.fpp if activo else None,
        activo.metodo_fpp if activo else None,
    )
    inicio_gestacion_iso = inicio_gestacion.isoformat() if inicio_gestacion else ''
    max_control_date = (inicio_gestacion + timedelta(days=42 * 7)).isoformat() if inicio_gestacion else ''
    estado_form = request.form.get('estado', control.estado) if request.method == 'POST' else control.estado
    min_control_date = hoy.isoformat() if estado_form in {'programado', 'reprogramado'} else ''
    error_fecha_control = None

    tipo_control_actual, centro_otro_actual, indicaciones_limpias = descomponer_indicaciones(
        control.indicaciones
    )

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
                edad_calc = _pkg.calcular_semana_gestacional(
                    activo.fum,
                    activo.fpp,
                    hoy=fecha_control,
                    metodo_fpp=activo.metodo_fpp,
                )
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

    semana_estimada_control = (
        int(control.edad_gestacional_semanas)
        if control.edad_gestacional_semanas is not None
        else None
    )

    if request.method == 'POST':
        centro_nombre_valor = request.form.get('centro_nombre_input', '')
    else:
        c_atencion = getattr(control, 'centro_atencion', None)
        if c_atencion:
            c_mun = (getattr(c_atencion, 'municipio', None) or '').strip()
            centro_nombre_valor = f"{c_atencion.nombre} ({c_mun})" if c_mun else c_atencion.nombre
        elif getattr(control, 'centro_atencion_id', None):
            c_obj = _pkg.centro_activo(control.centro_atencion_id)
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
        form_data=request.form if request.method == 'POST' else None,
    )


@main_bp.get('/consulta/imprimir')
@login_required
def imprimir_consulta():
    """Hoja imprimible con logística y preguntas pendientes de la cuenta."""
    if not _pkg._usuario_gestante():
        abort(403)
    control = _pkg.construir_inicio(current_user.id)["control"]
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
    if not _pkg._usuario_gestante():
        abort(403)
    control = _pkg.construir_inicio(current_user.id)["control"]
    if not control:
        flash('No tienes una próxima consulta para preparar.', 'error')
        return redirect(url_for('main.index'))
    return render_template('consulta_detalle.html', control=control)
