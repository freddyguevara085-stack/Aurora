# Aurora

Aurora es una aplicación web progresiva (PWA) de acompañamiento prenatal. Su objetivo es reunir información práctica y fácil de consultar sobre controles prenatales, señales de alerta y centros de atención cercanos, incluso cuando la conexión a internet es limitada.

El proyecto está pensado como un prototipo de hackatón: debe demostrar una experiencia clara y útil, no reemplazar un sistema clínico ni resolver todos los aspectos del seguimiento de un embarazo.

> **Aviso:** Aurora ofrece información general y no sustituye la valoración, el diagnóstico ni la atención de profesionales de la salud. Ante una emergencia, se debe contactar a los servicios locales correspondientes.

## Problema y propuesta

Durante el embarazo, la información importante puede estar distribuida entre distintas fuentes o depender de una conexión estable. Aurora propone una consulta rápida desde el teléfono mediante tres elementos sencillos:

- Una guía general de controles por etapa del embarazo.
- Un directorio básico de centros de salud y teléfonos de emergencia de una localidad definida.
- Una lista breve de señales de alerta que indican cuándo buscar atención profesional.

La principal ventaja del prototipo es mantener este contenido esencial disponible en una interfaz instalable y con soporte offline básico.

## Estado actual

El repositorio contiene la base técnica del proyecto:

- Servidor Flask y ruta principal.
- Plantillas Jinja con un layout compartido.
- Web App Manifest e icono para instalación.
- Service worker con caché de los recursos esenciales.
- Página inicial de demostración.

Las funciones de contenido prenatal, búsqueda y cálculo de etapa todavía forman parte del MVP por implementar. Esta distinción evita presentar como terminadas características que aún son una propuesta.

## MVP realista para la hackatón

El alcance recomendado, en orden de prioridad, es el siguiente:

1. **Pantalla de inicio clara:** acceso directo a las secciones principales y aviso médico visible.
2. **Etapa aproximada del embarazo:** ingreso opcional de la fecha de última menstruación y cálculo orientativo de semanas en el navegador.
3. **Guía prenatal estática:** lista breve de controles habituales por trimestre, respaldada por una fuente sanitaria confiable y claramente citada.
4. **Directorio local de muestra:** centros de una sola ciudad o zona, almacenados en un archivo local y filtrables por nombre o tipo.
5. **Señales de alerta:** contenido breve, sin diagnósticos ni recomendaciones personalizadas, que indique buscar atención profesional.
6. **Uso offline básico:** acceso a la interfaz y al contenido estático visitado previamente.

Si el tiempo es limitado, las prioridades 1, 3, 4 y 5 forman una demostración completa. El cálculo de semanas y el filtro del directorio son mejoras pequeñas que pueden añadirse después de asegurar el flujo principal.

## Flujo de demostración

Una presentación viable debería permitir:

1. Abrir o instalar Aurora desde un navegador compatible.
2. Consultar la guía de controles prenatales.
3. Buscar un centro dentro del directorio de muestra.
4. Revisar señales de alerta y encontrar un contacto de emergencia.
5. Volver a consultar el contenido esencial sin conexión.

Este flujo es suficiente para demostrar el valor de la propuesta sin depender de cuentas, servidores externos, mapas o notificaciones.

## Fuera del alcance inicial

Para mantener el proyecto realizable, el MVP no incluye:

- Diagnósticos, chat médico o recomendaciones clínicas personalizadas.
- Historias clínicas, expedientes o almacenamiento de documentos médicos.
- Registro de usuarios, autenticación o sincronización entre dispositivos.
- Geolocalización, mapas en tiempo real o cálculo de rutas.
- Actualización automática de hospitales desde servicios externos.
- Notificaciones programadas y recordatorios en segundo plano.
- Panel administrativo, base de datos remota o despliegue de alta disponibilidad.

Estas funciones aumentan considerablemente la complejidad, requieren pruebas adicionales y, en algunos casos, implican responsabilidades de privacidad y seguridad que exceden una demostración de hackatón.

## Decisiones técnicas

| Componente | Tecnología | Uso en el MVP |
| --- | --- | --- |
| Backend | Python 3 y Flask | Rutas HTTP y renderizado de vistas. |
| Presentación | Jinja2, HTML5 y CSS3 | Interfaz responsive y accesible. |
| Interactividad | JavaScript nativo | Cálculo de etapa, filtros y registro del service worker. |
| PWA | Web App Manifest y Service Worker | Instalación y caché offline básica. |
| Datos | Archivos JSON y `localStorage` opcional | Contenido local y preferencias simples, sin datos clínicos. |

Se evita incorporar un framework frontend o una base de datos mientras no sean necesarios. Para el alcance actual, archivos JSON y JavaScript nativo reducen el tiempo de desarrollo y facilitan la demostración.

## Riesgos y límites

- **Exactitud médica:** todo contenido prenatal debe citar y respetar fuentes sanitarias oficiales. Si no puede validarse, no debe presentarse como recomendación.
- **Datos locales:** teléfonos, horarios y direcciones pueden cambiar. El prototipo debe indicar la zona cubierta y la fecha de revisión de los datos.
- **Soporte offline:** la primera visita requiere conexión. El contenido nuevo o no almacenado en caché no estará disponible offline.
- **Compatibilidad PWA:** la instalación y algunas capacidades varían según el navegador y el sistema operativo.
- **Privacidad:** el MVP debe evitar recopilar nombres, documentos, ubicaciones precisas u otros datos sensibles.

## Criterios de éxito

El MVP se considera completo cuando:

- Las secciones principales funcionan correctamente en móvil y escritorio.
- El contenido médico muestra sus fuentes y un aviso de alcance.
- El directorio de muestra puede consultarse y filtrarse sin servicios externos.
- La aplicación conserva su contenido esencial después de una primera visita con conexión.
- La demostración puede completarse sin errores y en pocos minutos.

## Estructura del proyecto

```text
Aurora/
|-- app.py
|-- controllers/
|-- models/
|-- services/
|-- static/
|   |-- css/
|   |-- icons/
|   |-- js/
|   |-- manifest.json
|   `-- service-worker.js
|-- templates/
|   `-- layouts/
`-- requirements.txt
```

Las carpetas `models` y `services` están reservadas para crecimiento futuro. No es necesario llenarlas durante el MVP si la lógica continúa siendo pequeña.

## Instalación local

### Requisitos

- Python 3.10 o superior.
- `pip` y un navegador moderno.

### Pasos

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/freddyguevara085-stack/Aurora.git
   cd Aurora
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv .venv
   ```

   En Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Iniciar la aplicación:

   ```bash
   python app.py
   ```

   En Windows también puede utilizarse `run.bat` después de crear el entorno virtual.

5. Abrir `http://localhost:5000` en el navegador.

## Posibles mejoras posteriores

Solo después de completar y probar el MVP se recomienda evaluar:

- Guardado local de citas sin sincronización.
- Recordatorios, verificando primero las limitaciones de cada navegador.
- Más localidades con un proceso definido para revisar los datos.
- Pruebas automatizadas del cálculo de semanas y de las rutas Flask.
- Despliegue público con configuración segura para producción.

Estas mejoras no son requisitos para presentar una propuesta útil y coherente en la hackatón.
