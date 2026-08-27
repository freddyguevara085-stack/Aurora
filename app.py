from flask import Flask

from config import Config
from commands import register_commands
from controllers.auth import auth_bp
from controllers.routes import main_bp
from extensions import csrf, db, login_manager, migrate
import models

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "error"
csrf.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
register_commands(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
