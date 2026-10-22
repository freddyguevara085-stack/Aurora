"""Paquete de rutas de los flujos de la gestante.

Cada submódulo registra sus rutas sobre ``main_bp`` y delega las reglas de
negocio en ``services/gestacion.py``, ``services/home.py`` y ``services/mvp.py``.
Se reexportan los ayudantes y vistas para mantener compatibilidad con pruebas.
"""

from datetime import date, datetime, time, timedelta

from controllers.blueprints import main_bp
from controllers.decorators import usuario_gestante as _usuario_gestante
from extensions import db
from services.gestacion import (
    PLAN_PARTO_TRANSPORTES,
    PREGUNTA_MAX_CARACTERES,
    ROLES_COMUNITARIOS,
    TIPOS_CONTROL_VALIDOS,
    contacto_propio,
    construir_indicaciones,
    descomponer_indicaciones,
    enmascarar_identificacion,
    fechas_embarazo_desde_edad_gestacional,
    formatear_identificacion,
    ordenar_centros_por_zona,
    proximo_control_activo,
    resolver_centro_input,
    seguimiento_fecha_parto,
    validar_contacto_comunitario,
    validar_fecha_control,
    validar_fecha_nacimiento_real,
    validar_fechas_embarazo,
)
from services.home import (
    calcular_semana_gestacional,
    construir_inicio,
    fecha_inicio_gestacion,
)
from services.mvp import (
    centro_activo,
    centros_activos,
    controles_activos,
    perfil_y_embarazo,
    recordatorios_pendientes,
    ultimo_embarazo_con_nacimiento,
)

from controllers.gestante.calendario import calendario, nuevo_recordatorio
from controllers.gestante.controles import (
    controles,
    detalle_consulta,
    editar_control,
    imprimir_consulta,
    nuevo_control,
)
from controllers.gestante.embarazo import embarazo, registrar_nacimiento
from controllers.gestante.perfil import cambiar_password, perfil
from controllers.gestante.plan_parto import imprimir_plan_parto, plan_parto
from controllers.gestante.preguntas import (
    _renderizar_preguntas,
    actualizar_pregunta,
    preguntas_consulta,
)
from controllers.gestante.red_comunitaria import (
    editar_contacto_comunitario,
    eliminar_contacto_comunitario,
    nuevo_contacto_comunitario,
    red_comunitaria,
)

__all__ = [
    "PLAN_PARTO_TRANSPORTES",
    "PREGUNTA_MAX_CARACTERES",
    "ROLES_COMUNITARIOS",
    "TIPOS_CONTROL_VALIDOS",
    "_renderizar_preguntas",
    "_usuario_gestante",
    "actualizar_pregunta",
    "calcular_semana_gestacional",
    "calendario",
    "cambiar_password",
    "centro_activo",
    "centros_activos",
    "construir_indicaciones",
    "construir_inicio",
    "contacto_propio",
    "controles",
    "controles_activos",
    "date",
    "datetime",
    "db",
    "descomponer_indicaciones",
    "detalle_consulta",
    "editar_contacto_comunitario",
    "editar_control",
    "eliminar_contacto_comunitario",
    "embarazo",
    "enmascarar_identificacion",
    "fecha_inicio_gestacion",
    "fechas_embarazo_desde_edad_gestacional",
    "formatear_identificacion",
    "imprimir_consulta",
    "imprimir_plan_parto",
    "main_bp",
    "nuevo_contacto_comunitario",
    "nuevo_control",
    "nuevo_recordatorio",
    "ordenar_centros_por_zona",
    "perfil",
    "perfil_y_embarazo",
    "plan_parto",
    "preguntas_consulta",
    "proximo_control_activo",
    "recordatorios_pendientes",
    "red_comunitaria",
    "registrar_nacimiento",
    "resolver_centro_input",
    "seguimiento_fecha_parto",
    "time",
    "timedelta",
    "ultimo_embarazo_con_nacimiento",
    "validar_contacto_comunitario",
    "validar_fecha_control",
    "validar_fecha_nacimiento_real",
    "validar_fechas_embarazo",
]
