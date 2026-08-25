from flask import Flask

from config import Config
from controllers.routes import main_bp
from extensions import db, migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
