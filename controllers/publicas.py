"""Rutas públicas: inicio, guía, centros, alertas, información y PWA."""

from flask import abort, render_template, request, send_from_directory
from flask_login import current_user

from controllers.blueprints import main_bp
from controllers.decorators import admin_required, es_cuenta_demo as _es_cuenta_demo
from demo_nicaragua import BORRADORES, CONTEXTO, FECHA_CONSULTA, FUENTES
from services.home import calcular_semana_gestacional, construir_inicio
from services.mvp import (
    centros_activos,
    centro_activo,
    contenidos_publicados,
    perfil_y_embarazo,
    servicios_disponibles,
)


# Ruta principal (la vista HTML)
@main_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('public_home.html')
    home_data = construir_inicio(current_user.id)
    return render_template('index.html', home=home_data)


@main_bp.route('/guia')
def guia():
    activo = None
    if current_user.is_authenticated:
        _, activo = perfil_y_embarazo(current_user.id)
    semana = calcular_semana_gestacional(activo.fum, activo.fpp, metodo_fpp=activo.metodo_fpp) if activo else None

    publicados = contenidos_publicados()
    orientaciones = [
        {
            "id": f"pub-{c.id}",
            "titulo": c.titulo,
            "resumen": c.resumen or "",
            "cuerpo": c.contenido,
            "categoria": c.categoria,
            "trimestre": c.trimestre,
            "fuente_nombre": c.fuente_nombre,
            "fuente_url": c.fuente_url,
            "fecha_revision": c.fecha_revision.strftime('%d/%m/%Y') if c.fecha_revision else None,
            "es_borrador": False,
        }
        for c in publicados
    ]

    borradores = []
    if _es_cuenta_demo():
        borradores = [
            {
                **item,
                "fuente_nombre": FUENTES.get(item["fuente"], {}).get("nombre", "Fuente sin registrar"),
                "fuente_url": FUENTES.get(item["fuente"], {}).get("url", "#"),
            }
            for item in BORRADORES
        ]
        for item in borradores:
            orientaciones.append({
                "id": f"demo-{item['id']}",
                "titulo": item["titulo"],
                "resumen": item["texto"][:120] + ("…" if len(item["texto"]) > 120 else ""),
                "cuerpo": item["texto"],
                "categoria": item["categoria"].capitalize(),
                "trimestre": item.get("trimestre"),
                "fuente_nombre": item["fuente_nombre"],
                "fuente_url": item["fuente_url"],
                "fecha_revision": f"consultada {FECHA_CONSULTA}",
                "es_borrador": True,
            })

    return render_template(
        'guia.html',
        orientaciones=orientaciones,
        contenidos=publicados,
        borradores=borradores,
        fecha_consulta=FECHA_CONSULTA,
        semana=semana,
    )


@main_bp.route('/guia/<int:contenido_id>')
def detalle_guia(contenido_id):
    abort(404)


@main_bp.route('/alertas')
def alertas():
    senales = []
    if _es_cuenta_demo():
        from demo_nicaragua import SENALES_ALERTA
        senales = SENALES_ALERTA
    return render_template('alertas.html', senales=senales)


@main_bp.route('/centros')
def centros():
    centros = centros_activos()
    departamentos = sorted(list(set(c.departamento for c in centros if getattr(c, "departamento", None))))

    departamento_usuario = None
    if current_user.is_authenticated:
        perfil, _ = perfil_y_embarazo(current_user.id)
        if perfil and perfil.departamento:
            departamento_usuario = perfil.departamento

    return render_template(
        'centros.html',
        centros=centros,
        departamentos=departamentos,
        departamento_usuario=departamento_usuario,
        es_demo=_es_cuenta_demo(),
        q=(request.args.get('q') or '').strip()[:80],
        tipo=(request.args.get('tipo') or '').strip(),
        departamento=(request.args.get('departamento') or '').strip()[:100],
    )


@main_bp.route('/centros/<int:centro_id>')
def detalle_centro(centro_id):
    centro = centro_activo(centro_id)
    if not centro: abort(404)
    return render_template('centro_detalle.html', centro=centro, servicios=servicios_disponibles(centro.id))


# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
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
        contexto=CONTEXTO,
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
            'No compartas datos clínicos reales en esta versión de demostración.',
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
            'Es una demostración para validar si estas tareas simples ayudan a llegar mejor preparada y acompañada a la atención profesional.',
        ],
    )


@main_bp.route('/demo/revision-clinica')
@admin_required
def revision_clinica():
    return render_template(
        'revision_clinica.html',
        fuentes=FUENTES,
        borradores=BORRADORES,
        contexto=CONTEXTO,
        fecha_consulta=FECHA_CONSULTA,
    )
