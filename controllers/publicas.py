"""Rutas públicas: inicio, guía, centros, alertas, información y PWA."""

from flask import abort, render_template, request, send_from_directory
from flask_login import current_user

from controllers import gestante
from controllers.blueprints import main_bp
from services.catalogo_minsa import FECHA_CONSULTA, FUENTES, referencia_centro
from services.exploracion import filtrar_centros, organizar_guia
from services.home import (
    calcular_semana_gestacional,
    construir_inicio,
    construir_inicio as _construir_inicio_base,
)
from services.mvp import (
    centro_activo,
    centros_activos,
    contenidos_publicados,
    ensamblar_orientaciones_guia,
    perfil_y_embarazo,
    senales_activas,
    servicios_disponibles,
)


@main_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('public_home.html')
    inicio_fn = construir_inicio
    if (
        inicio_fn is _construir_inicio_base
        and getattr(gestante, 'construir_inicio', _construir_inicio_base) is not _construir_inicio_base
    ):
        inicio_fn = gestante.construir_inicio
    home_data = inicio_fn(current_user.id)
    return render_template('index.html', home=home_data)


@main_bp.route('/guia')
def guia():
    activo = None
    if current_user.is_authenticated:
        _, activo = perfil_y_embarazo(current_user.id)
    semana = (
        calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp)
        if activo
        else None
    )

    publicados = contenidos_publicados()
    orientaciones, temas = organizar_guia(ensamblar_orientaciones_guia(publicados))

    return render_template(
        'guia.html',
        temas=temas,
        orientaciones=orientaciones,
        contenidos=publicados,
        semana=semana,
    )


@main_bp.route('/alertas')
def alertas():
    return render_template('alertas.html', senales=senales_activas())


@main_bp.route('/centros')
def centros():
    lista_centros = centros_activos()
    departamentos = sorted(
        {c.departamento for c in lista_centros if getattr(c, "departamento", None)}
    )

    departamento = (request.args.get('departamento') or '').strip()[:100]
    municipio = (request.args.get('municipio') or '').strip()[:100]
    tipo = (request.args.get('tipo') or '').strip()
    tipos = {'hospital', 'centro_salud', 'puesto_salud', 'casa_materna', 'clinica', 'otro'}
    if tipo not in tipos:
        tipo = ''
    if departamento not in departamentos:
        departamento = ''
    municipios = sorted({c.municipio for c in lista_centros if c.municipio and (not departamento or c.departamento == departamento)})
    if municipio not in municipios:
        municipio = ''
    q = (request.args.get('q') or '').strip()[:80]
    filtrados = filtrar_centros(lista_centros, departamento, municipio, tipo, q)
    paginas = max(1, (len(filtrados) + 11) // 12)
    pagina = min(paginas, max(1, request.args.get('pagina', 1, type=int)))
    return render_template(
        'centros.html', centros=filtrados[(pagina-1)*12:pagina*12],
        departamentos=departamentos, municipios=municipios,
        q=q, tipo=tipo, departamento=departamento, municipio=municipio,
        total=len(filtrados), pagina=pagina, paginas=paginas,
    )


@main_bp.route('/centros/<int:centro_id>')
def detalle_centro(centro_id):
    centro = centro_activo(centro_id)
    if not centro:
        abort(404)
    return render_template(
        'centro_detalle.html',
        centro=centro,
        referencia=referencia_centro(centro),
        servicios=servicios_disponibles(centro.id),
    )


@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')


@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


@main_bp.route('/offline.html')
def offline():
    return send_from_directory('static', 'offline.html')


@main_bp.route('/fuentes')
def fuentes():
    return render_template(
        'informacion.html',
        titulo='Fuentes de información',
        icono='menu_book',
        contenido=[
            'Aurora organiza información de acompañamiento prenatal para fines educativos.',
            'Las señales de alerta y recomendaciones deben revisarse con profesionales de la salud antes de usarse en un contexto real.',
            'El contenido publicado incluye la fuente y la fecha de revisión registrada por el equipo administrador.',
        ],
        fuentes=FUENTES,
        fecha_consulta=FECHA_CONSULTA,
    )


@main_bp.route('/privacidad')
def privacidad():
    return render_template(
        'informacion.html',
        titulo='Privacidad',
        icono='shield',
        contenido=[
            'Aurora utiliza los datos del perfil y del embarazo para mostrar el seguimiento de la cuenta autenticada.',
            'Registra únicamente la información necesaria para organizar tu atención prenatal.',
            'Antes de un uso real deben definirse la política de privacidad, la retención y la eliminación de datos.',
        ],
    )


@main_bp.route('/acerca')
def acerca():
    return render_template(
        'informacion.html',
        titulo='Acerca de Aurora',
        icono='help',
        contenido=[
            'Aurora es un puente organizativo entre la vida diaria de una gestante y su atención prenatal.',
            'Ayuda a recordar controles, preparar preguntas y coordinar el traslado y las personas de apoyo elegidas por la usuaria.',
            'No interpreta síntomas, diagnostica, prescribe, recomienda tratamientos ni reemplaza al personal o a los servicios de salud.',
            'Su propósito es ayudar a llegar mejor preparada y acompañada a la atención profesional.',
        ],
    )
