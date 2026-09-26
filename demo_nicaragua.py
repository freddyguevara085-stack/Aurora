"""Datos verificables de fuentes oficiales para la demo de revisión clínica.

Cada dato registra la fuente (nombre y URL) y la fecha en que se consultó.
IMPORTANTE: la fecha de consulta NO es una fecha de revisión clínica. Aurora
todavía no ha sido revisada por profesionales de salud, por lo que todo el
material clínico permanece como borrador y fuera de las páginas públicas.

Fuentes consultadas el 2026-09-24:
- OPS/OMS - Salud materna: https://www.paho.org/es/temas/salud-materna
- OPS/OMS - Nicaragua: https://www.paho.org/es/nicaragua
- MINSA Nicaragua - Inicio: https://www.minsa.gob.ni/
- MINSA Nicaragua - Red de Salud, Hospitales: https://www.minsa.gob.ni/red-de-salud/hospitales
- MINSA Nicaragua - Red de Salud, Casa Materna: https://www.minsa.gob.ni/red-de-salud/casa-materna
"""

FECHA_CONSULTA = "2026-09-24"

FUENTES = {
    "ops_salud_materna": {
        "nombre": "OPS/OMS - Salud materna",
        "url": "https://www.paho.org/es/temas/salud-materna",
    },
    "ops_nicaragua": {
        "nombre": "OPS/OMS - Nicaragua",
        "url": "https://www.paho.org/es/nicaragua",
    },
    "minsa_inicio": {
        "nombre": "MINSA Nicaragua - Inicio (red de servicio pública)",
        "url": "https://www.minsa.gob.ni/",
    },
    "minsa_hospitales": {
        "nombre": "MINSA Nicaragua - Red de Salud: Hospitales",
        "url": "https://www.minsa.gob.ni/red-de-salud/hospitales",
    },
    "minsa_casas_maternas": {
        "nombre": "MINSA Nicaragua - Red de Salud: Casa Materna",
        "url": "https://www.minsa.gob.ni/red-de-salud/casa-materna",
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
        "nombre": "Luz Divina",
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
        "nombre": "Cleta Nubia Jarquín",
        "tipo_establecimiento": "casa_materna",
        "silais": "BOACO",
        "departamento": "Boaco",
        "municipio": "Teustepe",
        "direccion": "Entrada a Teustepe, contiguo al CDI",
        "fuente": "minsa_casas_maternas",
    },
]

# Borradores clínicos para la revisión de profesionales. El texto son
# afirmaciones atribuidas a la fuente; NO son recomendaciones de Aurora y no
# cuentan con aprobación ni fecha de revisión clínica.
BORRADORES = [
    {
        "id": "atencion-embarazo-parto-posparto",
        "titulo": "Atención durante el embarazo, el parto y el posparto",
        "categoria": "controles",
        "texto": (
            "La OPS/OMS indica que todas las mujeres necesitan acceso a la atención "
            "prenatal durante la gestación, a la atención especializada durante el parto "
            "y a la atención y apoyo en las primeras semanas tras el parto."
        ),
        "fuente": "ops_salud_materna",
    },
    {
        "id": "hemorragia-postparto",
        "titulo": "Hemorragia grave después del parto",
        "categoria": "emergencias",
        "texto": (
            "La OPS/OMS señala que las hemorragias graves tras el parto pueden provocar "
            "la muerte de una mujer sana en dos horas si no recibe atención adecuada, y "
            "que la inyección de oxitocina inmediatamente después del parto reduce el "
            "riesgo de hemorragia."
        ),
        "fuente": "ops_salud_materna",
    },
    {
        "id": "preeclampsia-eclampsia",
        "titulo": "Preeclampsia y eclampsia",
        "categoria": "emergencias",
        "texto": (
            "La OPS/OMS señala que la preeclampsia debe detectarse y tratarse "
            "adecuadamente antes de la aparición de convulsiones (eclampsia) u otras "
            "complicaciones potencialmente mortales, y que la administración de sulfato "
            "de magnesio puede reducir el riesgo de que las pacientes sufran eclampsia."
        ),
        "fuente": "ops_salud_materna",
    },
    {
        "id": "infecciones-postparto",
        "titulo": "Infecciones después del parto",
        "categoria": "emergencias",
        "texto": (
            "La OPS/OMS indica que las infecciones tras el parto pueden eliminarse con "
            "una buena higiene y reconociendo y tratando a tiempo los signos tempranos "
            "de infección."
        ),
        "fuente": "ops_salud_materna",
    },
    {
        "id": "embarazo-adolescencia",
        "titulo": "Prevención del embarazo en la adolescencia",
        "categoria": "prevencion",
        "texto": (
            "La OPS/OMS señala que para evitar la muerte materna también es fundamental "
            "evitar los embarazos no deseados o a edades demasiado tempranas, y que "
            "todas las mujeres, en particular las adolescentes, deben tener acceso a la "
            "anticoncepción y a servicios de salud reproductiva."
        ),
        "fuente": "ops_salud_materna",
    },
]

# Datos de contexto verificables (no clínicos).
CONTEXTO = [
    {
        "dato": (
            "Red de servicios de salud pública del MINSA: 79 hospitales, 153 centros de "
            "salud, 1470 puestos de salud y 179 casas maternas con 2,403 camas."
        ),
        "fuente": "minsa_inicio",
    },
    {
        "dato": "Línea directa y gratuita 102 de la Central de Ambulancias del MINSA.",
        "fuente": "minsa_inicio",
    },
    {
        "dato": (
            "Nicaragua tiene 15 departamentos, 2 regiones autónomas y 153 municipios; su "
            "población en 2023 se estimó en 7 046 310 habitantes (OPS/OMS)."
        ),
        "fuente": "ops_nicaragua",
    },
]
