"""Rutas del plan de parto y traslado comunitario."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

import controllers.gestante as _pkg
from controllers.blueprints import main_bp
from extensions import db
from models.gestacion import PlanParto
from services.gestacion import PLAN_PARTO_TRANSPORTES, ROLES_COMUNITARIOS


@main_bp.route('/plan-parto', methods=['GET', 'POST'])
@login_required
def plan_parto():
    """Visualización y edición de la logística familiar para acudir a la atención."""
    if not _pkg._usuario_gestante():
        abort(403)

    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
    if not activo:
        flash('Necesitas un embarazo registrado para organizar tu traslado y apoyo.', 'error')
        return redirect(url_for('main.embarazo'))

    plan = activo.plan_parto
    modo_editar = request.args.get('editar') == '1' or not plan or request.method == 'POST'
    centros = _pkg.centros_activos() if modo_editar else []
    contactos = perfil.contactos_comunitarios if perfil else []

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
            return render_template(
                'plan_parto.html',
                plan=plan,
                embarazo=activo,
                centros=centros,
                contactos=contactos,
                roles=ROLES_COMUNITARIOS,
                transportes=PLAN_PARTO_TRANSPORTES,
                editar=True,
                form_data=request.form,
            )

        if (centro_raw and centro_id is None) or (centro_id and not _pkg.centro_activo(centro_id)):
            flash('El centro de atención seleccionado no es válido.', 'error')
            return render_template(
                'plan_parto.html',
                plan=plan,
                embarazo=activo,
                centros=centros,
                contactos=contactos,
                roles=ROLES_COMUNITARIOS,
                transportes=PLAN_PARTO_TRANSPORTES,
                editar=True,
                form_data=request.form,
            )

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
            return render_template(
                'plan_parto.html',
                plan=plan,
                embarazo=activo,
                centros=centros,
                contactos=contactos,
                roles=ROLES_COMUNITARIOS,
                transportes=PLAN_PARTO_TRANSPORTES,
                editar=True,
                form_data=request.form,
            )

    return render_template(
        'plan_parto.html',
        plan=plan,
        embarazo=activo,
        centros=centros,
        contactos=contactos,
        roles=ROLES_COMUNITARIOS,
        transportes=PLAN_PARTO_TRANSPORTES,
        editar=modo_editar and (not plan or request.args.get('editar') == '1'),
    )


@main_bp.get('/plan-parto/imprimir')
@login_required
def imprimir_plan_parto():
    """Ficha imprimible con la logística y contactos elegidos por la usuaria."""
    if not _pkg._usuario_gestante():
        abort(403)

    perfil, activo = _pkg.perfil_y_embarazo(current_user.id)
    if not activo or not activo.plan_parto:
        flash('Registra primero tu plan de traslado y apoyo para poder imprimirlo.', 'error')
        return redirect(url_for('main.plan_parto'))

    semana = _pkg.calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp)
    return render_template(
        'plan_parto_impreso.html',
        plan=activo.plan_parto,
        embarazo=activo,
        perfil=perfil,
        semana=semana,
        transportes=PLAN_PARTO_TRANSPORTES,
        roles=ROLES_COMUNITARIOS,
    )
