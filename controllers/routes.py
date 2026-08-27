from flask import Blueprint, render_template, send_from_directory
from flask_login import current_user, login_required

from services.home import construir_inicio

main_bp = Blueprint('main', __name__)

# Ruta principal (la vista HTML)
@main_bp.route('/')
@login_required
def index():
    home_data = construir_inicio(current_user.id)
    return render_template('index.html', home=home_data)

# Ruta para que la PWA encuentre el Service Worker
@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

# Ruta para que la PWA encuentre el Manifest
@main_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')
