"""CRUD del catálogo de servicios del panel de administración."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from controllers.admin import admin_bp
from controllers.admin._common import _alternar
from controllers.decorators import admin_required
from extensions import db
from models.directorio import Servicio
from services.auditoria import registrar_auditoria


def validar_datos_servicio(form_data, servicio_actual_id=None):
    """Valida y limpia los datos del formulario de servicio."""
    errores = []

    nombre = (form_data.get("nombre") or "").strip()
    if not nombre:
        errores.append("El nombre del servicio es obligatorio.")
    elif len(nombre) > 120:
        errores.append("El nombre del servicio no puede exceder 120 caracteres.")
    else:
        existente = db.session.scalar(
            select(Servicio).where(Servicio.nombre == nombre)
        )
        if existente and (not servicio_actual_id or existente.id != servicio_actual_id):
            errores.append("Ya existe otro servicio registrado con ese nombre.")

    descripcion = (form_data.get("descripcion") or "").strip() or None
    if descripcion and len(descripcion) > 500:
        errores.append("La descripción no puede exceder 500 caracteres.")

    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0

    datos = {
        "nombre": nombre,
        "descripcion": descripcion,
        "activo": activo,
    }

    return datos, errores


@admin_bp.route("/servicios")
@admin_required
def servicios():
    """Listado general del catálogo de servicios para administración."""
    lista_servicios = db.session.scalars(
        select(Servicio).order_by(Servicio.nombre)
    ).all()

    return render_template("admin/servicios/index.html", servicios=lista_servicios)


@admin_bp.route("/servicios/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo_servicio():
    """Creación de un nuevo servicio en el catálogo."""
    if request.method == "POST":
        datos, errores = validar_datos_servicio(request.form)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template("admin/servicios/form.html", servicio=None, form_data=request.form, accion="crear")

        try:
            nuevo = Servicio(**datos)
            db.session.add(nuevo)
            db.session.flush()
            registrar_auditoria(
                usuario_id=current_user.id,
                accion="crear",
                entidad="servicios",
                registro_id=nuevo.id,
                detalles={"nombre": nuevo.nombre},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Servicio «{nuevo.nombre}» registrado exitosamente.", "success")
            return redirect(url_for("admin.servicios"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al registrar el servicio.", "error")
            return render_template("admin/servicios/form.html", servicio=None, form_data=request.form, accion="crear")

    return render_template("admin/servicios/form.html", servicio=None, form_data=None, accion="crear")


@admin_bp.route("/servicios/<int:servicio_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_servicio(servicio_id):
    """Edición de un servicio existente."""
    item = db.session.get(Servicio, servicio_id)
    if not item:
        abort(404)

    if request.method == "POST":
        datos, errores = validar_datos_servicio(request.form, servicio_actual_id=item.id)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template("admin/servicios/form.html", servicio=item, form_data=request.form, accion="editar")

        try:
            for campo, valor in datos.items():
                setattr(item, campo, valor)

            registrar_auditoria(
                usuario_id=current_user.id,
                accion="actualizar",
                entidad="servicios",
                registro_id=item.id,
                detalles={"nombre": item.nombre},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Servicio «{item.nombre}» actualizado correctamente.", "success")
            return redirect(url_for("admin.servicios"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al actualizar el servicio.", "error")
            return render_template("admin/servicios/form.html", servicio=item, form_data=request.form, accion="editar")

    return render_template("admin/servicios/form.html", servicio=item, form_data=None, accion="editar")


@admin_bp.route("/servicios/<int:servicio_id>/toggle", methods=["POST"])
@admin_required
def toggle_servicio(servicio_id):
    """Alterna el estado activo / inactivo de un servicio."""
    item = db.session.get(Servicio, servicio_id)
    if not item:
        abort(404)
    return _alternar(
        item,
        "activo",
        "servicios",
        {1: "El servicio ha sido activado.", 0: "El servicio ha sido desactivado."},
        "admin.servicios",
        mensaje_error="No se pudo cambiar el estado del servicio.",
    )


@admin_bp.route("/servicios/<int:servicio_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_servicio(servicio_id):
    """Elimina un servicio si no se encuentra asignado a centros de atención."""
    item = db.session.get(Servicio, servicio_id)
    if not item:
        abort(404)

    nombre = item.nombre
    try:
        db.session.delete(item)
        registrar_auditoria(
            usuario_id=current_user.id,
            accion="eliminar",
            entidad="servicios",
            registro_id=servicio_id,
            detalles={"nombre": nombre},
            ip=request.remote_addr,
        )
        db.session.commit()

        flash(f"Servicio «{nombre}» eliminado del catálogo.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        # Si está asignado a centros, se desactiva
        item.activo = 0
        try:
            registrar_auditoria(
                usuario_id=current_user.id,
                accion="desactivar_por_dependencias",
                entidad="servicios",
                registro_id=servicio_id,
                detalles={"nombre": nombre, "motivo": "Asignado a centros de salud"},
                ip=request.remote_addr,
            )
            db.session.commit()
            flash(f"El servicio «{nombre}» está asignado a centros de salud, por lo que fue desactivado en lugar de eliminado.", "warning")
        except SQLAlchemyError:
            db.session.rollback()
            flash("No fue posible procesar la eliminación del servicio.", "error")

    return redirect(url_for("admin.servicios"))
