"""Configuración de Aurora por entorno.

Cada entorno hereda de :class:`Config` y solo ajusta lo necesario. El entorno
activo se selecciona con la variable ``AURORA_ENV`` (development | testing |
production) desde :func:`create_app`; si no se indica, se usa desarrollo.

Regla de seguridad: ``SECRET_KEY`` es obligatoria en desarrollo y producción;
en pruebas se permite una clave por defecto controlada.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


load_dotenv()


def _env_flag(nombre: str, defecto: str = "0") -> bool:
    """Lee un booleano desde el entorno aceptando 1/true/yes/on."""
    return os.getenv(nombre, defecto).strip().lower() in {"1", "true", "yes", "on"}


def database_url():
    """Acepta la URL de Railway o las variables locales, sin interpolar secretos."""
    raw = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if raw:
        url = make_url(raw)
        if url.drivername not in {"mysql", "mysql+pymysql"}:
            raise RuntimeError("Aurora requiere una base de datos MySQL.")
        return url.set(drivername="mysql+pymysql").update_query_dict({"charset": "utf8mb4"})
    query = {"charset": "utf8mb4"}
    if os.getenv("MYSQL_UNIX_SOCKET"):
        query["unix_socket"] = os.environ["MYSQL_UNIX_SOCKET"]
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER", "root"),
        password=os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD", ""),
        host=os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT", "3306")),
        database=os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE", "aurora"),
        query=query,
    )


class Config:
    """Configuración base, común a todos los entornos."""

    SECRET_KEY = os.getenv("SECRET_KEY")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "aurora")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_UNIX_SOCKET = os.getenv("MYSQL_UNIX_SOCKET")

    _mysql_query = {"charset": "utf8mb4"}
    if MYSQL_UNIX_SOCKET:
        _mysql_query["unix_socket"] = MYSQL_UNIX_SOCKET

    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _env_flag("MAIL_USE_TLS", "1")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME


class DevelopmentConfig(Config):
    """Entorno local. El modo DEBUG se controla con AURORA_DEBUG."""

    DEBUG = _env_flag("AURORA_DEBUG")


class TestingConfig(Config):
    """Entorno de pruebas: sin depuración y con CSRF desactivado por el cliente."""

    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = os.getenv("SECRET_KEY", "aurora-testing-secret-key")


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
    clave = (
        nombre
        or os.getenv("AURORA_ENV")
        or os.getenv("FLASK_ENV")
        or "development"
    ).strip().lower()
    clase = CONFIG_POR_ENTORNO.get(clave, DevelopmentConfig)
    if not clase.SECRET_KEY:
        raise RuntimeError("SECRET_KEY debe estar definida para iniciar Aurora.")
    return clase
