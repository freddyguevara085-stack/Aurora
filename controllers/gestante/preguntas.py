"""Rutas de preguntas privadas para futuras consultas."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError, SQLAlchemyError

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.seguimiento import PreguntaConsulta


def _renderizar_preguntas(pregunta_borrador="", editar_id=None, error=None, status=200, preguntas=None):
    if preguntas is None:
        try:
            preguntas = db.session.scalars(
                db.select(PreguntaConsulta)
                .where(PreguntaConsulta.usuario_id == current_user.id)
                .order_by(PreguntaConsulta.estado, PreguntaConsulta.id)
            ).all()
        except OperationalError:
            db.session.rollback()
            preguntas = []
    return render_template(
        'preguntas.html',
        preguntas=preguntas,
        pregunta_borrador=pregunta_borrador,
        editar_id=editar_id,
        pregunta_error=error,
        max_caracteres=_pkg.PREGUNTA_MAX_CARACTERES,
    ), status


@main_bp.route('/preguntas', methods=['GET', 'POST'])
@login_required
def preguntas_consulta():
    if not _pkg._usuario_gestante():
        abort(403)
    if request.method == 'GET':
        editar_id = request.args.get('editar', type=int)
        borrador = ''
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
            borrador = pregunta.pregunta
        return _renderizar_preguntas(pregunta_borrador=borrador, editar_id=editar_id)

    max_len = _pkg.PREGUNTA_MAX_CARACTERES
    pregunta = (request.form.get('pregunta') or '').strip()
    if not pregunta or len(pregunta) > max_len:
        return _renderizar_preguntas(
            pregunta,
            error=f'Escribe una pregunta de hasta {max_len} caracteres.',
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
    if not _pkg._usuario_gestante():
        abort(403)
    pregunta_guardada = db.session.scalar(
        db.select(PreguntaConsulta).where(
            PreguntaConsulta.id == pregunta_id,
            PreguntaConsulta.usuario_id == current_user.id,
        )
    )
    if not pregunta_guardada:
        abort(404)

    max_len = _pkg.PREGUNTA_MAX_CARACTERES
    accion = request.form.get('accion')
    if accion == 'editar':
        pregunta = (request.form.get('pregunta') or '').strip()
        if not pregunta or len(pregunta) > max_len:
            return _renderizar_preguntas(
                pregunta,
                editar_id=pregunta_id,
                error=f'Escribe una pregunta de hasta {max_len} caracteres.',
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
