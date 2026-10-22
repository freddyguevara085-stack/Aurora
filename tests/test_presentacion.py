from types import SimpleNamespace

import pytest

from config import database_url
from services.demo import crear_demo


def test_url_railway_conserva_password_y_driver(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.setenv('MYSQL_URL', 'mysql://demo:p%40ss%2Fword@mysql.railway.internal:3306/railway')
    url = database_url()
    assert url.drivername == 'mysql+pymysql'
    assert url.password == 'p@ss/word'
    assert url.database == 'railway'
    assert url.query['charset'] == 'utf8mb4'


def test_database_url_tiene_prioridad(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'mysql://u:p@database:3306/seleccionada')
    monkeypatch.setenv('MYSQL_URL', 'mysql://u:p@otra:3306/otra')
    assert database_url().database == 'seleccionada'


def test_variables_individuales_railway(monkeypatch):
    for name in ('DATABASE_URL', 'MYSQL_URL', 'MYSQL_HOST', 'MYSQL_PORT',
                 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE', 'MYSQL_UNIX_SOCKET'):
        monkeypatch.delenv(name, raising=False)
    for name, value in {'MYSQLHOST':'mysql.railway.internal','MYSQLPORT':'3307',
                         'MYSQLUSER':'demo','MYSQLPASSWORD':'example', 'MYSQLDATABASE':'railway'}.items():
        monkeypatch.setenv(name, value)
    url = database_url()
    assert (url.host, url.port, url.username, url.database) == ('mysql.railway.internal', 3307, 'demo', 'railway')


def test_demo_rechaza_password_corta_antes_de_escribir():
    with pytest.raises(ValueError):
        crear_demo('corta')


def test_demo_no_sobrescribe_cuenta_existente(monkeypatch):
    from app import app
    from services import demo
    existente = SimpleNamespace(email=demo.DEMO_EMAIL)
    with app.app_context():
        monkeypatch.setattr(demo.db.session, 'scalar', lambda query: existente)
        assert crear_demo('password-de-prueba') == (existente, False)
