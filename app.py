import os

from flask import Flask, render_template

from config import Config
from commands import register_commands
from controllers.admin import admin_bp
from controllers.auth import auth_bp
from controllers.routes import main_bp
from extensions import csrf, db, login_manager
import models

app = Flask(__name__)
app.config.from_object(Config)
app.config["DEBUG"] = os.getenv("AURORA_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "error"
csrf.init_app(app)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
register_commands(app)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if app.config.get("SESSION_COOKIE_SECURE"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.errorhandler(403)
def acceso_denegado(error):
    return render_template(
        "errors/error.html",
        icono="lock",
        eyebrow="Error 403",
        titulo="Acceso denegado",
        mensaje="No tienes permisos para consultar este espacio.",
    ), 403


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template(
        "errors/error.html",
        icono="search_off",
        eyebrow="Error 404",
        titulo="Página no encontrada",
        mensaje="La página que buscas ya no está disponible o la dirección cambió.",
    ), 404


@app.errorhandler(500)
def error_servidor(error):
    db.session.rollback()
    return render_template(
        "errors/error.html",
        icono="error",
        eyebrow="Error 500",
        titulo="Algo no salió bien",
        mensaje="Estamos trabajando para recuperar el servicio. Intenta nuevamente en unos momentos.",
    ), 500

if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"], host='0.0.0.0', port=5000)
