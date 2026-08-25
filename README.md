# Aurora

> Contigo desde el primer latido.

Aurora es una aplicación web progresiva de acompañamiento prenatal orientada principalmente a mujeres embarazadas de Nicaragua, en especial primerizas y personas con conectividad limitada. Su interfaz actual presenta una pantalla de inicio responsive con información demostrativa del embarazo y recursos PWA para conservar la interfaz esencial tras una primera visita.

## Problema que aborda

Durante el embarazo, la información sobre controles, señales de alerta y centros de atención puede estar dispersa o no estar disponible en el momento de necesitarla. Aurora plantea una experiencia móvil clara para acompañar a la usuaria entre consultas médicas, sin sustituir la atención profesional.

## Propuesta de valor

Aurora concentra el acompañamiento prenatal en cuatro acciones: organizar el seguimiento del embarazo, recordar controles y citas, consultar información clara sobre cada etapa y señales de alerta, y ubicar centros de atención. La propuesta prioriza lectura sencilla, dispositivos móviles y la disponibilidad de recursos esenciales que ya hayan sido almacenados por el navegador.

## Público objetivo

- Mujeres embarazadas de Nicaragua, especialmente primerizas.
- Personas que requieren una consulta prenatal fácil de comprender desde el teléfono.
- Usuarios con conectividad intermitente que necesitan volver a consultar recursos esenciales cargados previamente.

## Funcionalidades principales

### Implementadas

- Pantalla de inicio responsive renderizada con Flask y plantillas Jinja.
- Tarjeta visual de embarazo con datos demostrativos de semana, trimestre, progreso, tamaño de referencia y próximo control.
- Accesos visuales a calendario, registro de control, señales de alerta, guía y centros; en la versión actual estos enlaces son anclas de la interfaz y no abren módulos independientes.
- Navegación inferior con las secciones Inicio, Embarazo, Guía, Centros y Perfil como estructura visual.
- Web App Manifest, registro de Service Worker y caché del shell de la aplicación, incluidos estilos, JavaScript y recursos gráficos utilizados por la vista de inicio.

### Alcance funcional de Aurora

La propuesta del producto contempla registro e inicio de sesión, cálculo y seguimiento personalizado del embarazo, controles y citas, calendario, recordatorios, información prenatal por etapas, señales de alerta, directorio de centros, búsqueda y filtros. Estas capacidades no están implementadas en el código actual y no se presentan como disponibles en esta versión.

## Alcance responsable y aviso de orientación

Aurora complementa la atención profesional: no diagnostica, no prescribe tratamientos y no sustituye al personal sanitario. La información prenatal y las señales de alerta deben sustentarse en fuentes sanitarias confiables y promover la búsqueda de atención profesional cuando corresponda. La aplicación no declara validación oficial por parte del MINSA.

## Roles y permisos

Los siguientes roles están definidos para el producto. La aplicación actual no incluye autenticación, autorización ni interfaces de administración; por ello estos permisos aún no se aplican mediante código.

| Rol | Permisos definidos |
| --- | --- |
| Usuario | Consultar información y administrar su seguimiento prenatal. |
| Administrador | Mantener centros, contenidos y señales de alerta. |
| Auditor | Consultar el historial de acciones administrativas. |

## Tecnologías utilizadas

| Tecnología | Función en el proyecto |
| --- | --- |
| Python | Lenguaje del servidor. |
| Flask 3.0.2 | Aplicación web, servidor de desarrollo y definición de rutas. |
| Jinja2 | Renderizado de las plantillas HTML. |
| HTML5 y CSS3 | Estructura y diseño responsive de la interfaz. |
| JavaScript | Registro del Service Worker en el navegador. |
| Web App Manifest y Service Worker | Configuración instalable y caché de recursos del shell de la aplicación. |
| MySQL 8.0 o superior | Motor previsto por el esquema relacional de `Aurora_BD.sql`; no está conectado a Flask en la versión actual. |
| python-dotenv 1.0.1 | Dependencia declarada en `requirements.txt`; el código actual no carga variables de entorno. |
| Git y GitHub | Control de versiones y colaboración mediante el repositorio remoto. |

## Arquitectura del proyecto

```text
Aurora/
├── app.py                         # Crea la aplicación Flask y registra el blueprint
├── Aurora_BD.sql                   # Esquema relacional para MySQL 8.0 o superior
├── controllers/
│   └── routes.py                  # Rutas /, /service-worker.js y /manifest.json
├── models/                        # Paquete reservado; no contiene modelos implementados
├── services/                      # Paquete reservado; no contiene servicios implementados
├── static/
│   ├── assets/inicio/             # Imágenes e iconos de la pantalla de inicio
│   ├── css/style.css              # Estilos de la interfaz
│   ├── js/app.js                  # Registro del Service Worker
│   ├── manifest.json              # Configuración de la PWA
│   └── service-worker.js          # Caché del shell de la aplicación
├── templates/
│   ├── layouts/base.html          # Layout base Jinja
│   ├── partials/bottom_nav.html   # Navegación inferior
│   └── index.html                 # Vista de inicio
├── requirements.txt               # Dependencias Python
└── run.bat                        # Inicio local en Windows con .venv
```

## Base de datos

El repositorio incluye `Aurora_BD.sql`, un esquema para MySQL 8.0 o superior. El script crea la base de datos `aurora` con codificación `utf8mb4`, tablas InnoDB, claves foráneas, índices, restricciones y una vista de resumen del embarazo.

Las entidades confirmadas son `roles`, `usuarios`, `perfiles_gestantes`, `embarazos`, `controles_prenatales`, `recordatorios`, `centros_atencion`, `contenidos_prenatales`, `senales_alerta` e `historial_auditoria`. El script también define `vista_resumen_embarazo` para calcular semana, trimestre y progreso del embarazo activo.

La aplicación Flask actual no carga este script, no contiene configuración de conexión a MySQL y no define modelos en `models/`. En consecuencia, la interfaz sigue usando datos demostrativos y no hay formularios funcionales conectados a persistencia.

## Requisitos previos

- Python 3 con `venv` disponible.
- `pip`.
- Un navegador moderno con soporte para Service Workers para comprobar las capacidades PWA.
- Git, si se clonará el repositorio.

## Instalación local

1. Clone el repositorio y entre en su carpeta:

```bash
git clone https://github.com/freddyguevara085-stack/Aurora.git
cd Aurora
```

2. Cree el entorno virtual.

Windows PowerShell:

```powershell
py -m venv .venv
```

Windows CMD:

```cmd
py -m venv .venv
```

Linux/macOS:

```bash
python3 -m venv .venv
```

3. Active el entorno e instale las dependencias.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Windows CMD:

```cmd
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Configuración de variables de entorno

La aplicación actual no lee variables de entorno. Aunque el repositorio incluye `.env.example`, este archivo está vacío y no se requiere configurarlo para ejecutar el sistema localmente.

El archivo `.gitignore` excluye `.env`, los entornos virtuales, cachés de Python y archivos de bases de datos locales (`*.db` y `*.sqlite3`) del control de versiones.

## Ejecución del sistema

Con las dependencias instaladas, ejecute `app.py` desde la raíz del proyecto.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe app.py
```

Windows CMD:

```cmd
.venv\Scripts\python.exe app.py
```

Linux/macOS:

```bash
python3 app.py
```

En Windows también está disponible el script `run.bat`, que usa `.venv\Scripts\python.exe` cuando el entorno virtual existe:

```cmd
run.bat
```

Abra la aplicación en [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

## Recorrido básico

1. Inicie el servidor y abra la URL local.
2. Compruebe la tarjeta de embarazo, el próximo control y las secciones visuales de la pantalla de inicio.
3. Verifique la navegación inferior y los accesos visuales; en esta versión no llevan a módulos funcionales separados.
4. En un navegador compatible, recargue la página una vez para registrar `/service-worker.js`. El Service Worker almacena el shell definido en `static/service-worker.js`, por lo que esos recursos pueden estar disponibles posteriormente con conectividad limitada.

## Seguridad y buenas prácticas

- La aplicación separa rutas, plantillas, recursos estáticos, modelos y servicios en directorios definidos.
- Los recursos de la interfaz se sirven mediante `url_for` en las plantillas, lo que evita rutas estáticas duplicadas en el HTML.
- El repositorio ignora archivos locales sensibles y generados, incluidos `.env`, `.venv/`, `__pycache__/`, `*.db` y `*.sqlite3`.
- La clave secreta configurada en `app.py` es adecuada solo para desarrollo local. Antes de cualquier despliegue debe reemplazarse por una configuración segura fuera del código fuente.
- El servidor se inicia con `debug=True`; no debe utilizarse esa configuración en un entorno de producción.

## Control de versiones

El repositorio usa Git y mantiene un remoto en GitHub. La rama principal actual es `main`; también existen referencias históricas de trabajo en `develop` y `temporal`, integradas en el historial de `main`. Los archivos fuente, recursos PWA y documentación se versionan en el repositorio, mientras que los entornos locales y datos locales se excluyen con `.gitignore`.

## Estado real del proyecto

Aurora cuenta con una base Flask navegable en la ruta principal, una interfaz de inicio responsive, una configuración PWA con caché de recursos esenciales y un esquema relacional MySQL documentado en `Aurora_BD.sql`. Los datos mostrados en la vista son demostrativos y están definidos en `controllers/routes.py`.

No hay registro o inicio de sesión, gestión de perfiles, conexión de Flask a MySQL, persistencia de datos, formularios operativos, calendario funcional, recordatorios, búsqueda de centros, directorio, contenido prenatal gestionable, señales de alerta administrables, historial de auditoría ni aplicación efectiva de roles. Estas diferencias son relevantes frente al alcance de producto y a los entregables completos de la categoría.

## Limitaciones responsables

- El contenido mostrado no constituye una recomendación clínica personalizada.
- La caché se limita a los recursos del shell definidos en el Service Worker; no equivale a funcionamiento completamente sin conexión.
- La pantalla actual utiliza datos de demostración, no información personal ni registros médicos.
- Los enlaces a secciones futuras son elementos de interfaz y no rutas implementadas.

## Hackathon Nicaragua 2026

Este repositorio se prepara para la preclasificación del Hackathon Nicaragua 2026, categoría Aficionado. El documento presenta de forma verificable la descripción general, las tecnologías utilizadas, la instalación básica y la ejecución local del sistema, y distingue el prototipo implementado del alcance completo propuesto para Aurora.
