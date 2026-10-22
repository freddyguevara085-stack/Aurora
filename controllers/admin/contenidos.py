"""CRUD de contenidos prenatales (guía) del panel de administración."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from controllers.admin import admin_bp
from controllers.admin._common import _alternar, _url_fuente_valida  # noqa: F401
from controllers.decorators import admin_required
from extensions import db
from models.contenido import ContenidoPrenatal
from services.admin import validar_datos_contenido
from services.auditoria import registrar_auditoria


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
