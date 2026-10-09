"""CRUD de centros de atención del panel de administración."""

from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from controllers.admin import admin_bp
from controllers.admin._common import _alternar
from controllers.decorators import admin_required
from extensions import db
from models.directorio import CentroAtencion, CentroServicio, Servicio
from models.seguimiento import ControlPrenatal
from services.auditoria import registrar_auditoria


def validar_datos_centro(form_data, centro_actual_id=None):
    """Valida y limpia los datos del formulario de centro de salud."""
    errores = []

    nombre = (form_data.get("nombre") or "").strip()
    if not nombre:
        errores.append("El nombre del centro de salud es obligatorio.")
    elif len(nombre) > 150:
        errores.append("El nombre no puede exceder 150 caracteres.")

    codigo_minsa = (form_data.get("codigo_minsa") or "").strip() or None
    if codigo_minsa:
        if len(codigo_minsa) > 20:
            errores.append("El código MINSA no puede exceder 20 caracteres.")
        else:
            existente = db.session.scalar(
                select(CentroAtencion).where(CentroAtencion.codigo_minsa == codigo_minsa)
            )
            if existente and (not centro_actual_id or existente.id != centro_actual_id):
                errores.append("Ya existe otro centro registrado con ese código MINSA.")

    tipo = (form_data.get("tipo_establecimiento") or "").strip()
    tipos_validos = {"hospital", "centro_salud", "puesto_salud", "casa_materna", "clinica", "otro"}
    if tipo not in tipos_validos:
        errores.append("El tipo de establecimiento seleccionado no es válido.")

    silais = (form_data.get("silais") or "").strip() or None
    if silais and len(silais) > 100:
        errores.append("El SILAIS no puede exceder 100 caracteres.")

    municipio = (form_data.get("municipio") or "").strip()
    if not municipio:
        errores.append("El municipio es obligatorio.")
    elif len(municipio) > 100:
        errores.append("El municipio no puede exceder 100 caracteres.")

    departamento = (form_data.get("departamento") or "").strip()
    if not departamento:
        errores.append("El departamento es obligatorio.")
    elif len(departamento) > 100:
        errores.append("El departamento no puede exceder 100 caracteres.")

    direccion = (form_data.get("direccion") or "").strip() or None
    telefono = (form_data.get("telefono") or "").strip() or None
    if telefono and len(telefono) > 30:
        errores.append("El teléfono no puede exceder 30 caracteres.")

    horario = (form_data.get("horario") or "").strip() or None
    if horario and len(horario) > 255:
        errores.append("El horario no puede exceder 255 caracteres.")

    latitud_raw = (form_data.get("latitud") or "").strip()
    latitud = None
    if latitud_raw:
        try:
            latitud = float(latitud_raw)
            if not (-90.0 <= latitud <= 90.0):
                errores.append("La latitud debe estar entre -90 y 90 grados.")
        except ValueError:
            errores.append("La latitud debe ser un número decimal válido.")

    longitud_raw = (form_data.get("longitud") or "").strip()
    longitud = None
    if longitud_raw:
        try:
            longitud = float(longitud_raw)
            if not (-180.0 <= longitud <= 180.0):
                errores.append("La longitud debe estar entre -180 y 180 grados.")
        except ValueError:
            errores.append("La longitud debe ser un número decimal válido.")

    fecha_ver_raw = (form_data.get("fecha_verificacion") or "").strip()
    fecha_verificacion = None
    if fecha_ver_raw:
        try:
            fecha_verificacion = date.fromisoformat(fecha_ver_raw)
            if fecha_verificacion > date.today():
                errores.append("La fecha de revisión no puede estar en el futuro.")
        except ValueError:
            errores.append("La fecha de verificación debe tener formato AAAA-MM-DD válido.")

    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0

    servicios_seleccionados = form_data.getlist("servicios_ids")

    servicios_ids = []
    for sid in servicios_seleccionados:
        try:
            servicios_ids.append(int(sid))
        except (ValueError, TypeError):
            pass

    datos = {
        "codigo_minsa": codigo_minsa,
        "nombre": nombre,
        "tipo_establecimiento": tipo,
        "silais": silais,
        "municipio": municipio,
        "departamento": departamento,
        "direccion": direccion,
        "telefono": telefono,
        "horario": horario,
        "latitud": latitud,
        "longitud": longitud,
        "fecha_verificacion": fecha_verificacion,
        "activo": activo,
    }

    return datos, servicios_ids, errores


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
    if tipo in {"hospital", "centro_salud", "puesto_salud", "casa_materna", "clinica", "otro"}:
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

            for sid in servicios_ids:
                if db.session.get(Servicio, sid):
                    asig = CentroServicio(
                        centro_atencion_id=nuevo.id,
                        servicio_id=sid,
                        disponible=1,
                        fecha_verificacion=datos["fecha_verificacion"],
                    )
                    db.session.add(asig)

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

            # Sincronizar servicios asignados
            db.session.execute(
                db.delete(CentroServicio).where(CentroServicio.centro_atencion_id == item.id)
            )
            for sid in servicios_ids:
                if db.session.get(Servicio, sid):
                    asig = CentroServicio(
                        centro_atencion_id=item.id,
                        servicio_id=sid,
                        disponible=1,
                        fecha_verificacion=datos["fecha_verificacion"],
                    )
                    db.session.add(asig)

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
