"""Controlador principal y rutas del panel de administración de Aurora."""



from datetime import date

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from flask_login import current_user, login_required

from sqlalchemy import func, or_, select

from sqlalchemy.exc import SQLAlchemyError, IntegrityError



from extensions import db

from models.auditoria import HistorialAuditoria

from models.contenido import ContenidoPrenatal, SenalAlerta

from models.directorio import CentroAtencion, CentroServicio, Servicio

from models.usuario import Usuario

from services.auditoria import registrar_auditoria



admin_bp = Blueprint("admin", __name__, url_prefix="/admin")





def admin_required(f):

    """Decorador para proteger rutas exclusivas del rol administrador."""

    @wraps(f)

    @login_required

    def decorated_function(*args, **kwargs):

        if not (current_user.rol and current_user.rol.nombre == "administrador"):

            abort(403)

        return f(*args, **kwargs)

    return decorated_function





# ============================================================================

# DASHBOARD

# ============================================================================



@admin_bp.route("/")

@admin_required

def dashboard():

    """Vista principal del panel administrativo con métricas y accesos rápidos."""

    total_contenidos = db.session.scalar(select(func.count(ContenidoPrenatal.id))) or 0

    total_publicados = db.session.scalar(select(func.count(ContenidoPrenatal.id)).where(ContenidoPrenatal.publicado == 1)) or 0

    total_senales = db.session.scalar(select(func.count(SenalAlerta.id))) or 0

    total_senales_activas = db.session.scalar(select(func.count(SenalAlerta.id)).where(SenalAlerta.activo == 1)) or 0

    total_centros = db.session.scalar(select(func.count(CentroAtencion.id))) or 0

    total_centros_activos = db.session.scalar(select(func.count(CentroAtencion.id)).where(CentroAtencion.activo == 1)) or 0

    total_servicios = db.session.scalar(select(func.count(Servicio.id))) or 0



    ultimos_eventos = db.session.scalars(

        select(HistorialAuditoria)

        .order_by(HistorialAuditoria.created_at.desc())

        .limit(6)

    ).all()



    metricas = {

        "contenidos": total_contenidos,

        "contenidos_publicados": total_publicados,

        "senales": total_senales,

        "senales_activas": total_senales_activas,

        "centros": total_centros,

        "centros_activos": total_centros_activos,

        "servicios": total_servicios,

    }



    return render_template("admin/dashboard.html", metricas=metricas, eventos=ultimos_eventos)





# ============================================================================

# CRUD: CONTENIDOS PRENATALES (GUÍA)

# ============================================================================



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



    nuevo_estado = 0 if item.publicado == 1 else 1

    item.publicado = nuevo_estado

    item.actualizado_por_usuario_id = current_user.id



    try:

        registrar_auditoria(

            usuario_id=current_user.id,

            accion="cambiar_estado",

            entidad="contenidos_prenatales",

            registro_id=item.id,

            detalles={"publicado": nuevo_estado},

            ip=request.remote_addr,

        )
        db.session.commit()



        estado_txt = "publicado" if nuevo_estado == 1 else "guardado como borrador"

        flash(f"El contenido ahora está {estado_txt}.", "success")

    except SQLAlchemyError:

        db.session.rollback()

        flash("No se pudo cambiar el estado de publicación.", "error")



    return redirect(url_for("admin.contenidos"))





# ============================================================================

# CRUD: SEÑALES DE ALERTA

# ============================================================================



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



    nuevo_estado = 0 if item.activo == 1 else 1

    item.activo = nuevo_estado

    item.actualizado_por_usuario_id = current_user.id



    try:

        registrar_auditoria(

            usuario_id=current_user.id,

            accion="cambiar_estado",

            entidad="senales_alerta",

            registro_id=item.id,

            detalles={"activo": nuevo_estado},

            ip=request.remote_addr,

        )
        db.session.commit()



        estado_txt = "activada" if nuevo_estado == 1 else "desactivada"

        flash(f"La señal de alerta ha sido {estado_txt}.", "success")

    except SQLAlchemyError:

        db.session.rollback()

        flash("No se pudo cambiar el estado de la señal de alerta.", "error")



    return redirect(url_for("admin.senales"))





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





# ============================================================================

# CRUD: CENTROS DE ATENCIÓN

# ============================================================================



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

        except ValueError:

            errores.append("La fecha de verificación debe tener formato AAAA-MM-DD válido.")



    activo = 1 if form_data.get("activo") in ("1", "true", "on") else 0



    if hasattr(form_data, "getlist"):

        servicios_seleccionados = form_data.getlist("servicios_ids")

    else:

        val = form_data.get("servicios_ids")

        servicios_seleccionados = val if isinstance(val, (list, tuple, set)) else ([val] if val else [])



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

            CentroServicio.query.filter_by(centro_atencion_id=item.id).delete()

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



    nuevo_estado = 0 if item.activo == 1 else 1

    item.activo = nuevo_estado



    try:

        registrar_auditoria(

            usuario_id=current_user.id,

            accion="cambiar_estado",

            entidad="centros_atencion",

            registro_id=item.id,

            detalles={"activo": nuevo_estado},

            ip=request.remote_addr,

        )
        db.session.commit()



        estado_txt = "activado" if nuevo_estado == 1 else "desactivado"

        flash(f"El centro de salud ha sido {estado_txt}.", "success")

    except SQLAlchemyError:

        db.session.rollback()

        flash("No se pudo cambiar el estado del centro de salud.", "error")



    return redirect(url_for("admin.centros"))





@admin_bp.route("/centros/<int:centro_id>/eliminar", methods=["POST"])

@admin_required

def eliminar_centro(centro_id):

    """Desactiva o elimina un centro de atención verificando integridad referencial."""

    item = db.session.get(CentroAtencion, centro_id)

    if not item:

        abort(404)



    nombre = item.nombre

    try:

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

    except IntegrityError:

        db.session.rollback()

        # Si tiene controles asignados por integridad referencial, lo desactivamos de forma segura

        item.activo = 0

        try:

            registrar_auditoria(

                usuario_id=current_user.id,

                accion="desactivar_por_dependencias",

                entidad="centros_atencion",

                registro_id=centro_id,

                detalles={"nombre": nombre, "motivo": "Tiene controles asociados"},

                ip=request.remote_addr,

            )
            db.session.commit()

            flash(f"El centro «{nombre}» tiene controles registrados asociados, por lo que fue desactivado en lugar de eliminado para conservar el historial.", "warning")

        except SQLAlchemyError:

            db.session.rollback()

            flash("No fue posible procesar la eliminación del centro.", "error")



    return redirect(url_for("admin.centros"))





# ============================================================================

# CRUD: CATÁLOGO DE SERVICIOS

# ============================================================================



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



    nuevo_estado = 0 if item.activo == 1 else 1

    item.activo = nuevo_estado



    try:

        registrar_auditoria(

            usuario_id=current_user.id,

            accion="cambiar_estado",

            entidad="servicios",

            registro_id=item.id,

            detalles={"activo": nuevo_estado},

            ip=request.remote_addr,

        )
        db.session.commit()



        estado_txt = "activado" if nuevo_estado == 1 else "desactivado"

        flash(f"El servicio ha sido {estado_txt}.", "success")

    except SQLAlchemyError:

        db.session.rollback()

        flash("No se pudo cambiar el estado del servicio.", "error")



    return redirect(url_for("admin.servicios"))

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
