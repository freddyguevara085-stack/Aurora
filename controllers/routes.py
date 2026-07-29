from flask import Blueprint, render_template, send_from_directory

main_bp = Blueprint('main', __name__)

# Ruta principal (la vista HTML)
@main_bp.route('/')
def index():
    return render_template('index.html')

# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')