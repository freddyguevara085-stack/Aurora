"""Rutas de la red comunitaria y personal de apoyo."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.gestacion import ContactoComunitario
from services.gestacion import ROLES_COMUNITARIOS, contacto_propio, validar_contacto_comunitario


@main_bp.get('/red-comunitaria')
@login_required
def red_comunitaria():
    """Contactos personales elegidos por la usuaria para acompañamiento y traslado."""
    if not _pkg._usuario_gestante():
        abort(403)
    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
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
    if not _pkg._usuario_gestante():
        abort(403)
    perfil, _ = _pkg.perfil_y_embarazo(current_user.id)
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
    if not _pkg._usuario_gestante():
        abort(403)
    perfil, _ = _pkg.perfil_y_embarazo(current_user.id)
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
    if not _pkg._usuario_gestante():
        abort(403)
    perfil, _ = _pkg.perfil_y_embarazo(current_user.id)
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
