"""Datos verificables de fuentes oficiales para la demo de revisión clínica.

Cada dato registra la fuente (nombre y URL) y la fecha en que se consultó.
IMPORTANTE: la fecha de consulta NO es una fecha de revisión clínica. Aurora
todavía no ha sido revisada por profesionales de salud; estos resúmenes son
borradores demo visibles solo a las cuentas ficticias del entorno de demostración.

Fuentes MINSA consultadas el 2026-10-06:
- MINSA - Actividades Básicas durante la Atención Prenatal (2022).
- MINSA - Elaboración y utilización del Censo Gerencial (2022).
- MINSA - Atención del Recién Nacido (2022).
- MINSA - Normativa 078, Sistema de Información Perinatal Plus.
- MINSA Nicaragua - Red de Salud, Hospitales: https://www.minsa.gob.ni/index.php/red-de-salud/hospitales
- MINSA Nicaragua - Red de Salud, Casa Materna: https://www.minsa.gob.ni/index.php/red-de-salud/casa-materna
"""

# Cuentas ficticias. Solo ven estos borradores cuando DEMO_MODE está activo.
CUENTA_DEMO_EMAIL = "maria.demo@aurora.ni"
CUENTAS_DEMO_EMAILS = frozenset({
    CUENTA_DEMO_EMAIL,
    "prueba.semana08@example.com",
    "prueba.semana20@example.com",
    "prueba.semana34@example.com",
})

FECHA_CONSULTA = "2026-10-06"

FUENTES = {
    "minsa_inicio": {
        "nombre": "MINSA Nicaragua - Inicio (red de servicio pública)",
        "url": "https://www.minsa.gob.ni/",
    },
    "minsa_hospitales": {
        "nombre": "MINSA Nicaragua - Red de Salud: Hospitales",
        "url": "https://www.minsa.gob.ni/index.php/red-de-salud/hospitales",
    },
    "minsa_casas_maternas": {
        "nombre": "MINSA Nicaragua - Red de Salud: Casa Materna",
        "url": "https://www.minsa.gob.ni/index.php/red-de-salud/casa-materna",
    },
    "minsa_atencion_prenatal_2022": {
        "nombre": "MINSA - Actividades Básicas durante la Atención Prenatal (2022); cita Normativa 011, tercera edición (2020)",
        "url": "https://www.minsa.gob.ni/sites/default/files/publicaciones/II-Atencion%20Prenatal%202022-11.pdf",
    },
    "minsa_censo_gerencial_2022": {
        "nombre": "MINSA - Elaboración y utilización del Censo Gerencial (2022)",
        "url": "https://www.minsa.gob.ni/sites/default/files/publicaciones/I-%20Censo%20gerencial%202022-11.pdf",
    },
    "minsa_recien_nacido_2022": {
        "nombre": "MINSA - Atención del Recién Nacido (2022); referencia Normativa 108 (2022)",
        "url": "https://www.minsa.gob.ni/sites/default/files/publicaciones/V-Atencion%20del%20Reci%C3%A9n%20Nacido%202022-11.pdf",
    },
    "minsa_sip_plus_2022": {
        "nombre": "MINSA - Normativa 078, Sistema de Información Perinatal Plus, segunda edición (2021; publicada en 2022)",
        "url": "https://www.minsa.gob.ni/sites/default/files/publicaciones/Normativa%20078%20final%2019092022.pdf",
    },
}

# Centros confirmados en el listado oficial del MINSA (nombre, tipo, SILAIS,
# ubicación). Teléfono, horario y coordenadas NO aparecen en la fuente: se dejan
# vacíos y la aplicación los muestra como "por confirmar". No se registra fecha
# de verificación porque no hubo revisión institucional documentada.
CENTROS = [
    {
        "nombre": "Hospital Regional Nuevo Amanecer",
        "tipo_establecimiento": "hospital",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Puerto Cabezas",
        "direccion": "Bo. Los Ángeles, frente a la Farmacia Familiar, casco urbano, Puerto Cabezas",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Departamental José Nieborowsky",
        "tipo_establecimiento": "hospital",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Boaco",
        "direccion": "Carretera Boaco-Muy Muy, Bo. Jorge Smith, Boaco",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Departamental España",
        "tipo_establecimiento": "hospital",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Chinandega",
        "direccion": "Colonia Roberto González, del Boulevard 2 cuadras al sur, contiguo al SILAIS Chinandega",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Regional Asunción",
        "tipo_establecimiento": "hospital",
        "silais": "CHONTALES",
        "departamento": "Chontales",
        "municipio": "Juigalpa",
        "direccion": "Km 141 carretera Managua - El Rama, La Repetidora, Juigalpa",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Regional San Juan de Dios",
        "tipo_establecimiento": "hospital",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "Estelí",
        "direccion": "Salida sur de Estelí Km 146, Bo. Justo Flores",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Departamental Amistad Japón Nicaragua",
        "tipo_establecimiento": "hospital",
        "silais": "GRANADA",
        "departamento": "Granada",
        "municipio": "Granada",
        "direccion": "Km 44 1/2 carretera Granada - Masaya, Barrio El Capullo",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Departamental Victoria Motta",
        "tipo_establecimiento": "hospital",
        "silais": "JINOTEGA",
        "departamento": "Jinotega",
        "municipio": "Jinotega",
        "direccion": "Barrio 20 de Mayo, Jinotega",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Regional Santiago",
        "tipo_establecimiento": "hospital",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Jinotepe",
        "direccion": "Primera entrada barrio José Antonio Sánchez, Jinotepe",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Departamental CMP (El Maestro)",
        "tipo_establecimiento": "hospital",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Diriamba",
        "direccion": "Costado sur del Estadio de Fútbol Cacique Diriangén, Barrio Roberto López",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Casa materna Luz Divina",
        "tipo_establecimiento": "casa_materna",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Puerto Cabezas",
        "direccion": "Bo. Libertad, contiguo a casa departamental sandinista",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa materna Mama Chila",
        "tipo_establecimiento": "casa_materna",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Santa Lucía",
        "direccion": "Sector 7, contiguo a pozos de ENACAL",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa materna Cleta Nubia Jarquín",
        "tipo_establecimiento": "casa_materna",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Teustepe",
        "direccion": "Entrada a Teustepe, contiguo al CDI",
        "fuente": "minsa_casas_maternas",
    },
]

# Resúmenes del proceso de atención para una demo. No indican tratamientos,
# no sustituyen la orientación profesional y aún requieren revisión clínica.
BORRADORES = [
    {
        "id": "inicio-atencion-prenatal",
        "titulo": "Inicio de la atención prenatal",
        "categoria": "controles",
        "texto": (
            "El material formativo del MINSA consultado para esta demostración presenta "
            "la captación prenatal como un proceso temprano y periódico. Idealmente, la "
            "primera atención ocurre durante el primer trimestre, hasta las 12 semanas. "
            "El equipo de salud define las atenciones que corresponden a cada persona "
            "según su situación. Aurora solo ayuda a organizar fechas y preguntas."
        ),
        "fuente": "minsa_atencion_prenatal_2022",
    },
    {
        "id": "seguimiento-prenatal-bajo-riesgo",
        "titulo": "Seguimiento prenatal de bajo riesgo",
        "categoria": "controles",
        "texto": (
            "El material formativo del MINSA de 2022 resume el esquema de la Normativa 011, "
            "tercera edición de 2020, para embarazos clasificados de bajo riesgo: primera "
            "atención hasta las 12 semanas; después, entre las 16–20, 24–26, 30, 34 y 36 "
            "semanas, más evaluaciones integrales a las 38 y 40 semanas. El equipo de salud "
            "ajusta el calendario a cada situación. Este ejemplo no es una agenda individual "
            "ni una indicación para autocalificar el embarazo."
        ),
        "fuente": "minsa_atencion_prenatal_2022",
    },
    {
        "id": "registro-perinatal-y-continuidad",
        "titulo": "Registro y continuidad de la atención",
        "categoria": "registro",
        "texto": (
            "La Normativa 078 del MINSA describe el Sistema de Información Perinatal Plus "
            "como apoyo al registro y seguimiento de la atención de la mujer durante el "
            "embarazo, el parto y el puerperio, y del recién nacido. Ese expediente lo "
            "gestiona el personal de salud. Aurora es una agenda personal de demostración "
            "y no reemplaza ni almacena el expediente clínico oficial."
        ),
        "fuente": "minsa_sip_plus_2022",
    },
    {
        "id": "plan-de-parto-y-apoyo",
        "titulo": "Preparación y red de apoyo",
        "categoria": "preparacion",
        "texto": (
            "Los materiales formativos del MINSA incluyen la preparación del plan de parto "
            "y el seguimiento de la coordinación con una Casa Materna cuando corresponde. "
            "En Aurora puedes anotar acompañamiento y traslado como recordatorio personal; "
            "confirma cualquier plan y disponibilidad directamente con tu unidad de salud."
        ),
        "fuente": "minsa_censo_gerencial_2022",
    },
    {
        "id": "parto-y-atencion-del-recien-nacido",
        "titulo": "Parto y atención del recién nacido",
        "categoria": "parto",
        "texto": (
            "El MINSA publica materiales diferenciados para la atención del parto y la "
            "atención inmediata del recién nacido por personal de salud. La evaluación, "
            "las decisiones y cualquier procedimiento corresponden al equipo que brinda "
            "la atención; Aurora solo ayuda a organizar preguntas y apoyo familiar."
        ),
        "fuente": "minsa_recien_nacido_2022",
    },
    {
        "id": "puerperio-y-seguimiento-postnatal",
        "titulo": "Puerperio y seguimiento después del parto",
        "categoria": "puerperio",
        "texto": (
            "El material formativo del MINSA incluye el seguimiento de la puérpera y la "
            "continuidad postnatal después del parto. El calendario de atención depende "
            "de cada caso y lo determina el personal de salud. Esta sección solo muestra "
            "que la organización puede continuar después del nacimiento; no ofrece pautas "
            "de cuidado ni recomendaciones clínicas."
        ),
        "fuente": "minsa_censo_gerencial_2022",
    },
]

# No se añade contexto clínico fuera de las fichas citadas de esta demostración.
CONTEXTO = []
