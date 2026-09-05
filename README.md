# Aurora

Aurora es una aplicación web de acompañamiento prenatal. Su MVP busca que una gestante pueda entender en qué etapa está, organizar su próximo control y encontrar orientación para buscar ayuda. No diagnostica, no prescribe ni sustituye la atención de profesionales de salud.

## Alcance del MVP

El recorrido principal que valida Aurora es: iniciar sesión, completar el perfil y embarazo, consultar la semana gestacional, registrar un control y acceder a señales de alerta y centros de atención.

### Funciones principales para la gestante

- Inicio de sesión por correo y contraseña.
- Perfil con datos personales, ubicación, contacto de emergencia y consentimiento.
- Registro y edición del embarazo activo, con cálculo visual orientativo de semana, trimestre y FPP desde la FUM cuando corresponde.
- Registro y consulta de controles prenatales propios.
- Calendario de controles y consulta de recordatorios pendientes previamente registrados.
- Señales de alerta con orientación para buscar atención profesional.
- Directorio de centros activos, con búsqueda, filtros y detalle de servicios.

### Funciones complementarias

- Guía prenatal con filtros por trimestre y categoría.
- Instalación como PWA y caché de recursos estáticos esenciales. Los datos dinámicos y las páginas privadas requieren conexión al servidor.

### Soporte interno

El repositorio también contiene un panel administrativo para mantener contenidos, señales, centros y servicios, además de mostrar métricas y eventos recientes de auditoría. Este panel facilita la demostración y operación del MVP, pero no forma parte de la propuesta de valor principal para la gestante.

### Fuera del alcance actual

- Registro público y recuperación de contraseña.
- Creación, edición o envío automático de recordatorios y notificaciones.
- Edición o reprogramación de controles ya registrados.
- Funcionamiento completo sin conexión.
- Interfaz dedicada para el rol `auditor`.
- Integraciones con expedientes clínicos o sistemas institucionales.

## Tecnologías

| Tecnología | Uso en Aurora |
| --- | --- |
| Python y Flask | Aplicación web, blueprints y servidor de desarrollo. |
| Flask-SQLAlchemy y PyMySQL | Modelos ORM y conexión a MySQL. |
| Flask-Login | Sesiones de usuario y protección de rutas. |
| Flask-WTF | Protección CSRF para formularios. |
| Flask-Migrate | Integración de migraciones para el proyecto. |
| Jinja2, HTML y CSS | Plantillas y diseño responsive. |
| Poppins e iconos Material Symbols locales | Tipografía e iconografía sin CDN. |
| Service Worker y Web App Manifest | Instalación PWA y caché del shell estático. |
| MySQL | Persistencia relacional. |

## Estructura del proyecto

```text
Aurora/
├── app.py                         # Inicialización Flask y registro de blueprints
├── config.py                      # Configuración desde variables de entorno
├── extensions.py                  # db, login manager, CSRF y migraciones
├── commands.py                    # Comando Flask para crear usuarios
├── controllers/
│   ├── auth.py                    # Inicio y cierre de sesión
│   ├── routes.py                  # Flujos de la gestante y recursos PWA
│   └── admin.py                   # Panel administrativo y validaciones
├── models/                        # Modelos SQLAlchemy de acceso, gestación, contenido y directorio
├── services/                      # Consultas de negocio, inicio y auditoría
├── templates/
│   ├── admin/                     # Vistas Jinja del panel administrativo
│   ├── layouts/ y partials/       # Layout, navegación y componentes reutilizables
│   └── *.html                     # Vistas de autenticación y gestante
├── static/
│   ├── assets/                    # Recursos visuales locales
│   ├── css/style.css              # Estilos de la aplicación
│   ├── fonts/                     # Poppins e iconos locales
│   ├── js/app.js                  # Registro del service worker
│   ├── manifest.json              # Manifest PWA
│   └── service-worker.js          # Caché del shell estático
├── Aurora_BD.sql                  # Esquema y catálogo base de MySQL
├── database/Aurora_MVP_seed.sql   # Datos iniciales idempotentes del MVP
├── requirements.txt
└── run.bat
```

La separación anterior corresponde al patrón MVC: los controladores reciben las solicitudes, los modelos representan los datos, los servicios concentran consultas reutilizables y las plantillas renderizan las vistas.

## Requisitos previos

- Python 3 con `venv` y `pip`.
- MySQL disponible localmente.
- Git, si se clonará el repositorio.
- Navegador moderno con soporte de Service Worker para probar la PWA.

## Instalación en Windows

Clona el proyecto y entra a su carpeta:

```bash
git clone https://github.com/freddyguevara085-stack/Aurora.git
cd Aurora
```

### Entorno virtual y dependencias

Crea el entorno virtual e instala las dependencias según la terminal que utilices:

**Opción A — PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**Opción B — CMD (Símbolo del sistema):**

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

## Configuración local

Copia la plantilla pública de configuración y completa los valores locales necesarios. No subas `.env` al repositorio ni compartas sus valores.

- En PowerShell:
  ```powershell
  Copy-Item .env.example .env
  ```
- En CMD:
  ```cmd
  copy .env.example .env
  ```

La aplicación requiere `SECRET_KEY` y utiliza las variables `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER` y `MYSQL_PASSWORD` para construir la conexión. Los nombres de la base y las credenciales de `.env` deben coincidir con tu instalación local de MySQL.

## Base de datos MySQL

### Importación por consola (CMD)

El script [Aurora_BD.sql](Aurora_BD.sql) crea la base `aurora`, sus tablas, claves, índices, roles y permisos. Para cargar contenidos, señales y servicios iniciales del MVP, se ejecuta el seed idempotente [database/Aurora_MVP_seed.sql](database/Aurora_MVP_seed.sql).

Dado que el operador de redirección `<` está reservado en PowerShell y produce un error de sintaxis, los siguientes comandos deben ejecutarse en **CMD (Símbolo del sistema)** desde la raíz del repositorio:

```cmd
mysql -u root -p < Aurora_BD.sql
mysql -u root -p aurora < database\Aurora_MVP_seed.sql
```

> **Nota para PowerShell:** Si prefieres importar utilizando PowerShell en lugar de CMD, utiliza el paso de contenido por tubería (*pipe*):
> ```powershell
> Get-Content Aurora_BD.sql | mysql -u root -p
> Get-Content database\Aurora_MVP_seed.sql | mysql -u root -p aurora
> ```

### Alternativa gráfica desde MySQL Workbench

Si prefieres importar la base de datos visualmente sin usar la consola:

1. Abre **MySQL Workbench** y conéctate a tu servidor local de MySQL.
2. **Esquema y catálogos base**: Ve al menú **File > Open SQL Script...** (o pulsa `Ctrl + Shift + O`), selecciona el archivo [Aurora_BD.sql](Aurora_BD.sql) de la raíz del proyecto y presiona el icono de rayo (**Execute / `Ctrl + Shift + Enter`**). Esto creará la base de datos `aurora`, las tablas, índices, roles y permisos.
3. **Datos iniciales (Seed)**: De la misma forma, abre el archivo [database/Aurora_MVP_seed.sql](database/Aurora_MVP_seed.sql) y ejecútalo (asegurándote de que el esquema `aurora` esté seleccionado o activo) para cargar los contenidos prenatales, señales de alerta y servicios iniciales del MVP.

### Diagrama Entidad-Relación

El diagrama Entidad-Relación (ER) ya existe y se entrega por separado como parte de los entregables oficiales de la competencia (Hackathon Nicaragua 2026, categoría Aficionado). No se incluye un archivo gráfico del diagrama dentro de este repositorio; todas las entidades, claves primarias, foráneas, restricciones de integridad e índices se encuentran íntegramente implementadas y documentadas en [Aurora_BD.sql](Aurora_BD.sql).

## Normalización de la base de datos (1FN y 2FN)

El diseño del esquema relacional en [Aurora_BD.sql](Aurora_BD.sql) fue analizado y estructurado bajo las reglas de normalización:

### Primera Forma Normal (1FN)

- **Criterio**: Requiere que cada campo contenga exclusivamente valores atómicos (indivisibles), que no existan grupos repetitivos ni atributos multivaluados en una misma columna, y que cada tabla cuente con una clave primaria que identifique de forma única cada tupla.
- **Justificación en el esquema real**:
  - Las entidades principales (`roles`, `permisos`, `usuarios`, `perfiles_gestantes`, `embarazos`, `controles_prenatales`, `centros_atencion`, `servicios`, `recordatorios`, `contenidos_prenatales` y `senales_alerta`) descomponen la información en columnas con tipos de datos atómicos escalares (`int`, `varchar`, `date`, `decimal`, etc.) y cuentan con claves primarias definidas (`id`).
  - Las relaciones de muchos a muchos no emplean listas o cadenas delimitadas dentro de un solo campo, sino tablas intermedias asociativas (`roles_permisos` y `centros_servicios`), preservando la atomicidad.
- **Inconsistencia técnica identificada (reporte sin modificación del SQL)**:
  - En la tabla `historial_auditoria`, la columna `detalles` se define como tipo `json` (`detalles json null`). En la teoría relacional clásica (1FN estricta), un objeto JSON contiene una estructura semiestructurada no atómica (pares clave-valor). Si bien es una práctica estándar y eficiente en motores modernos como MySQL para almacenar registros de auditoría sin proliferación excesiva de tablas, desde una perspectiva formal estricta representa una excepción a la regla de atomicidad de la 1FN.

### Segunda Forma Normal (2FN)

- **Criterio**: Requiere satisfacer 1FN y garantizar que todos los atributos no clave dependan funcionalmente de la totalidad de la clave primaria (dependencia funcional completa), sin dependencias parciales respecto a subconjuntos de claves compuestas.
- **Tablas con clave primaria simple**:
  - En todas las tablas cuya clave primaria consta de una única columna subrogada (`id`) —tales como `usuarios`, `perfiles_gestantes`, `embarazos`, `centros_atencion`, `servicios`, `recordatorios`, `contenidos_prenatales` y `senales_alerta`— no existe la posibilidad matemática de una dependencia parcial de la clave primaria (al no existir un subconjunto propio de una clave de un solo atributo). Por lo tanto, cumplen 2FN intrínsecamente.
- **Claves compuestas y ausencia de dependencias parciales**:
  - **`roles_permisos`** (clave primaria compuesta: `(rol_id, permiso_id)`):
    - Atributo no clave: `asignado_at` (marca temporal de asignación).
    - *Justificación*: El campo `asignado_at` indica el momento exacto en que un permiso específico fue concedido a un rol específico. No depende de `rol_id` en solitario (el rol existe independientemente de cuándo se asignó un permiso particular) ni de `permiso_id` en solitario (el permiso existe con anterioridad a su vinculación). Depende funcionalmente de la combinación completa `(rol_id, permiso_id)`. Al no existir dependencias parciales, cumple 2FN.
  - **`centros_servicios`** (clave primaria compuesta: `(centro_atencion_id, servicio_id)`):
    - Atributos no clave: `disponible`, `observaciones`, `fecha_verificacion`, `created_at`, `updated_at`.
    - *Justificación*: Los atributos `disponible` (si la sede ofrece o no el servicio), `observaciones` (condiciones locales de atención) y `fecha_verificacion` (fecha en la que se constató el servicio en esa sede) describen exclusivamente la prestación de un servicio concreto en una sede puntual. Los datos generales del centro (nombre, municipio, teléfono, ubicación) residen en `centros_atencion`, y los del servicio (nombre, descripción general) en `servicios`. Ningún atributo no clave depende únicamente de `centro_atencion_id` ni únicamente de `servicio_id`, sino de la clave compuesta completa `(centro_atencion_id, servicio_id)`. Se garantiza la ausencia de dependencias parciales, cumpliendo 2FN.
  - **`controles_prenatales`**:
    - Posee una clave primaria subrogada `id` y una clave candidata única compuesta `(embarazo_id, numero_control)`. Todos los atributos descriptivos del control (`fecha_control`, `hora_control`, `edad_gestacional_semanas`, `estado`, `indicaciones`, `notas`, etc.) dependen funcionalmente de esa consulta médica específica en ese embarazo; no dependen únicamente del número ordinal de control ni únicamente del embarazo.

## Ejecutar Flask localmente

Con `.venv` activado y `.env` configurado:

```powershell
.\.venv\Scripts\python.exe app.py
```

También puedes usar:

```cmd
run.bat
```

Abre [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

Para crear una cuenta local mediante el comando interactivo de Flask:

```powershell
flask --app app create-user
```

## Rutas principales

| Área | Rutas |
| --- | --- |
| Autenticación | `GET/POST /login`, `POST /logout` |
| Inicio y perfil | `/`, `GET/POST /perfil` |
| Embarazo | `GET/POST /embarazo`, `/embarazo?editar=1` |
| Controles | `/controles`, `GET/POST /controles/nuevo`, `/calendario` |
| Información | `/guia`, `/guia/<contenido_id>`, `/alertas` |
| Directorio | `/centros`, `/centros/<centro_id>` |
| Administración | `/admin/`, `/admin/contenidos`, `/admin/senales`, `/admin/centros`, `/admin/servicios` y sus formularios de alta, edición, cambio de estado y eliminación |
| PWA | `/manifest.json`, `/service-worker.js` |

## Roles y permisos

| Rol | Estado real en el MVP |
| --- | --- |
| `usuario` | Puede acceder a su perfil, embarazo, controles, calendario, guía, alertas y directorio. Las consultas se limitan al perfil asociado a `current_user.id`. |
| `administrador` | Es el único rol autorizado por `admin_required` para acceder al panel y gestionar contenidos, señales, centros y servicios. El panel muestra actividad reciente de auditoría. |
| `auditor` | Está previsto en el esquema con el permiso `consultar_auditoria`, pero queda fuera del alcance funcional actual porque no existe una ruta o interfaz específica para este rol. |

Los permisos se modelan en las tablas `roles`, `permisos` y `roles_permisos`. La autorización actualmente aplicada en las rutas administrativas exige explícitamente el rol `administrador`.

## Seguridad aplicada

- Contraseñas verificadas mediante hashes de Werkzeug; el comando de creación de usuarios genera hashes y no recibe contraseñas por argumentos.
- CSRF global con Flask-WTF en los formularios POST.
- Rutas protegidas con `login_required`.
- Restricción de administración mediante `admin_required` y comprobación de rol.
- Consultas de embarazo, perfil y controles ligadas a la persona autenticada; no aceptan identificadores de perfil, embarazo o usuario enviados por cliente para seleccionar datos ajenos.
- `POST /logout` protegido por sesión y CSRF; `GET /logout` no está disponible.
- Redirección `next` de login normalizada para aceptar solo rutas locales seguras.
- Rollback ante errores SQL en operaciones de escritura.

## PWA y caché estática

El navegador registra el service worker desde `static/js/app.js`. Tras una visita inicial con conexión, `static/service-worker.js` almacena el manifest, CSS, JavaScript, tipografías e imágenes esenciales del shell de Aurora.

Esta capacidad permite instalar la aplicación y reutilizar recursos visuales ya descargados; no ofrece un modo funcional sin conexión. Las páginas privadas no se agregan al shell y los datos dinámicos requieren acceso al servidor.

## Limitaciones del MVP

- Aurora brinda acompañamiento informativo; no diagnostica, no prescribe y no sustituye la atención profesional.
- La fecha probable de parto y la semana mostrada son orientativas.
- El directorio comunica cuando un centro no tiene verificación institucional registrada. Confirma teléfono, horario y servicios directamente con el establecimiento antes de acudir.
- Las cuentas se crean localmente mediante un comando administrativo; no existe registro público ni recuperación de contraseña.
- Los recordatorios existentes solo se consultan. El MVP no los crea, envía ni convierte en notificaciones del dispositivo.
- Los controles pueden registrarse y consultarse, pero todavía no editarse o reprogramarse desde la interfaz de la gestante.
- El proyecto aún no incluye una suite de pruebas automatizadas.
- Un despliegue con datos reales requeriría validación clínica y legal, controles adicionales de privacidad y seguridad, copias de respaldo y una configuración de producción.

## Estado actual

El MVP incluye el recorrido principal de la gestante, autenticación, persistencia MySQL, contenidos de apoyo, directorio de centros y un panel administrativo de soporte. La prioridad antes de ampliar el alcance es validar el recorrido principal con usuarias, incorporar pruebas automatizadas y cerrar los requisitos necesarios para un despliegue seguro.
