"""CRUD de centros de atención del panel de administración."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from controllers.admin import admin_bp
from controllers.admin._common import _alternar
from controllers.decorators import admin_required
from extensions import db
from models.directorio import CentroAtencion, Servicio
from models.seguimiento import ControlPrenatal
from services.admin import (
    TIPOS_ESTABLECIMIENTO_VALIDOS,
    _sincronizar_servicios_centro,
    validar_datos_centro,
)
from services.auditoria import registrar_auditoria


@admin_bp.route("/centros")
@admin_required
def centros():
    """Listado general de centros de atención para administración."""
    busqueda = (request.args.get("q") or "").strip()
    tipo = (request.args.get("tipo") or "").strip()
    estado = (request.args.get("estado") or "").strip()

    query = select(CentroAtencion)

    if busqueda:
        termino = f"%{busqueda[:80]}%"
        query = query.where(
            or_(
                CentroAtencion.nombre.ilike(termino),
                CentroAtencion.municipio.ilike(termino),
                CentroAtencion.departamento.ilike(termino),
            )
        )
    if tipo in TIPOS_ESTABLECIMIENTO_VALIDOS:
        query = query.where(CentroAtencion.tipo_establecimiento == tipo)
    if estado == "activo":
        query = query.where(CentroAtencion.activo == 1)
    elif estado == "inactivo":
        query = query.where(CentroAtencion.activo == 0)

    lista_centros = db.session.scalars(
        query.order_by(CentroAtencion.departamento, CentroAtencion.municipio, CentroAtencion.nombre)
    ).all()

    return render_template(
        "admin/centros/index.html",
        centros=lista_centros,
        busqueda_actual=busqueda,
        tipo_actual=tipo,
        estado_actual=estado,
    )


@admin_bp.route("/centros/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo_centro():
    """Creación de un nuevo centro de atención con asignación de servicios."""
    catalogo_servicios = db.session.scalars(
        select(Servicio).where(Servicio.activo == 1).order_by(Servicio.nombre)
    ).all()

    if request.method == "POST":
        datos, servicios_ids, errores = validar_datos_centro(request.form)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template(
                "admin/centros/form.html",
                centro=None,
                servicios=catalogo_servicios,
                servicios_asignados_ids=set(servicios_ids),
                form_data=request.form,
                accion="crear",
            )

        try:
            nuevo = CentroAtencion(**datos)
            db.session.add(nuevo)
            db.session.flush()
            _sincronizar_servicios_centro(nuevo.id, servicios_ids, datos["fecha_verificacion"])

            registrar_auditoria(
                usuario_id=current_user.id,
                accion="crear",
                entidad="centros_atencion",
                registro_id=nuevo.id,
                detalles={"nombre": nuevo.nombre, "municipio": nuevo.municipio, "servicios_count": len(servicios_ids)},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Centro de salud «{nuevo.nombre}» registrado exitosamente.", "success")
            return redirect(url_for("admin.centros"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al registrar el centro de salud.", "error")
            return render_template(
                "admin/centros/form.html",
                centro=None,
                servicios=catalogo_servicios,
                servicios_asignados_ids=set(servicios_ids),
                form_data=request.form,
                accion="crear",
            )

    return render_template(
        "admin/centros/form.html",
        centro=None,
        servicios=catalogo_servicios,
        servicios_asignados_ids=set(),
        form_data=None,
        accion="crear",
    )


@admin_bp.route("/centros/<int:centro_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_centro(centro_id):
    """Edición de un centro de atención existente y sus servicios asignados."""
    item = db.session.get(CentroAtencion, centro_id)
    if not item:
        abort(404)

    catalogo_servicios = db.session.scalars(
        select(Servicio).where(Servicio.activo == 1).order_by(Servicio.nombre)
    ).all()

    if request.method == "POST":
        datos, servicios_ids, errores = validar_datos_centro(request.form, centro_actual_id=item.id)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template(
                "admin/centros/form.html",
                centro=item,
                servicios=catalogo_servicios,
                servicios_asignados_ids=set(servicios_ids),
                form_data=request.form,
                accion="editar",
            )

        try:
            for campo, valor in datos.items():
                setattr(item, campo, valor)

            _sincronizar_servicios_centro(item.id, servicios_ids, datos["fecha_verificacion"])

            registrar_auditoria(
                usuario_id=current_user.id,
                accion="actualizar",
                entidad="centros_atencion",
                registro_id=item.id,
                detalles={"nombre": item.nombre, "municipio": item.municipio, "servicios_count": len(servicios_ids)},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Centro de salud «{item.nombre}» actualizado correctamente.", "success")
            return redirect(url_for("admin.centros"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al actualizar el centro de salud.", "error")
            return render_template(
                "admin/centros/form.html",
                centro=item,
                servicios=catalogo_servicios,
                servicios_asignados_ids=set(servicios_ids),
                form_data=request.form,
                accion="editar",
            )

    servicios_actuales_ids = {cs.servicio_id for cs in item.asignaciones_servicios if cs.disponible}
    return render_template(
        "admin/centros/form.html",
        centro=item,
        servicios=catalogo_servicios,
        servicios_asignados_ids=servicios_actuales_ids,
        form_data=None,
        accion="editar",
    )


@admin_bp.route("/centros/<int:centro_id>/toggle", methods=["POST"])
@admin_required
def toggle_centro(centro_id):
    """Alterna el estado activo / inactivo de un centro de atención."""
    item = db.session.get(CentroAtencion, centro_id)
    if not item:
        abort(404)
    return _alternar(
        item,
        "activo",
        "centros_atencion",
        {1: "El centro de salud ha sido activado.", 0: "El centro de salud ha sido desactivado."},
        "admin.centros",
        mensaje_error="No se pudo cambiar el estado del centro de salud.",
    )


@admin_bp.route("/centros/<int:centro_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_centro(centro_id):
    """Desactiva o elimina un centro de atención verificando integridad referencial."""
    item = db.session.get(CentroAtencion, centro_id)
    if not item:
        abort(404)

    nombre = item.nombre
    tiene_controles = db.session.scalar(
        db.select(ControlPrenatal.id).where(ControlPrenatal.centro_atencion_id == centro_id).limit(1)
    )

    try:
        if tiene_controles:
            item.activo = 0
            registrar_auditoria(
                usuario_id=current_user.id,
                accion="desactivar_por_dependencias",
                entidad="centros_atencion",
                registro_id=centro_id,
                detalles={"nombre": nombre, "motivo": "Tiene controles asociados"},
                ip=request.remote_addr,
            )
            db.session.commit()
            flash(f"El centro «{nombre}» tiene controles asociados, por lo que fue desactivado en lugar de eliminado.", "warning")
        else:
            db.session.delete(item)
            registrar_auditoria(
                usuario_id=current_user.id,
                accion="eliminar",
                entidad="centros_atencion",
                registro_id=centro_id,
                detalles={"nombre": nombre},
                ip=request.remote_addr,
            )
            db.session.commit()
            flash(f"Centro «{nombre}» eliminado del sistema.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No fue posible procesar la eliminación del centro.", "error")

    return redirect(url_for("admin.centros"))
