"""Fábrica de la aplicación Aurora.

``create_app`` construye una instancia de Flask con la configuración del entorno
seleccionado (``AURORA_ENV``). Al final del módulo se expone ``app`` para los
puntos de entrada existentes (``wsgi.py``, ``flask --app app``, pruebas).
"""

from flask import Flask, render_template

from commands import register_commands
from config import get_config
from controllers import gestante, publicas  # noqa: F401  (registran sus rutas)
from controllers.admin import admin_bp
from controllers.auth import auth_bp
from controllers.blueprints import main_bp
from extensions import csrf, db, login_manager
import models  # noqa: F401  (registra los modelos antes de cualquier consulta)


def create_app(config_name: str | None = None) -> Flask:
    """Crea y configura una instancia de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    _registrar_extensiones(app)
    _registrar_blueprints(app)
    register_commands(app)
    _registrar_manejadores_de_error(app)
    _registrar_cabeceras_de_seguridad(app)

    return app


def _registrar_extensiones(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para continuar."
    login_manager.login_message_category = "error"
    csrf.init_app(app)


def _registrar_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)


def _registrar_cabeceras_de_seguridad(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def _registrar_manejadores_de_error(app: Flask) -> None:
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
        app.logger.exception(error)
        db.session.rollback()
        return render_template(
            "errors/error.html",
            icono="error",
            eyebrow="Error 500",
            titulo="Algo no salió bien",
            mensaje="Estamos trabajando para recuperar el servicio. Intenta nuevamente en unos momentos.",
            reintentar=True,
        ), 500


# Instancia por defecto usada por wsgi.py, `flask --app app` y las pruebas.
app = create_app()


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"], host='127.0.0.1', port=5000)
