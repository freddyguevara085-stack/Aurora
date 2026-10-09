"""CRUD de señales de alerta del panel de administración."""

from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from controllers.admin import admin_bp
from controllers.admin._common import _alternar, _url_fuente_valida
from controllers.decorators import admin_required
from extensions import db
from models.contenido import SenalAlerta
from services.auditoria import registrar_auditoria


def validar_datos_senal(form_data):
    """Valida y limpia los datos del formulario de señal de alerta."""
    errores = []

    titulo = (form_data.get("titulo") or "").strip()
    if not titulo:
        errores.append("El título es obligatorio.")
    elif len(titulo) > 180:
        errores.append("El título no puede exceder 180 caracteres.")

    descripcion = (form_data.get("descripcion") or "").strip()
    if not descripcion:
        errores.append("La descripción de la señal es obligatoria.")

    accion_recomendada = (form_data.get("accion_recomendada") or "").strip()
    if not accion_recomendada:
        errores.append("La acción recomendada es obligatoria.")

    orden_raw = (form_data.get("orden_visual") or "0").strip()
    orden_visual = 0
    try:
        orden_visual = int(orden_raw)
        if not (0 <= orden_visual <= 65535):
            errores.append("El orden visual debe ser un número entero entre 0 y 65535.")
    except ValueError:
        errores.append("El orden visual debe ser un número entero.")

    fuente_nombre = (form_data.get("fuente_nombre") or "").strip()
    if not fuente_nombre:
        errores.append("El nombre de la fuente es obligatorio.")
    elif len(fuente_nombre) > 180:
        errores.append("El nombre de la fuente no puede exceder 180 caracteres.")

    fuente_url = (form_data.get("fuente_url") or "").strip() or None
    if fuente_url and len(fuente_url) > 500:
        errores.append("La URL de la fuente no puede exceder 500 caracteres.")
    if not _url_fuente_valida(fuente_url):
        errores.append("La URL de la fuente debe usar HTTP o HTTPS.")

    fecha_rev_raw = (form_data.get("fecha_revision") or "").strip()
    fecha_revision = None
    if not fecha_rev_raw:
        errores.append("La fecha de revisión médica es obligatoria.")
    else:
        try:
            fecha_revision = date.fromisoformat(fecha_rev_raw)
        except ValueError:
            errores.append("La fecha de revisión debe tener formato AAAA-MM-DD válido.")

    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0

    datos = {
        "titulo": titulo,
        "descripcion": descripcion,
        "accion_recomendada": accion_recomendada,
        "orden_visual": orden_visual,
        "fuente_nombre": fuente_nombre,
        "fuente_url": fuente_url,
        "fecha_revision": fecha_revision,
        "activo": activo,
    }

    return datos, errores


@admin_bp.route("/senales")
@admin_required
def senales():
    """Listado general de señales de alerta para administración."""
    estado = request.args.get("estado", "").strip()
    query = select(SenalAlerta)

    if estado == "activa":
        query = query.where(SenalAlerta.activo == 1)
    elif estado == "inactiva":
        query = query.where(SenalAlerta.activo == 0)

    lista_senales = db.session.scalars(
        query.order_by(SenalAlerta.orden_visual.asc(), SenalAlerta.id.asc())
    ).all()

    return render_template("admin/senales/index.html", senales=lista_senales, estado_actual=estado)


@admin_bp.route("/senales/nueva", methods=["GET", "POST"])
@admin_required
def nueva_senal():
    """Creación de una nueva señal de alerta."""
    if request.method == "POST":
        datos, errores = validar_datos_senal(request.form)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template(
                "admin/senales/form.html",
                senal=None,
                form_data=request.form,
                accion="crear",
            )

        try:
            nueva = SenalAlerta(
                creado_por_usuario_id=current_user.id,
                **datos
            )
            db.session.add(nueva)
            db.session.flush()
            registrar_auditoria(
                usuario_id=current_user.id,
                accion="crear",
                entidad="senales_alerta",
                registro_id=nueva.id,
                detalles={"titulo": nueva.titulo, "activo": nueva.activo},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Señal de alerta «{nueva.titulo}» registrada exitosamente.", "success")
            return redirect(url_for("admin.senales"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al registrar la señal de alerta.", "error")
            return render_template(
                "admin/senales/form.html",
                senal=None,
                form_data=request.form,
                accion="crear",
            )

    return render_template("admin/senales/form.html", senal=None, form_data=None, accion="crear")


@admin_bp.route("/senales/<int:senal_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_senal(senal_id):
    """Edición de una señal de alerta existente."""
    item = db.session.get(SenalAlerta, senal_id)
    if not item:
        abort(404)

    if request.method == "POST":
        datos, errores = validar_datos_senal(request.form)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template(
                "admin/senales/form.html",
                senal=item,
                form_data=request.form,
                accion="editar",
            )

        try:
            for campo, valor in datos.items():
                setattr(item, campo, valor)
            item.actualizado_por_usuario_id = current_user.id

            registrar_auditoria(
                usuario_id=current_user.id,
                accion="actualizar",
                entidad="senales_alerta",
                registro_id=item.id,
                detalles={"titulo": item.titulo, "activo": item.activo},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Señal de alerta «{item.titulo}» actualizada correctamente.", "success")
            return redirect(url_for("admin.senales"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al actualizar la señal de alerta.", "error")
            return render_template(
                "admin/senales/form.html",
                senal=item,
                form_data=request.form,
                accion="editar",
            )

    return render_template("admin/senales/form.html", senal=item, form_data=None, accion="editar")


@admin_bp.route("/senales/<int:senal_id>/toggle", methods=["POST"])
@admin_required
def toggle_senal(senal_id):
    """Alterna el estado activo / inactivo de una señal de alerta."""
    item = db.session.get(SenalAlerta, senal_id)
    if not item:
        abort(404)
    return _alternar(
        item,
        "activo",
        "senales_alerta",
        {1: "La señal de alerta ha sido activada.", 0: "La señal de alerta ha sido desactivada."},
        "admin.senales",
        mensaje_error="No se pudo cambiar el estado de la señal de alerta.",
    )


@admin_bp.route("/senales/<int:senal_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_senal(senal_id):
    """Elimina una señal de alerta del sistema."""
    item = db.session.get(SenalAlerta, senal_id)
    if not item:
        abort(404)

    titulo = item.titulo
    try:
        db.session.delete(item)
        registrar_auditoria(
            usuario_id=current_user.id,
            accion="eliminar",
            entidad="senales_alerta",
            registro_id=senal_id,
            detalles={"titulo": titulo},
            ip=request.remote_addr,
        )
        db.session.commit()

        flash(f"Señal de alerta «{titulo}» eliminada del sistema.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No fue posible eliminar la señal de alerta.", "error")

    return redirect(url_for("admin.senales"))
