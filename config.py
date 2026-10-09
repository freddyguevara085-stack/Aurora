"""Configuración de Aurora por entorno.

Cada entorno hereda de :class:`Config` y solo ajusta lo necesario. El entorno
activo se selecciona con la variable ``AURORA_ENV`` (development | testing |
production) desde :func:`create_app`; si no se indica, se usa desarrollo.

Regla de seguridad: ``SECRET_KEY`` es obligatoria y el arranque falla en voz alta
si no está definida, para no iniciar con una clave vacía o por defecto.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL


load_dotenv()


def _env_flag(nombre: str, defecto: str = "0") -> bool:
    """Lee un booleano desde el entorno aceptando 1/true/yes/on."""
    return os.getenv(nombre, defecto).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Configuración base, común a todos los entornos."""

    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('SECRET_KEY debe estar definida para iniciar Aurora.')

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _env_flag('SESSION_COOKIE_SECURE')

    # Habilita comandos que cargan datos de demostración. Debe quedar desactivado
    # en producción para no insertar centros ni perfiles ficticios por accidente.
    DEMO_MODE = _env_flag('AURORA_DEMO')

    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'aurora')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername='mysql+pymysql',
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DATABASE,
        query={'charset': 'utf8mb4'},
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Entorno local. El modo DEBUG se controla con AURORA_DEBUG."""

    DEBUG = _env_flag('AURORA_DEBUG')


class TestingConfig(Config):
    """Entorno de pruebas: sin depuración y con CSRF desactivado por el cliente."""

    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Entorno de producción: nunca en modo debug."""

    DEBUG = False


CONFIG_POR_ENTORNO = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(nombre: str | None = None):
    """Devuelve la clase de configuración para el nombre indicado o AURORA_ENV."""
    clave = (nombre or os.getenv("AURORA_ENV", "development")).strip().lower()
    return CONFIG_POR_ENTORNO.get(clave, DevelopmentConfig)
