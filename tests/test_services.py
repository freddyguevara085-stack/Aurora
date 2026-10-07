from datetime import date, timedelta

from controllers.routes import fechas_embarazo_desde_edad_gestacional, validar_fecha_control, validar_fechas_embarazo
from demo_nicaragua import BORRADORES, CENTROS, FUENTES, SENALES_ALERTA
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


def test_edad_gestacional_indicada_se_convierte_en_fecha_que_sigue_avanzando():
    referencia = date(2026, 10, 7)
    fum, fpp, error = fechas_embarazo_desde_edad_gestacional("20", "3", referencia.isoformat(), referencia)
    assert fum is None and fpp == referencia + timedelta(days=280 - 143) and error is None
    assert calcular_semana_gestacional(fum, fpp, referencia, "profesional") == 20
    assert calcular_semana_gestacional(fum, fpp, referencia + timedelta(days=7), "profesional") == 21


def test_edad_gestacional_indicada_rechaza_valores_fuera_de_rango():
    assert fechas_embarazo_desde_edad_gestacional("43", "0", date.today().isoformat())[2]
    assert fechas_embarazo_desde_edad_gestacional("20", "7", date.today().isoformat())[2]
    assert fechas_embarazo_desde_edad_gestacional(None, "2", date.today().isoformat())[2]


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


def test_guia_demo_cubre_filtros_y_directorio_solo_tiene_fuentes_minsa():
    assert {item["categoria"] for item in BORRADORES} >= {
        "controles", "preparacion", "puerperio", "registro", "alertas"
    }
    assert all(item["fuente"].startswith("minsa_") and item["fuente"] in FUENTES for item in BORRADORES)
    assert len(CENTROS) >= 430
    assert len(SENALES_ALERTA) == 10
    assert all(s["activo"] == 1 and s["titulo"] and s["accion_recomendada"] for s in SENALES_ALERTA)
    deptos = {centro["departamento"] for centro in CENTROS}
    assert len(deptos) == 17
    assert not any("Distrito" in d for d in deptos)
    assert {centro["tipo_establecimiento"] for centro in CENTROS} == {
        "hospital", "casa_materna", "centro_salud", "clinica"
    }
    assert all(centro["fuente"] in FUENTES for centro in CENTROS)
    assert all(centro.get("zona") in (None, "urbano", "rural") for centro in CENTROS)
    assert all(
        centro.get("subtipo") for centro in CENTROS
        if centro["tipo_establecimiento"] == "hospital"
    )
    claves = [(centro["nombre"], centro["municipio"]) for centro in CENTROS]
    assert len(claves) == len(set(claves))
