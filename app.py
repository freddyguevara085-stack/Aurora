from flask import Flask
from controllers.routes import main_bp

app = Flask(__name__)
# Una clave secreta básica para desarrollo
app.config['SECRET_KEY'] = 'clave-secreta-hackathon'

# Registramos el controlador de rutas
app.register_blueprint(main_bp)

if __name__ == '__main__':
    # debug=True permite que los cambios se vean sin reiniciar el servidor
    app.run(debug=True, host='0.0.0.0', port=5000)