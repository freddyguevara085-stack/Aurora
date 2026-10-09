"""Pruebas de la arquitectura MVC: fábrica de aplicación y registro de rutas.

No dependen de MySQL: solo construyen la aplicación y comprueban el mapa de rutas.
"""

ENDPOINTS_ESPERADOS = {
    # Gestante
    "main.index",
    "main.embarazo",
    "main.registrar_nacimiento",
    "main.controles",
    "main.nuevo_control",
    "main.editar_control",
    "main.perfil",
    "main.cambiar_password",
    "main.plan_parto",
    "main.imprimir_plan_parto",
    "main.red_comunitaria",
    "main.preguntas_consulta",
    "main.calendario",
    # Públicas
    "main.guia",
    "main.centros",
    "main.detalle_centro",
    "main.alertas",
    "main.revision_clinica",
    # Auth
    "auth.login",
    "auth.logout",
    "auth.registro",
    "auth.recuperar_password",
    # Admin
    "admin.dashboard",
    "admin.contenidos",
    "admin.nuevo_contenido",
    "admin.senales",
    "admin.nueva_senal",
    "admin.centros",
    "admin.nuevo_centro",
    "admin.servicios",
    "admin.nuevo_servicio",
}


def test_la_fabrica_construye_la_aplicacion():
    from app import create_app

    app = create_app("testing")
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    faltantes = ENDPOINTS_ESPERADOS - endpoints
    assert not faltantes, f"Endpoints ausentes: {sorted(faltantes)}"


def test_los_controladores_comparten_el_blueprint_main():
    from controllers import gestante, publicas
    from controllers.blueprints import main_bp

    assert gestante.main_bp is main_bp
    assert publicas.main_bp is main_bp


def test_las_reglas_de_negocio_viven_en_services():
    from services.gestacion import validar_fechas_embarazo

    fum, fpp, error = validar_fechas_embarazo(None, None, None)
    assert (fum, fpp) == (None, None)
    assert error
