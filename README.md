# Aurora

Aurora es una aplicación móvil de acompañamiento prenatal orientada a facilitar el acceso oportuno a información práctica durante el embarazo. Su propuesta de valor consiste en centralizar, incluso sin conexión a internet, un calendario de controles prenatales y un directorio de centros de salud y hospitales locales, para que la persona usuaria pueda organizar sus consultas y ubicar apoyo cercano con rapidez.

La aplicación prioriza una experiencia simple, clara y offline-first: los datos esenciales se almacenan en el dispositivo y se consultan sin depender de conectividad continua. El contenido informativo no sustituye la valoración, diagnóstico ni atención de profesionales de la salud.

## Características principales (MVP)

- **Calendario de controles prenatales:** registro de fecha estimada de parto o última menstruación, visualización de controles sugeridos por etapa y seguimiento del estado de cada cita.
- **Recordatorios locales:** notificaciones programadas para próximos controles, con opción de marcar una cita como completada o reprogramarla.
- **Directorio de salud y emergencia:** listado local de centros de salud, hospitales y contactos de emergencia con teléfono, dirección, horario y servicios disponibles.
- **Búsqueda rápida del directorio:** filtrado por nombre, tipo de centro o zona para encontrar un contacto relevante con menos pasos.
- **Información breve de señales de alerta:** pantalla de consulta con recomendaciones para buscar atención profesional inmediata ante síntomas que requieran evaluación. Debe validarse con fuentes sanitarias locales antes de su publicación.

## Stack tecnológico

Aurora se implementa como una **Progressive Web App (PWA)** con un backend ligero en Python. Esta arquitectura permite ejecutarla desde el navegador, instalarla en dispositivos compatibles y conservar recursos esenciales para su uso sin conexión.

| Componente | Tecnología recomendada | Propósito |
| --- | --- | --- |
| Backend y servidor | Python 3 con Flask | Enrutamiento HTTP, composición de vistas y punto de entrada de la aplicación. |
| Capa de presentación | Jinja2, HTML5 y CSS3 | Plantillas renderizadas en servidor e interfaz responsive. |
| Interactividad | JavaScript nativo | Registro del service worker y comportamiento dinámico de la interfaz. |
| Capacidades PWA | Web App Manifest y Service Worker | Instalación web, caché de recursos y funcionamiento offline básico. |
| Datos locales | Cache Storage e IndexedDB | Disponibilidad offline de recursos y persistencia futura de citas y directorio. |
| Configuración | `python-dotenv` y archivo `.env` | Gestión de variables de entorno durante el desarrollo. |

La aplicación ya separa rutas, plantillas, recursos estáticos y capas reservadas para modelos y servicios. Como siguiente etapa, puede incorporarse una base de datos local o remota para actualizar el directorio y respaldar información con consentimiento explícito, sin que sea un requisito para el MVP.

## Instalación y configuración básica

### Requisitos previos

- Python 3.10 o superior.
- `pip` y un entorno virtual de Python.
- Un navegador moderno con soporte para PWA, preferiblemente Chrome, Edge o Firefox.

### Pasos

1. Clonar el repositorio y entrar al directorio del proyecto:

   ```bash
   git clone <URL_DEL_REPOSITORIO>
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

3. Instalar las dependencias del backend:

   ```bash
   pip install -r requirements.txt
   ```

4. Crear la configuración local a partir del ejemplo, si el proyecto la requiere:

   ```bash
   cp .env.example .env
   ```

   En Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Iniciar el entorno de desarrollo:

   ```bash
   python app.py
   ```

6. Abrir `http://localhost:5000` en el navegador. Para probar la instalación, use la opción de instalar aplicación que ofrece el navegador.


