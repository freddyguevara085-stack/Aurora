# Aurora

**Información prenatal clara, cercana y disponible cuando se necesita.**

Aurora es una aplicación web progresiva (PWA) de acompañamiento prenatal. Reúne en una sola experiencia información práctica sobre las etapas del embarazo, controles prenatales, señales de alerta y centros de atención.

Nuestro propósito es brindar una herramienta sencilla, confiable y fácil de consultar desde el teléfono. Al funcionar como PWA, Aurora podrá instalarse desde un navegador compatible y conservar su contenido esencial para consultas posteriores, incluso cuando la conexión sea limitada.

El proyecto se desarrolla como una propuesta de hackatón en categoría aficionado, combinando utilidad social, diseño accesible y una implementación técnica realista.

> **Aviso:** Aurora ofrece información general de orientación y promueve la búsqueda oportuna de atención profesional.

## Nuestra motivación

El embarazo es una etapa en la que surgen preguntas frecuentes y se necesita consultar información con rapidez. Sin embargo, los datos importantes pueden estar repartidos entre distintas fuentes, redactados de forma complicada o depender permanentemente de una conexión a internet.

Aurora nace para organizar esa información en una interfaz amigable. La aplicación busca acompañar la consulta diaria, ayudar a reconocer información importante y facilitar el acceso a centros de atención disponibles en la comunidad.

## Objetivo general

Desarrollar una aplicación web progresiva que facilite el acceso a información prenatal organizada, señales de alerta y datos de centros de salud mediante una experiencia responsive, instalable y con soporte offline básico.

## ¿Cómo acompaña Aurora?

Aurora concentra su experiencia en cuatro áreas principales:

### Guía prenatal

Presenta información breve y ordenada por trimestre para ayudar a comprender los controles y cuidados generales correspondientes a cada etapa del embarazo. Cada contenido deberá mostrar una fuente sanitaria confiable y su fecha de revisión.

### Señales de alerta

Ofrece una sección visible y fácil de entender con situaciones que requieren buscar atención profesional. Su diseño priorizará mensajes directos, lectura rápida y acceso inmediato al directorio de centros.

### Directorio de centros

Permite consultar centros de salud de una ciudad o zona seleccionada. La información podrá incluir nombre, tipo de establecimiento, municipio, dirección, teléfono, horario y fecha de verificación.

### Experiencia PWA

Permite utilizar Aurora como una aplicación instalable desde el navegador. El contenido esencial previamente cargado podrá mantenerse disponible mediante un service worker y una estrategia básica de caché.

## Propuesta de valor

Aurora reúne en una sola herramienta tres cualidades principales:

- **Claridad:** información organizada y presentada con lenguaje comprensible.
- **Accesibilidad:** interfaz adaptable a teléfonos y computadoras.
- **Disponibilidad:** contenido esencial preparado para consultas con conectividad limitada.

La combinación de estas cualidades convierte a Aurora en una guía de consulta práctica que acerca información prenatal y recursos locales a quienes los necesitan.

## Funcionalidades del MVP

La primera versión funcional contempla:

1. Pantalla de inicio con acceso directo a las secciones principales.
2. Guía prenatal organizada por trimestre.
3. Sección de señales de alerta.
4. Directorio local de centros de salud.
5. Buscador y filtros por nombre, municipio o tipo de centro.
6. Formularios básicos para gestionar la información del directorio.
7. Permisos definidos para administrador, usuario y auditor.
8. Registro básico de acciones administrativas.
9. Diseño responsive para móvil y escritorio.
10. Instalación como PWA y funcionamiento offline básico.

La base de datos y los roles apoyarán la organización y actualización de la información, mientras que la experiencia pública seguirá concentrada en la consulta prenatal.

## Usuarios y responsabilidades

| Rol | Participación en Aurora |
| --- | --- |
| Usuario | Consulta la guía prenatal, las señales de alerta y el directorio. |
| Administrador | Mantiene actualizados los centros y contenidos disponibles. |
| Auditor | Revisa el historial de acciones para apoyar la integridad de la información. |

## Estado actual del proyecto

Aurora cuenta con su base técnica inicial:

- Aplicación Flask en funcionamiento.
- Controlador con la ruta principal.
- Plantillas Jinja y layout HTML compartido.
- Página inicial de demostración.
- Web App Manifest e icono de instalación.
- Service worker con caché inicial.
- Registro del service worker mediante JavaScript.
- Script de arranque para Windows.
- Estructura preparada para incorporar modelos y servicios.

El desarrollo continuará con la construcción de la interfaz, los módulos de contenido, el directorio y la persistencia de datos.

## Tecnologías utilizadas

| Tecnología | Función dentro del proyecto |
| --- | --- |
| Python 3 | Lenguaje principal del backend. |
| Flask | Servidor, rutas y renderizado de vistas. |
| Jinja2 | Plantillas y reutilización de layouts. |
| HTML5 | Estructura semántica de la interfaz. |
| CSS3 | Diseño visual y adaptación a diferentes pantallas. |
| JavaScript | Interactividad y comportamiento de la PWA. |
| Web App Manifest | Configuración de la aplicación instalable. |
| Service Worker | Caché y acceso offline básico. |
| Git y GitHub | Control de versiones y evidencia del avance. |

SQLite y las dependencias de autenticación se incorporarán durante la etapa correspondiente del desarrollo.



## Instalación local

### Requisitos

- Python 3.10 o superior.
- `pip`.
- Git.
- Un navegador moderno.

### Pasos

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/freddyguevara085-stack/Aurora.git
   cd Aurora
   ```

2. Crear un entorno virtual:

   ```bash
   python -m venv .venv
   ```

3. Activar el entorno virtual.

   En Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   En Windows CMD:

   ```bat
   .venv\Scripts\activate.bat
   ```

   En Linux o macOS:

   ```bash
   source .venv/bin/activate
   ```

4. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

Con el entorno virtual activado, ejecutar:

```bash
python app.py
```

En Windows también se puede iniciar con:

```bat
run.bat
```

Después, abrir en el navegador:

```text
http://localhost:5000
```

## Experiencia de demostración

El recorrido principal de Aurora permitirá:

1. Abrir o instalar la aplicación desde el navegador.
2. Explorar información correspondiente a una etapa del embarazo.
3. Consultar las señales de alerta.
4. Buscar un centro de atención mediante filtros sencillos.
5. Acceder nuevamente al contenido esencial después de una primera visita con conexión.

## Ruta de desarrollo

El proyecto avanzará en el siguiente orden:

1. Completar la identidad visual, la navegación y el diseño responsive.
2. Desarrollar la guía prenatal y la sección de señales de alerta.
3. Diseñar el modelo entidad-relación.
4. Implementar el directorio de centros y sus filtros.
5. Integrar la base de datos y los formularios de gestión.
6. Aplicar los roles y permisos definidos.
7. Registrar las acciones administrativas relevantes.
8. Completar la estrategia de caché y probar el funcionamiento offline.
9. Realizar pruebas funcionales y preparar la demostración final.

## Criterios de éxito

Aurora tendrá un MVP completo cuando:

- La navegación sea clara en móvil y escritorio.
- La guía y las señales de alerta presenten información organizada y con fuentes.
- El directorio permita encontrar centros mediante búsqueda y filtros.
- Los formularios mantengan actualizada la información presentada.
- Cada rol pueda realizar únicamente las acciones que le corresponden.
- El contenido esencial pueda consultarse después de una primera visita con conexión.
- El recorrido principal pueda demostrarse de forma fluida y sin errores.

## Enfoque responsable

Aurora está orientada a la educación y a la consulta de información general. El contenido se seleccionará a partir de fuentes sanitarias confiables, se identificará su fecha de revisión y se mantendrá visible el llamado a buscar atención profesional cuando corresponda.

---

**Aurora busca acompañar cada etapa con información cercana, organizada y accesible.**
