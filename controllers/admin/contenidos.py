"""CRUD de contenidos prenatales (guía) del panel de administración."""

from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from controllers.admin import admin_bp
from controllers.admin._common import _alternar, _url_fuente_valida
from controllers.decorators import admin_required
from extensions import db
from models.contenido import ContenidoPrenatal
from services.auditoria import registrar_auditoria


def validar_datos_contenido(form_data):
    """Valida y limpia los datos del formulario de contenido prenatal."""
    errores = []

    titulo = (form_data.get("titulo") or "").strip()
    if not titulo:
        errores.append("El título es obligatorio.")
    elif len(titulo) > 180:
        errores.append("El título no puede exceder 180 caracteres.")

    resumen = (form_data.get("resumen") or "").strip() or None
    if resumen and len(resumen) > 500:
        errores.append("El resumen no puede exceder 500 caracteres.")

    contenido = (form_data.get("contenido") or "").strip()
    if not contenido:
        errores.append("El cuerpo del contenido no puede estar vacío.")

    categoria = (form_data.get("categoria") or "").strip()
    if not categoria:
        errores.append("La categoría es obligatoria.")
    elif len(categoria) > 80:
        errores.append("La categoría no puede exceder 80 caracteres.")

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
        errores.append("La fecha de revisión es obligatoria.")
    else:
        try:
            fecha_revision = date.fromisoformat(fecha_rev_raw)
        except ValueError:
            errores.append("La fecha de revisión debe tener formato AAAA-MM-DD válido.")

    trimestre_raw = (form_data.get("trimestre") or "").strip()
    trimestre = None
    if trimestre_raw:
        try:
            trimestre = int(trimestre_raw)
            if trimestre not in (1, 2, 3):
                errores.append("El trimestre debe ser 1, 2 o 3.")
        except ValueError:
            errores.append("El trimestre debe ser numérico.")

    sem_desde_raw = (form_data.get("semana_desde") or "").strip()
    sem_hasta_raw = (form_data.get("semana_hasta") or "").strip()
    semana_desde = None
    semana_hasta = None

    if sem_desde_raw or sem_hasta_raw:
        if not (sem_desde_raw and sem_hasta_raw):
            errores.append("Debes especificar tanto la semana inicial como la final, o dejar ambas vacías.")
        else:
            try:
                semana_desde = int(sem_desde_raw)
                semana_hasta = int(sem_hasta_raw)
                if not (1 <= semana_desde <= 42):
                    errores.append("La semana inicial debe estar entre 1 y 42.")
                if not (1 <= semana_hasta <= 42):
                    errores.append("La semana final debe estar entre 1 y 42.")
                if semana_desde > semana_hasta:
                    errores.append("La semana inicial no puede ser mayor que la semana final.")
            except ValueError:
                errores.append("Las semanas de gestación deben ser números enteros.")

    publicado = 1 if form_data.get("publicado") in ("1", "true", "on") else 0

    datos = {
        "titulo": titulo,
        "resumen": resumen,
        "contenido": contenido,
        "categoria": categoria,
        "semana_desde": semana_desde,
        "semana_hasta": semana_hasta,
        "trimestre": trimestre,
        "fuente_nombre": fuente_nombre,
        "fuente_url": fuente_url,
        "fecha_revision": fecha_revision,
        "publicado": publicado,
    }

    return datos, errores


@admin_bp.route("/contenidos")
@admin_required
def contenidos():
    """Listado general de contenidos prenatales para administración."""
    query = select(ContenidoPrenatal)

    categoria = (request.args.get("categoria") or "").strip()
    trimestre = request.args.get("trimestre", type=int)
    estado = request.args.get("estado", "").strip()

    if categoria:
        query = query.where(ContenidoPrenatal.categoria.ilike(f"%{categoria}%"))
    if trimestre in (1, 2, 3):
        query = query.where(ContenidoPrenatal.trimestre == trimestre)
    if estado == "publicado":
        query = query.where(ContenidoPrenatal.publicado == 1)
    elif estado == "borrador":
        query = query.where(ContenidoPrenatal.publicado == 0)

    lista_contenidos = db.session.scalars(
        query.order_by(ContenidoPrenatal.updated_at.desc(), ContenidoPrenatal.id.desc())
    ).all()

    categorias_disponibles = db.session.scalars(
        select(ContenidoPrenatal.categoria).distinct().order_by(ContenidoPrenatal.categoria)
    ).all()

    return render_template(
        "admin/contenidos/index.html",
        contenidos=lista_contenidos,
        categoria_actual=categoria,
        trimestre_actual=trimestre,
        estado_actual=estado,
        categorias_disponibles=categorias_disponibles,
    )


@admin_bp.route("/contenidos/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo_contenido():
    """Creación de un nuevo artículo en la guía prenatal."""
    if request.method == "POST":
        datos, errores = validar_datos_contenido(request.form)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template(
                "admin/contenidos/form.html",
                contenido=None,
                form_data=request.form,
                accion="crear",
            )

        try:
            nuevo = ContenidoPrenatal(
                creado_por_usuario_id=current_user.id,
                **datos
            )
            db.session.add(nuevo)
            db.session.flush()
            registrar_auditoria(
                usuario_id=current_user.id,
                accion="crear",
                entidad="contenidos_prenatales",
                registro_id=nuevo.id,
                detalles={"titulo": nuevo.titulo, "publicado": nuevo.publicado},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Contenido «{nuevo.titulo}» creado exitosamente.", "success")
            return redirect(url_for("admin.contenidos"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al guardar el contenido.", "error")
            return render_template(
                "admin/contenidos/form.html",
                contenido=None,
                form_data=request.form,
                accion="crear",
            )

    return render_template("admin/contenidos/form.html", contenido=None, form_data=None, accion="crear")


@admin_bp.route("/contenidos/<int:contenido_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_contenido(contenido_id):
    """Edición de un contenido prenatal existente."""
    item = db.session.get(ContenidoPrenatal, contenido_id)
    if not item:
        abort(404)

    if request.method == "POST":
        datos, errores = validar_datos_contenido(request.form)
        if errores:
            for err in errores:
                flash(err, "error")
            return render_template(
                "admin/contenidos/form.html",
                contenido=item,
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
                entidad="contenidos_prenatales",
                registro_id=item.id,
                detalles={"titulo": item.titulo, "publicado": item.publicado},
                ip=request.remote_addr,
            )
            db.session.commit()

            flash(f"Contenido «{item.titulo}» actualizado correctamente.", "success")
            return redirect(url_for("admin.contenidos"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error en la base de datos al actualizar el contenido.", "error")
            return render_template(
                "admin/contenidos/form.html",
                contenido=item,
                form_data=request.form,
                accion="editar",
            )

    return render_template("admin/contenidos/form.html", contenido=item, form_data=None, accion="editar")


@admin_bp.route("/contenidos/<int:contenido_id>/eliminar", methods=["POST"])
@admin_required
def eliminar_contenido(contenido_id):
    """Elimina un artículo de la guía prenatal."""
    item = db.session.get(ContenidoPrenatal, contenido_id)
    if not item:
        abort(404)

    titulo = item.titulo
    try:
        db.session.delete(item)
        registrar_auditoria(
            usuario_id=current_user.id,
            accion="eliminar",
            entidad="contenidos_prenatales",
            registro_id=contenido_id,
            detalles={"titulo": titulo},
            ip=request.remote_addr,
        )
        db.session.commit()

        flash(f"Contenido «{titulo}» eliminado del sistema.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No fue posible eliminar el contenido.", "error")

    return redirect(url_for("admin.contenidos"))


@admin_bp.route("/contenidos/<int:contenido_id>/toggle", methods=["POST"])
@admin_required
def toggle_publicacion_contenido(contenido_id):
    """Alterna el estado publicado / borrador de un contenido."""
    item = db.session.get(ContenidoPrenatal, contenido_id)
    if not item:
        abort(404)
    return _alternar(
        item,
        "publicado",
        "contenidos_prenatales",
        {1: "El contenido ahora está publicado.", 0: "El contenido ahora está guardado como borrador."},
        "admin.contenidos",
        mensaje_error="No se pudo cambiar el estado de publicación.",
    )
