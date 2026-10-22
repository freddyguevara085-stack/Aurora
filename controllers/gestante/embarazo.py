"""Rutas del seguimiento del embarazo y registro de nacimiento."""

from datetime import timedelta

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.gestacion import Embarazo
from services.gestacion import (
    fechas_embarazo_desde_edad_gestacional,
    proximo_control_activo,
    seguimiento_fecha_parto,
    validar_fecha_nacimiento_real,
    validar_fechas_embarazo,
)


@main_bp.route('/embarazo', methods=['GET', 'POST'])
@login_required
def embarazo():
    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
    editar = (request.args.get('editar') == '1' or request.method == 'POST') and activo is not None
    form_data = None
    hoy = _pkg.date.today()

    if request.method == 'POST':
        if not _pkg._usuario_gestante() or not perfil:
            abort(403)
        form_data = request.form
        fum = request.form.get('fum') or None
        semanas_raw = request.form.get('semanas_gestacion') or None
        dias_raw = request.form.get('dias_gestacion') or None
        fuente = request.form.get('fuente_fecha')
        edad_ingresada = semanas_raw is not None or (dias_raw is not None and dias_raw != '0')
        fum_fecha = fpp_fecha = None
        error = None
        if fuente not in (None, 'periodo', 'consulta'):
            error = 'Elige la fecha de tu período o las semanas de tu consulta.'
        elif fuente == 'consulta' and not edad_ingresada and activo and activo.metodo_fpp in ('profesional', 'ecografia', 'otro'):
            # Guardar sin escribir nuevas semanas conserva las fechas existentes.
            fum_fecha, fpp_fecha, metodo = activo.fum, activo.fpp, activo.metodo_fpp
        elif fuente == 'consulta' or (fuente is None and edad_ingresada):
            fum_fecha, fpp_fecha, error = fechas_embarazo_desde_edad_gestacional(
                semanas_raw,
                dias_raw,
                request.form.get('fecha_referencia_gestacion') or None,
                hoy=hoy,
            )
            metodo = 'profesional'
        else:
            metodo = 'fum' if fuente == 'periodo' else (activo.metodo_fpp if activo and activo.metodo_fpp else ('fum' if fum else None))
            fpp_existente = activo.fpp if fuente is None and activo and activo.metodo_fpp != 'fum' else None
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
                flash('Los datos de tu embarazo se guardaron.', 'success')
                return redirect(url_for('main.embarazo'))
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible guardar la información del embarazo.', 'error')

    embarazo_mostrado = activo or (_pkg.ultimo_embarazo_con_nacimiento(perfil.id) if perfil else None)
    controles = _pkg.controles_activos(embarazo_mostrado)
    semana = (
        _pkg.calcular_semana_gestacional(activo.fum, activo.fpp, hoy=hoy, metodo_fpp=activo.metodo_fpp)
        if activo
        else None
    )
    fecha_nac_real = getattr(embarazo_mostrado, 'fecha_nacimiento_real', None) if embarazo_mostrado else None
    semana_al_nacimiento = (
        _pkg.calcular_semana_gestacional(
            embarazo_mostrado.fum,
            embarazo_mostrado.fpp,
            hoy=fecha_nac_real,
            metodo_fpp=embarazo_mostrado.metodo_fpp,
        )
        if embarazo_mostrado and fecha_nac_real
        else None
    )
    proximo = proximo_control_activo(controles, hoy=hoy) if activo else None

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
        date=hoy,
        min_fum=(hoy - timedelta(days=42 * 7)).isoformat(),
        min_fpp=(hoy - timedelta(days=14)).isoformat(),
        max_fpp=(hoy + timedelta(days=280)).isoformat(),
        seguimiento=seguimiento_fecha_parto(
            embarazo_mostrado.fpp if embarazo_mostrado else None,
            fecha_nac_real,
            hoy=hoy,
        ) if embarazo_mostrado else None,
    )


@main_bp.route('/embarazo/nacimiento', methods=['GET', 'POST'])
@login_required
def registrar_nacimiento():
    """Registra o corrige la fecha real sin modificar la FPP estimada."""
    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
    embarazo_actual = activo or (_pkg.ultimo_embarazo_con_nacimiento(perfil.id) if perfil else None)
    if not perfil or not embarazo_actual:
        flash('Necesitas un embarazo registrado para anotar el nacimiento.', 'error')
        return redirect(url_for('main.embarazo'))

    hoy = _pkg.date.today()
    if request.method == 'POST':
        if not _pkg._usuario_gestante():
            abort(403)
        fecha_real, error = validar_fecha_nacimiento_real(
            request.form.get('fecha_nacimiento_real'),
            hoy=hoy,
        )
        if error:
            flash(error, 'error')
        else:
            try:
                embarazo_actual.fecha_nacimiento_real = fecha_real
                embarazo_actual.fecha_fin = fecha_real
                embarazo_actual.estado = 'finalizado'
                db.session.commit()
                flash('La fecha real del nacimiento fue guardada. La fecha probable se conserva como estimación.', 'success')
                return redirect(url_for('main.embarazo'))
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible guardar la fecha real del nacimiento.', 'error')

    return render_template(
        'nacimiento_form.html',
        embarazo=embarazo_actual,
        seguimiento=seguimiento_fecha_parto(
            embarazo_actual.fpp,
            getattr(embarazo_actual, 'fecha_nacimiento_real', None),
            hoy=hoy,
        ),
        form_data=request.form if request.method == 'POST' else None,
        date=hoy,
    )
