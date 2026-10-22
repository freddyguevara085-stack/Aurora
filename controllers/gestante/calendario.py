"""Rutas de calendario y recordatorios personales."""

from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.seguimiento import ControlPrenatal, Recordatorio


@main_bp.route('/calendario')
@login_required
def calendario():
    _, activo = _pkg.perfil_y_embarazo(current_user.id)
    recordatorios = _pkg.recordatorios_pendientes(current_user.id)
    return render_template(
        'calendario.html',
        embarazo=activo,
        controles=_pkg.controles_activos(activo),
        recordatorios=recordatorios,
    )


@main_bp.route('/recordatorios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_recordatorio():
    if not _pkg._usuario_gestante():
        abort(403)

    _, activo = _pkg.perfil_y_embarazo(current_user.id)
    controles = _pkg.controles_activos(activo)
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

    return render_template(
        'recordatorio_form.html',
        controles=controles,
        form_data=request.form if request.method == 'POST' else None,
    )
