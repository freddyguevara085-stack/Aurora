from datetime import date, timedelta

from controllers.routes import validar_fechas_embarazo
from services.home import calcular_semana_gestacional


def test_calcular_semana_desde_fum_y_limita_a_42():
    fum = date(2026, 1, 1)
    assert calcular_semana_gestacional(fum, None, fum + timedelta(days=70)) == 10
    assert calcular_semana_gestacional(fum, None, fum + timedelta(days=400)) == 42


def test_calcular_semana_desde_fpp():
    fpp = date(2026, 10, 8)
    assert calcular_semana_gestacional(None, fpp, date(2026, 7, 16)) == 28


def test_validar_fechas_embarazo_calcula_fpp_desde_fum():
    fum, fpp, error = validar_fechas_embarazo("2026-01-01", None, "fum")
    assert (fum, fpp, error) == (date(2026, 1, 1), date(2026, 10, 8), None)


def test_validar_fechas_embarazo_rechaza_relacion_incoherente():
    fum, fpp, error = validar_fechas_embarazo("2026-01-01", "2027-01-01", "otro")
    assert fum is None and fpp is None
    assert error