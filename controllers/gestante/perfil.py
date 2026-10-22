"""Rutas de perfil de la gestante y cambio de contraseña."""

from datetime import date, datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.gestacion import PerfilGestante
from services.gestacion import enmascarar_identificacion, formatear_identificacion


@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    perfil_actual, embarazo_actual = _pkg.perfil_y_embarazo(current_user.id)
    hoy = _pkg.date.today()

    if request.method == 'POST':
        if not _pkg._usuario_gestante():
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
        if nacimiento and nacimiento > hoy:
            flash('La fecha de nacimiento no puede estar en el futuro.', 'error')
            nacimiento = None
            fecha_invalida = True
        if fecha_invalida:
            semana = (
                _pkg.calcular_semana_gestacional(
                    embarazo_actual.fum,
                    embarazo_actual.fpp,
                    hoy=hoy,
                    metodo_fpp=embarazo_actual.metodo_fpp,
                )
                if embarazo_actual
                else None
            )
            return render_template(
                'perfil.html',
                perfil=perfil_actual,
                embarazo=embarazo_actual,
                semana=semana,
                cedula=None,
                es_gestante=True,
                form_data=request.form,
                date=hoy,
            )

        perfil_actual = perfil_actual or PerfilGestante(usuario_id=current_user.id)
        nueva_cedula = formatear_identificacion(request.form.get('cedula'))
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
        if not perfil_actual.id:
            db.session.add(perfil_actual)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible actualizar el perfil.', 'error')
        else:
            flash('Perfil actualizado.', 'success')
            return redirect(url_for('main.perfil'))

    cedula = enmascarar_identificacion(perfil_actual.cedula) if perfil_actual and perfil_actual.cedula else None
    semana = (
        _pkg.calcular_semana_gestacional(
            embarazo_actual.fum,
            embarazo_actual.fpp,
            hoy=hoy,
            metodo_fpp=embarazo_actual.metodo_fpp,
        )
        if embarazo_actual
        else None
    )
    return render_template(
        'perfil.html',
        perfil=perfil_actual,
        embarazo=embarazo_actual,
        semana=semana,
        cedula=cedula,
        es_gestante=_pkg._usuario_gestante(),
        form_data=None,
        date=hoy,
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
