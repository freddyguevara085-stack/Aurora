from datetime import date, timedelta

from controllers.routes import validar_fecha_control, validar_fechas_embarazo
from services.home import calcular_semana_gestacional


def test_calcular_semana_desde_fum_y_limita_a_42():
    hoy = date.today()
    fum = hoy - timedelta(days=70)
    assert calcular_semana_gestacional(fum, None, fum + timedelta(days=70)) == 10
    assert calcular_semana_gestacional(hoy - timedelta(days=400), None, hoy) == 42


def test_calcular_semana_desde_fpp():
    hoy = date.today()
    fpp = hoy + timedelta(days=84)
    assert calcular_semana_gestacional(None, fpp, hoy) == 28
    assert calcular_semana_gestacional(None, fpp, hoy, metodo_fpp="otro") == 28


def test_validar_fechas_embarazo_calcula_fpp_desde_fum():
    fum_esperada = date.today() - timedelta(days=100)
    fum, fpp, error = validar_fechas_embarazo(fum_esperada.isoformat(), None, "fum")
    assert (fum, fpp, error) == (fum_esperada, fum_esperada + timedelta(days=280), None)


def test_validar_fechas_embarazo_rechaza_relacion_incoherente():
    hoy = date.today()
    fum, fpp, error = validar_fechas_embarazo(
        (hoy - timedelta(days=100)).isoformat(),
        (hoy + timedelta(days=300)).isoformat(),
        "otro",
    )
    assert fum is None and fpp is None
    assert error


def test_validar_fechas_embarazo_rechaza_fpp_pasada_sin_fum():
    fpp_pasada = (date.today() - timedelta(days=15)).isoformat()
    fum, fpp, error = validar_fechas_embarazo(None, fpp_pasada, "otro")
    assert fum is None and fpp is None
    assert "42 semanas" in error.lower()


def test_validar_fechas_embarazo_acepta_fpp_futura_sin_fum():
    fpp_futura = date.today() + timedelta(days=1)
    fum, fpp, error = validar_fechas_embarazo(None, fpp_futura.isoformat(), "otro")
    assert fum is None
    assert fpp == fpp_futura
    assert error is None


def test_validar_fechas_embarazo_rechaza_fum_de_hace_tres_anios_y_fpp_futura():
    hoy = date.today()
    fum, fpp, error = validar_fechas_embarazo(
        (hoy - timedelta(days=3 * 365)).isoformat(),
        (hoy + timedelta(days=100)).isoformat(),
        "otro",
    )
    assert fum is None and fpp is None
    assert "42 semanas" in error.lower()


def test_validar_fechas_embarazo_rechaza_fpp_fum_con_metodo_fum_si_no_coincide():
    hoy = date.today()
    fum_entrada = hoy - timedelta(days=100)
    fpp_incoherente = hoy + timedelta(days=181)
    fum, fpp, error = validar_fechas_embarazo(
        fum_entrada.isoformat(), fpp_incoherente.isoformat(), "fum"
    )
    assert fum is None and fpp is None
    assert "280 días" in error


def test_validar_fecha_control_restringe_pasado_y_fuera_de_gestacion():
    hoy = date.today()
    inicio = hoy - timedelta(days=70)
    assert "pasado" in validar_fecha_control(hoy - timedelta(days=1), inicio, "programado", hoy)
    assert "42 semanas" in validar_fecha_control(inicio + timedelta(days=295), inicio, "programado", hoy)
    assert validar_fecha_control(hoy + timedelta(days=2), inicio, "programado", hoy) is None
    assert validar_fecha_control(hoy - timedelta(days=7), inicio, "realizado", hoy) is None
