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
- MINSA - Red de Salud: hospitales, casas maternas, centros de salud y clínicas previsionales.
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
    "minsa_centros_salud": {
        "nombre": "MINSA Nicaragua - Red de Salud: Centro de Salud",
        "url": "https://www.minsa.gob.ni/index.php/red-de-salud/centro-de-salud",
    },
    "minsa_clinicas_previsionales": {
        "nombre": "MINSA Nicaragua - Red de Salud: Clínicas Médicas Previsionales",
        "url": "https://www.minsa.gob.ni/index.php/red-de-salud/clinica-medica-previsional",
    },
    "minsa_cmp_info": {
        "nombre": "MINSA Nicaragua - Clínicas Médicas Previsionales del MINSA",
        "url": "https://www.minsa.gob.ni/index.php/centros-e-institutos/clinicas-medicas-previsionales-del-ministerio-de-salud-cmp-minsa",
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
        "trimestre": 1,
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
        "id": "fum-fpp-fechas-orientativas",
        "titulo": "FUM y FPP: fechas orientativas",
        "categoria": "controles",
        "texto": (
            "El material formativo del MINSA explica la FPP como la fecha en que se "
            "cumplen 40 semanas y describe su estimación con herramientas de datación "
            "gestacional. En Aurora, el método FUM usa un cálculo aproximado de 280 días; "
            "una estimación de ecografía o profesional puede ser distinta. Confirma tus "
            "fechas con el personal de salud."
        ),
        "fuente": "minsa_atencion_prenatal_2022",
    },
    {
        "id": "preparar-atencion-prenatal",
        "titulo": "Preparar cada atención prenatal",
        "categoria": "controles",
        "texto": (
            "El MINSA describe la atención prenatal como una secuencia periódica de "
            "atenciones a cargo del personal de salud. Para una consulta puedes ordenar "
            "tus fechas y anotar lo que deseas conversar. Los exámenes, valoraciones y "
            "decisiones clínicas los realiza el equipo que te atiende."
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
        "id": "censo-gerencial-continuidad",
        "titulo": "Seguimiento de citas y continuidad",
        "categoria": "registro",
        "texto": (
            "El material formativo del Censo Gerencial del MINSA describe cómo los "
            "servicios organizan el seguimiento de embarazadas, puérperas y postnatales. "
            "Aurora no es ese registro institucional; aquí puedes anotar recordatorios "
            "personales para conversar con tu unidad de salud."
        ),
        "fuente": "minsa_censo_gerencial_2022",
    },
    {
        "id": "registro-parto-recien-nacido",
        "titulo": "Registro del parto y del recién nacido",
        "categoria": "registro",
        "texto": (
            "La documentación perinatal del MINSA incluye segmentos para registrar la "
            "atención del parto y del recién nacido como parte de la continuidad con la "
            "historia de embarazo. Ese registro clínico oficial lo completa el personal "
            "de salud, no Aurora."
        ),
        "fuente": "minsa_sip_plus_2022",
    },
    {
        "id": "plan-de-parto-y-apoyo",
        "titulo": "Preparación y red de apoyo",
        "categoria": "preparacion",
        "trimestre": 3,
        "texto": (
            "Los materiales formativos del MINSA incluyen la preparación del plan de parto "
            "y el seguimiento de la coordinación con una Casa Materna cuando corresponde. "
            "En Aurora puedes anotar acompañamiento y traslado como recordatorio personal; "
            "confirma cualquier plan y disponibilidad directamente con tu unidad de salud."
        ),
        "fuente": "minsa_censo_gerencial_2022",
    },
    {
        "id": "casa-materna-y-coordinacion",
        "titulo": "Casa Materna y coordinación local",
        "categoria": "preparacion",
        "trimestre": 3,
        "texto": (
            "Los materiales del MINSA incluyen la coordinación con una Casa Materna "
            "dentro de la organización alrededor del parto cuando corresponde. La unidad "
            "de salud confirma si aplica a cada situación y la disponibilidad del servicio. "
            "El directorio de Aurora no confirma cupos ni servicios."
        ),
        "fuente": "minsa_censo_gerencial_2022",
    },
    {
        "id": "parto-y-atencion-del-recien-nacido",
        "titulo": "Parto y atención del recién nacido",
        "categoria": "preparacion",
        "trimestre": 3,
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
    {
        "id": "recien-nacido-y-lactancia",
        "titulo": "Recién nacido, lactancia y apoyo",
        "categoria": "puerperio",
        "texto": (
            "Los materiales formativos del MINSA incluyen la atención inmediata del recién "
            "nacido y el acompañamiento a la lactancia como parte de la continuidad "
            "materno-infantil. Para dudas o apoyo individual, conversa con el personal de "
            "salud que atiende a la familia; esta ficha no da instrucciones clínicas."
        ),
        "fuente": "minsa_recien_nacido_2022",
    },
]

# Más registros del directorio público, comprobados en los listados MINSA
# consultados el 2026-10-06. Se importan solo los campos publicados por MINSA.
CENTROS.extend([
    {
        "nombre": "Hospital Primario Oswaldo Padilla",
        "tipo_establecimiento": "hospital",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Waspán",
        "direccion": "Barrio Esteban Jaenz, casco urbano Waspam, Bo. Esteban Jaens",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario Ahmed Campos Corea, El Papayal",
        "tipo_establecimiento": "hospital",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "San Lorenzo",
        "direccion": "Km 104 carretera al Rama, Bo. El Papayal",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario San Francisco de Asís",
        "tipo_establecimiento": "hospital",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Camoapa",
        "direccion": "De la farmacia del Divino Niño 7 cuadras al norte",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario San José",
        "tipo_establecimiento": "hospital",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Diriamba",
        "direccion": "Del Reloj 3 cuadras abajo, 4 cuadras al sur, Barrio La Libertad",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario Raymundo García",
        "tipo_establecimiento": "hospital",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Somotillo",
        "direccion": "Del Mercado Central 3 km hacia carretera Cinco Pinos, Las Colinas",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario Tomás Borge Martínez",
        "tipo_establecimiento": "hospital",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Chichigalpa",
        "direccion": "Empalme Chichigalpa, 200 m al este, carretera a León, San José",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario Monseñor Julio C. Videa",
        "tipo_establecimiento": "hospital",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "Pueblo Nuevo",
        "direccion": "Salida hacia La Cofradía, contiguo al preescolar Janeth Rodríguez, Bo. Bayron Jiménez",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario Monte Carmelo",
        "tipo_establecimiento": "hospital",
        "silais": "GRANADA",
        "departamento": "Granada",
        "municipio": "Nandaime",
        "direccion": "Plaza José Dolores Estrada 3 cuadras al oeste, Barrio Juan José Quezada",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Primario Odorico de Andrea",
        "tipo_establecimiento": "hospital",
        "silais": "JINOTEGA",
        "departamento": "Jinotega",
        "municipio": "San Rafael del Norte",
        "direccion": "Del MINED 200 varas al sur, Barrio Uriel Blandón",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Regional César Amador Molina",
        "tipo_establecimiento": "hospital",
        "silais": "MATAGALPA",
        "departamento": "Matagalpa",
        "municipio": "Matagalpa",
        "direccion": "Del Maxi Palí 1 km al oeste, Barrio Walter Mendoza",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Escuela Oscar Danilo Rosales",
        "tipo_establecimiento": "hospital",
        "silais": "LEON",
        "departamento": "León",
        "municipio": "León",
        "direccion": "Catedral 1 cuadra al sur, Sagrario",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Hospital Departamental Gaspar García Laviana",
        "tipo_establecimiento": "hospital",
        "silais": "RIVAS",
        "departamento": "Rivas",
        "municipio": "Rivas",
        "direccion": "Km 113 carretera a Tola, Barrio Pedro Espinoza",
        "fuente": "minsa_hospitales",
    },
    {
        "nombre": "Casa Materna Dalila Penglas",
        "tipo_establecimiento": "casa_materna",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Prinzapolka",
        "direccion": "Alamikamba, frente a la primera casa de médicos",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Sahsa",
        "tipo_establecimiento": "casa_materna",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Puerto Cabezas",
        "direccion": "Calle principal, contiguo a la iglesia Morava",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Santa Inés",
        "tipo_establecimiento": "casa_materna",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Waspán",
        "direccion": "Bo. Santa Inés, contiguo a clínica Santa Inés",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Wanky Tagni",
        "tipo_establecimiento": "casa_materna",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Waspán",
        "direccion": "Bo. 4 de Mayo, frente a la casa del mecánico Taly",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Gladys Aragón Fernández",
        "tipo_establecimiento": "casa_materna",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Camoapa",
        "direccion": "Antiguas instalaciones del Centro de Salud, Bo. San Martín, del Gallo más Gallo 15 varas al oeste",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Arlen Siú",
        "tipo_establecimiento": "casa_materna",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "El Rosario",
        "direccion": "Estadio Municipal 300 m arriba, Bertha Díaz",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Elba Barrios",
        "tipo_establecimiento": "casa_materna",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Dolores",
        "direccion": "Contiguo al taller de los Espinozas",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna María Rural",
        "tipo_establecimiento": "casa_materna",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Diriamba",
        "direccion": "Instalaciones del Centro de Salud Manuel de Jesús Rivera, Santa Cecilia",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Nora Astorga",
        "tipo_establecimiento": "casa_materna",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Chichigalpa",
        "direccion": "Contiguo al Hospital Primario Tomás Borge Martínez, empalme Chichigalpa 200 m al este, carretera a León",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Acoyapa",
        "tipo_establecimiento": "casa_materna",
        "silais": "CHONTALES",
        "departamento": "Chontales",
        "municipio": "Acoyapa",
        "direccion": "En predio del Centro de Salud Familiar, sede municipal",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna La Trinidad",
        "tipo_establecimiento": "casa_materna",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "La Trinidad",
        "direccion": "Del hospital 2 cuadras al sur y 2 1/2 al oeste",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna Pueblo Nuevo",
        "tipo_establecimiento": "casa_materna",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "Pueblo Nuevo",
        "direccion": "Costado norte del Hospital Primario Monseñor Julio César Videa",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Casa Materna de Nandaime",
        "tipo_establecimiento": "casa_materna",
        "silais": "GRANADA",
        "departamento": "Granada",
        "municipio": "Nandaime",
        "direccion": "Del Hospital Primario Monte Carmelo 3 cuadras al sur y media cuadra al este",
        "fuente": "minsa_casas_maternas",
    },
    {
        "nombre": "Centro de Salud Ernesto Hodgson",
        "tipo_establecimiento": "centro_salud",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Puerto Cabezas",
        "direccion": "Frente al supermercado Monter, Barrio Libertad",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud María Antonieta Bendaña",
        "tipo_establecimiento": "centro_salud",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Santa Lucía",
        "direccion": "Contiguo a la Iglesia Católica, Barrio Sector 8",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Ramón Guillén Navarro",
        "tipo_establecimiento": "centro_salud",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Boaco",
        "direccion": "Frente al Parque José Nieborowsky, Barrio Olama",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud San José de los Remates",
        "tipo_establecimiento": "centro_salud",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "San José de los Remates",
        "direccion": "Policía Nacional 1 cuadra al este, Barrio Zona 3",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Dr. Sócrates Flores Vivas",
        "tipo_establecimiento": "centro_salud",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "San Marcos",
        "direccion": "Instituto Juan XXII, 1 1/2 cuadras al norte, Colonia Manuel Moya",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Gregoria Gutiérrez",
        "tipo_establecimiento": "centro_salud",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Dolores",
        "direccion": "De PLASTINIC 6 cuadras abajo y 1 1/2 al sur, Dolores Central",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Carolina Osejo",
        "tipo_establecimiento": "centro_salud",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Villanueva",
        "direccion": "Contiguo al cementerio, casco urbano de Villanueva, Sector 6",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Dra. Alma Nubia López",
        "tipo_establecimiento": "centro_salud",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Posoltega",
        "direccion": "Del empalme de Posoltega 1,500 m al sur, frente a antena Claro, Juan XXIII Zona 2",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Germán Pomares Ordóñez",
        "tipo_establecimiento": "centro_salud",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "San Pedro del Norte",
        "direccion": "Contiguo a la Iglesia Católica, Barrio Central",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Pedro Narváez Cisneros",
        "tipo_establecimiento": "centro_salud",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Jinotepe",
        "direccion": "Frente a los bomberos, Barrio San José",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Fátima Pavón",
        "tipo_establecimiento": "centro_salud",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "La Trinidad",
        "direccion": "Costado norte del parque, Barrio San José",
        "fuente": "minsa_centros_salud",
    },
    {
        "nombre": "Centro de Salud Leonel Rugama Rugama",
        "tipo_establecimiento": "centro_salud",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "Estelí",
        "direccion": "Frente al Instituto Nacional Francisco Luis Espinoza, Barrio Alfredo Lazo",
        "fuente": "minsa_centros_salud",
    },
])

# Clínicas Médicas Previsionales (CMP MINSA), según el listado oficial consultado
# el 2026-10-06. MINSA indica que su atención se rige por convenios con el INSS.
CENTROS.extend([
    {
        "nombre": "Puerto Cabezas",
        "tipo_establecimiento": "clinica",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Puerto Cabezas",
        "direccion": "Barrio El Cocal, antiguo edificio de la Universidad BICU",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Waspán",
        "tipo_establecimiento": "clinica",
        "silais": "RACCN BILWI",
        "departamento": "RACCN",
        "municipio": "Waspán",
        "direccion": "Dentro de las instalaciones del Hospital Primario Oswaldo Padilla",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Dr. Moisés Evenor Sotelo",
        "tipo_establecimiento": "clinica",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Boaco",
        "direccion": "Antiguas instalaciones del Hospital José Nieborowsky",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Jinotepe",
        "tipo_establecimiento": "clinica",
        "silais": "CARAZO",
        "departamento": "Carazo",
        "municipio": "Jinotepe",
        "direccion": "Agrimersa 1 cuadra al oeste, media cuadra al sur",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "San Vicente de Paul",
        "tipo_establecimiento": "clinica",
        "silais": "CHINANDEGA",
        "departamento": "Chinandega",
        "municipio": "Chinandega",
        "direccion": "Rotonda Los Encuentros 120 m al norte, carretera Panamericana",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Asunción",
        "tipo_establecimiento": "clinica",
        "silais": "CHONTALES",
        "departamento": "Chontales",
        "municipio": "Juigalpa",
        "direccion": "Gasolinera El Puma, 4 cuadras al oeste, 1 cuadra al sur",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Santo Tomás",
        "tipo_establecimiento": "clinica",
        "silais": "CHONTALES",
        "departamento": "Chontales",
        "municipio": "Santo Tomás",
        "direccion": "Del Estadio Municipal media cuadra al norte",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "San Juan de Dios",
        "tipo_establecimiento": "clinica",
        "silais": "ESTELI",
        "departamento": "Estelí",
        "municipio": "Estelí",
        "direccion": "Antiguo Hospital Alejandro Dávila Bolaños",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Amistad Japón - Nicaragua",
        "tipo_establecimiento": "clinica",
        "silais": "GRANADA",
        "departamento": "Granada",
        "municipio": "Granada",
        "direccion": "Km 45 1/2 carretera Granada - Masaya",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Filial Siuna",
        "tipo_establecimiento": "clinica",
        "silais": "RACCN LAS MINAS",
        "departamento": "RACCN",
        "municipio": "Siuna",
        "direccion": "Barrio Sol de Libertad, costado norte de la oficina del proyecto Alcaldía",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Bonanza",
        "tipo_establecimiento": "clinica",
        "silais": "RACCN LAS MINAS",
        "departamento": "RACCN",
        "municipio": "Bonanza",
        "direccion": "Contiguo a la Casa Materna Municipal, Barrio Marcos Antonio Somarriba",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Rosita",
        "tipo_establecimiento": "clinica",
        "silais": "RACCN LAS MINAS",
        "departamento": "RACCN",
        "municipio": "Rosita",
        "direccion": "Contiguo al Hospital Rosario Pravia, Bo. 28 de Mayo, frente a Casa Materna Meyling Onsang",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "CMP Somoto",
        "tipo_establecimiento": "clinica",
        "silais": "MADRIZ",
        "departamento": "Madriz",
        "municipio": "Somoto",
        "direccion": "Contiguo a la Alcaldía Municipal de Somoto",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Policlínico Adulto Mayor Lidia Saavedra de Ortega",
        "tipo_establecimiento": "clinica",
        "silais": "MANAGUA",
        "departamento": "Managua",
        "municipio": "Managua",
        "direccion": "Del Ministerio del Trabajo 2 cuadras arriba, 2 cuadras al lago",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Tipitapa",
        "tipo_establecimiento": "clinica",
        "silais": "MANAGUA",
        "departamento": "Managua",
        "municipio": "Tipitapa",
        "direccion": "Frente a la oficina de Claro",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Zona Franca",
        "tipo_establecimiento": "clinica",
        "silais": "MANAGUA",
        "departamento": "Managua",
        "municipio": "Managua",
        "direccion": "Carretera Norte, Complejo Zona Franca Las Mercedes",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Masatepe",
        "tipo_establecimiento": "clinica",
        "silais": "MASAYA",
        "departamento": "Masaya",
        "municipio": "Masatepe",
        "direccion": "Farmacia Gulmara 4 cuadras al norte",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Ocotal, Nueva Segovia",
        "tipo_establecimiento": "clinica",
        "silais": "NUEVA SEGOVIA",
        "departamento": "Nueva Segovia",
        "municipio": "Ocotal",
        "direccion": "Barrio María Auxiliadora, de la 5 esquinas 2 cuadras al sur",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Jalapa",
        "tipo_establecimiento": "clinica",
        "silais": "NUEVA SEGOVIA",
        "departamento": "Nueva Segovia",
        "municipio": "Jalapa",
        "direccion": "Dentro de las instalaciones del Hospital Primario Pastor Jiménez",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Dr. Ernesto Sequeira",
        "tipo_establecimiento": "clinica",
        "silais": "RACCS",
        "departamento": "RACCS",
        "municipio": "Bluefields",
        "direccion": "Barrio San Pedro, dentro de las instalaciones del Hospital Dr. Ernesto Sequeira",
        "fuente": "minsa_clinicas_previsionales",
    },
    {
        "nombre": "Sub-Filial Moyogalpa",
        "tipo_establecimiento": "clinica",
        "silais": "RIVAS",
        "departamento": "Rivas",
        "municipio": "Altagracia",
        "direccion": "Dentro de las instalaciones del Hospital Primario Héroes y Mártires de Ometepe",
        "fuente": "minsa_clinicas_previsionales",
    },
])

# No se añade contexto clínico fuera de las fichas citadas de esta demostración.
CONTEXTO = []
