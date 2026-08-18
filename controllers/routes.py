from flask import Blueprint, render_template, send_from_directory

main_bp = Blueprint('main', __name__)

# Ruta principal (la vista HTML)
@main_bp.route('/')
def index():
    # Estos valores de demostracion conservan la forma que tendran los datos
    # del perfil y de los controles cuando se conecten los servicios.
    home_data = {
        'user_name': 'Ana',
        'week': 24,
        'trimester': 'Trimestre 2',
        'progress': 60,
        'baby_size': 'coco',
        'next_appointment': {
            'date': '15 de Octubre',
            'time': '10:00 AM',
            'clinic': 'Centro Médico Salud & Vida',
        },
    }
    return render_template('index.html', home=home_data)

# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')
