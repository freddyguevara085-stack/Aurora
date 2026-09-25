import os

from flask import Flask, render_template

from config import Config
from commands import register_commands
from controllers.admin import admin_bp
from controllers.auth import auth_bp
from controllers.routes import main_bp
from extensions import csrf, db, login_manager, migrate
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
migrate.init_app(app, db)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
register_commands(app)


@app.errorhandler(403)
def acceso_denegado(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def error_servidor(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500

if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"], host='0.0.0.0', port=5000)
