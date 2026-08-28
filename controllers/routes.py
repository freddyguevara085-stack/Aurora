from datetime import date, datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from services.home import calcular_semana_gestacional, construir_inicio
from services.mvp import centros_activos, centro_activo, contenidos_publicados, controles_activos, perfil_y_embarazo, recordatorios_pendientes, servicios_disponibles
from extensions import db
from models.contenido import ContenidoPrenatal, SenalAlerta
from models.directorio import CentroAtencion
from models.gestacion import Embarazo, PerfilGestante
from models.seguimiento import ControlPrenatal

main_bp = Blueprint('main', __name__)

# Ruta principal (la vista HTML)
@main_bp.route('/')
@login_required
def index():
    home_data = construir_inicio(current_user.id)
    return render_template('index.html', home=home_data)


def _usuario_gestante():
    return current_user.rol and current_user.rol.nombre == "usuario"


def validar_fechas_embarazo(fum_raw, fpp_raw, metodo):
    """Normaliza fechas del embarazo sin aceptar estimaciones contradictorias."""
    try:
        fum = date.fromisoformat(fum_raw) if fum_raw else None
        fpp = date.fromisoformat(fpp_raw) if fpp_raw else None
    except ValueError:
        return None, None, "Revisa el formato de las fechas."
    if not fum and not fpp:
        return None, None, "Indica la fecha de última menstruación o la fecha probable de parto."
    if fum and fum > date.today():
        return None, None, "La fecha de última menstruación no puede estar en el futuro."
    if metodo == "fum" and fum:
        return fum, fum + timedelta(days=280), None
    if fum and fpp:
        dias = (fpp - fum).days
        if dias < 1 or dias > 322:
            return None, None, "La relación entre las fechas no parece coherente."
    return fum, fpp, None


@main_bp.route('/embarazo', methods=['GET', 'POST'])
@login_required
def embarazo():
    perfil, activo = perfil_y_embarazo(current_user.id)
    editar = (request.args.get('editar') == '1' or request.method == 'POST') and activo is not None
    form_data = None
    if request.method == 'POST':
        if not _usuario_gestante() or not perfil:
            abort(403)
        form_data = request.form
        fum = request.form.get('fum') or None
        fpp = request.form.get('fpp') or None
        metodo = request.form.get('metodo_fpp') or None
        if metodo and metodo not in {'fum', 'ecografia', 'profesional', 'otro'}:
            flash('Método no válido.', 'error')
        else:
            fum_fecha, fpp_fecha, error = validar_fechas_embarazo(fum, fpp, metodo)
            if error:
                flash(error, 'error')
            else:
                try:
                    destino = activo or Embarazo(perfil_gestante_id=perfil.id, estado='activo')
                    destino.fum, destino.fpp, destino.metodo_fpp = fum_fecha, fpp_fecha, metodo
                    if not activo:
                        db.session.add(destino)
                    db.session.commit()
                    return redirect(url_for('main.embarazo'))
                except SQLAlchemyError:
                    db.session.rollback()
                    flash('No fue posible guardar la información del embarazo.', 'error')
    controles = controles_activos(activo)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp) if activo else None
    proximo = next((control for control in controles if control.fecha_control >= date.today() and control.estado in {'programado', 'reprogramado'}), None)
    return render_template(
        'embarazo.html',
        perfil=perfil,
        embarazo=activo,
        controles=controles,
        proximo=proximo,
        semana=semana,
        editar=editar,
        form_data=form_data,
        date=date.today(),
    )


@main_bp.route('/controles')
@login_required
def controles():
    _, activo = perfil_y_embarazo(current_user.id)
    controles = controles_activos(activo)
    hoy = date.today()
    proximos = [control for control in controles if control.fecha_control >= hoy and control.estado in {'programado', 'reprogramado'}]
    proximo = min(proximos, key=lambda control: (control.fecha_control, control.hora_control or datetime.min.time()), default=None)
    anteriores = [control for control in reversed(controles) if control is not proximo]
    return render_template('controles.html', embarazo=activo, controles=controles, proximo=proximo, anteriores=anteriores)


@main_bp.route('/controles/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_control():
    _, activo = perfil_y_embarazo(current_user.id)
    if not activo:
        flash('Necesitas un embarazo activo para registrar un control.', 'error')
        return redirect(url_for('main.controles'))
    centros = centros_activos()
    if request.method == 'POST':
        try:
            numero = int(request.form.get('numero_control', ''))
            edad = request.form.get('edad_gestacional') or None
            edad = float(edad) if edad else None
            fecha_control = date.fromisoformat(request.form.get('fecha_control', ''))
            centro_id = int(request.form.get('centro_atencion_id')) if request.form.get('centro_atencion_id') else None
            estado = request.form.get('estado', 'programado')
            if numero < 1 or (edad is not None and not 0 <= edad <= 45) or estado not in {'programado', 'realizado', 'reprogramado', 'cancelado'} or (centro_id and not centro_activo(centro_id)):
                raise ValueError
            db.session.add(ControlPrenatal(embarazo_id=activo.id, registrado_por_usuario_id=current_user.id, numero_control=numero, fecha_control=fecha_control, edad_gestacional_semanas=edad, centro_atencion_id=centro_id, estado=estado, indicaciones=request.form.get('indicaciones') or None))
            db.session.commit()
            return redirect(url_for('main.controles'))
        except (ValueError, TypeError):
            flash('Revisa los datos del control.', 'error')
        except SQLAlchemyError:
            db.session.rollback(); flash('Ya existe ese número de control.', 'error')
    return render_template('control_form.html', centros=centros)


@main_bp.route('/calendario')
@login_required
def calendario():
    _, activo = perfil_y_embarazo(current_user.id)
    return render_template('calendario.html', embarazo=activo, controles=controles_activos(activo), recordatorios=recordatorios_pendientes(current_user.id))


@main_bp.route('/guia')
@login_required
def guia():
    trimestre = request.args.get('trimestre', type=int)
    categoria = (request.args.get('categoria') or '').strip()[:80]
    _, activo = perfil_y_embarazo(current_user.id)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp) if activo else None
    return render_template('guia.html', contenidos=contenidos_publicados(trimestre, categoria), trimestre=trimestre, categoria=categoria, semana=semana)


@main_bp.route('/guia/<int:contenido_id>')
@login_required
def detalle_guia(contenido_id):
    contenido = db.session.scalar(db.select(ContenidoPrenatal).where(ContenidoPrenatal.id == contenido_id, ContenidoPrenatal.publicado == 1))
    if not contenido: abort(404)
    return render_template('guia_detalle.html', contenido=contenido)


@main_bp.route('/alertas')
@login_required
def alertas():
    senales = db.session.scalars(db.select(SenalAlerta).where(SenalAlerta.activo == 1).order_by(SenalAlerta.orden_visual, SenalAlerta.id).limit(30)).all()
    return render_template('alertas.html', senales=senales)


@main_bp.route('/centros')
@login_required
def centros():
    return render_template('centros.html', centros=centros_activos((request.args.get('q') or '').strip(), (request.args.get('tipo') or '').strip()), q=(request.args.get('q') or '').strip()[:80], tipo=(request.args.get('tipo') or '').strip())


@main_bp.route('/centros/<int:centro_id>')
@login_required
def detalle_centro(centro_id):
    centro = centro_activo(centro_id)
    if not centro: abort(404)
    return render_template('centro_detalle.html', centro=centro, servicios=servicios_disponibles(centro.id))


@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    perfil_actual, embarazo_actual = perfil_y_embarazo(current_user.id)
    if request.method == 'POST':
        if not _usuario_gestante():
            abort(403)
        consentimiento = request.form.get('consentimiento_datos', '0')
        if consentimiento not in {'0', '1'}:
            abort(400)
        nacimiento_raw = request.form.get('fecha_nacimiento') or None
        fecha_invalida = False
        try:
            nacimiento = date.fromisoformat(nacimiento_raw) if nacimiento_raw else None
        except ValueError:
            nacimiento = None
            fecha_invalida = True
            flash('La fecha de nacimiento no es válida.', 'error')
        if nacimiento and nacimiento > date.today():
            flash('La fecha de nacimiento no puede estar en el futuro.', 'error')
            nacimiento = None
            fecha_invalida = True
        if fecha_invalida:
            semana = calcular_semana_gestacional(embarazo_actual.fum, embarazo_actual.fpp) if embarazo_actual else None
            return render_template('perfil.html', perfil=perfil_actual, embarazo=embarazo_actual, semana=semana, cedula=None, es_gestante=True, form_data=request.form, date=date.today())
        perfil_actual = perfil_actual or PerfilGestante(usuario_id=current_user.id)
        perfil_actual.cedula = (request.form.get('cedula') or '').strip()[:20] or None
        perfil_actual.fecha_nacimiento = nacimiento
        perfil_actual.telefono = (request.form.get('telefono') or '').strip()[:30] or None
        perfil_actual.direccion_residencia = (request.form.get('direccion_residencia') or '').strip() or None
        perfil_actual.municipio = (request.form.get('municipio') or '').strip()[:100] or None
        perfil_actual.departamento = (request.form.get('departamento') or '').strip()[:100] or None
        perfil_actual.contacto_emergencia_nombre = (request.form.get('contacto_emergencia_nombre') or '').strip()[:150] or None
        perfil_actual.contacto_emergencia_telefono = (request.form.get('contacto_emergencia_telefono') or '').strip()[:30] or None
        perfil_actual.consentimiento_datos = int(consentimiento)
        perfil_actual.fecha_consentimiento = datetime.now() if consentimiento == '1' else None
        if not perfil_actual.id: db.session.add(perfil_actual)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash('No fue posible actualizar el perfil.', 'error')
        else:
            flash('Perfil actualizado.', 'success')
            return redirect(url_for('main.perfil'))
    cedula = None
    if perfil_actual and perfil_actual.cedula:
        cedula = '*' * max(0, len(perfil_actual.cedula) - 4) + perfil_actual.cedula[-4:]
    semana = calcular_semana_gestacional(embarazo_actual.fum, embarazo_actual.fpp) if embarazo_actual else None
    return render_template('perfil.html', perfil=perfil_actual, embarazo=embarazo_actual, semana=semana, cedula=cedula, es_gestante=_usuario_gestante(), form_data=None, date=date.today())

# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')
