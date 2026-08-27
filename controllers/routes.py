from datetime import date, datetime

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


@main_bp.route('/embarazo', methods=['GET', 'POST'])
@login_required
def embarazo():
    perfil, activo = perfil_y_embarazo(current_user.id)
    if request.method == 'POST':
        if not _usuario_gestante() or not perfil or activo:
            abort(403)
        fum = request.form.get('fum') or None
        fpp = request.form.get('fpp') or None
        metodo = request.form.get('metodo_fpp') or None
        if not fum and not fpp:
            flash('Indica FUM o FPP.', 'error')
        elif metodo and metodo not in {'fum', 'ecografia', 'profesional', 'otro'}:
            flash('Método no válido.', 'error')
        else:
            try:
                nuevo = Embarazo(perfil_gestante_id=perfil.id, fum=date.fromisoformat(fum) if fum else None, fpp=date.fromisoformat(fpp) if fpp else None, metodo_fpp=metodo, estado='activo')
                db.session.add(nuevo); db.session.commit()
                return redirect(url_for('main.embarazo'))
            except ValueError:
                flash('Las fechas no son válidas.', 'error')
            except SQLAlchemyError:
                db.session.rollback()
                flash('No fue posible registrar el embarazo.', 'error')
    controles = controles_activos(activo)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp) if activo else None
    return render_template('embarazo.html', perfil=perfil, embarazo=activo, controles=controles, semana=semana)


@main_bp.route('/controles')
@login_required
def controles():
    _, activo = perfil_y_embarazo(current_user.id)
    return render_template('controles.html', embarazo=activo, controles=controles_activos(activo))


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
    return render_template('guia.html', contenidos=contenidos_publicados(trimestre, categoria), trimestre=trimestre, categoria=categoria)


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
    perfil_actual, _ = perfil_y_embarazo(current_user.id)
    if request.method == 'POST':
        if not _usuario_gestante():
            abort(403)
        consentimiento = request.form.get('consentimiento_datos', '0')
        if consentimiento not in {'0', '1'}:
            abort(400)
        perfil_actual = perfil_actual or PerfilGestante(usuario_id=current_user.id)
        perfil_actual.telefono = (request.form.get('telefono') or '').strip()[:30] or None
        perfil_actual.direccion_residencia = (request.form.get('direccion_residencia') or '').strip() or None
        perfil_actual.municipio = (request.form.get('municipio') or '').strip()[:100] or None
        perfil_actual.departamento = (request.form.get('departamento') or '').strip()[:100] or None
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
    return render_template('perfil.html', perfil=perfil_actual, cedula=cedula, es_gestante=_usuario_gestante())

# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')
