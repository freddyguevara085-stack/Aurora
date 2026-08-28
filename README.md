# Aurora

Aurora es una aplicación web progresiva para el acompañamiento prenatal. Ayuda a la gestante a organizar su información de embarazo, controles y recursos educativos desde una experiencia móvil, sin sustituir la atención de profesionales de salud.

Estado técnico de referencia: commit `13f7d36` (`feat: completar MVP de Aurora`).

## Funciones principales

- Autenticación por correo y contraseña, con redirección según rol.
- Perfil de gestante con datos personales, ubicación, contacto de emergencia y consentimiento.
- Registro y edición del embarazo activo, cálculo visual de semana y trimestre, y cálculo de FPP desde FUM cuando corresponde.
- Registro, consulta y seguimiento de controles prenatales propios.
- Calendario de controles y recordatorios pendientes.
- Guía prenatal con filtros por trimestre y categoría, más detalle de artículos publicados.
- Señales de alerta activas con orientación para buscar atención profesional cuando corresponda.
- Directorio de centros activos, búsqueda por nombre o municipio, filtro por tipo y detalle de servicios.
- Panel administrativo para contenidos prenatales, señales de alerta, centros de atención y servicios; incluye métricas y eventos recientes de auditoría.
- PWA instalable con caché del shell estático y recursos esenciales tras una visita inicial en línea.

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
| Service Worker y Web App Manifest | Capacidades PWA y disponibilidad básica sin conexión. |
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

```powershell
git clone https://github.com/freddyguevara085-stack/Aurora.git
cd Aurora
```

Crea y activa el entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

En CMD, la activación equivalente es:

```cmd
.venv\Scripts\activate.bat
```

## Configuración local

Copia la plantilla pública de configuración y completa los valores locales necesarios. No subas `.env` al repositorio ni compartas sus valores.

```powershell
Copy-Item .env.example .env
```

La aplicación requiere `SECRET_KEY` y utiliza las variables `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER` y `MYSQL_PASSWORD` para construir la conexión. Los nombres de la base y las credenciales de `.env` deben coincidir con tu instalación local de MySQL.

### Base de datos MySQL

El script [Aurora_BD.sql](Aurora_BD.sql) crea la base `aurora`, sus tablas, claves, índices, roles y permisos. Ejecútalo desde la raíz del repositorio:

```powershell
mysql -u root -p < Aurora_BD.sql
```

Para cargar contenidos, señales y servicios iniciales del MVP, ejecuta el seed idempotente:

```powershell
mysql -u root -p aurora < database\Aurora_MVP_seed.sql
```

El modelo relacional y sus relaciones están definidos en [Aurora_BD.sql](Aurora_BD.sql). No hay un diagrama gráfico separado en el repositorio.

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
| `usuario` | Puede acceder a su perfil, embarazo, controles, calendario, guía, alertas y directorio. Las consultas de seguimiento se limitan al perfil asociado a `current_user.id`. |
| `administrador` | Es el único rol autorizado por `admin_required` para acceder al panel y gestionar contenidos, señales, centros y servicios. El panel muestra actividad reciente de auditoría. |
| `auditor` | Está definido en el esquema con el permiso `consultar_auditoria`, pero el MVP actual no expone una ruta o interfaz específica para este rol. |

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

## PWA y disponibilidad sin conexión

El navegador registra el service worker desde `static/js/app.js`. Tras una visita inicial con conexión, `static/service-worker.js` almacena el manifest, CSS, JavaScript, tipografías e imágenes esenciales del shell de Aurora.

La caché es básica y no convierte Aurora en una aplicación clínica sin conexión: las páginas privadas no se agregan al shell y los datos dinámicos requieren acceso al servidor.

## Limitaciones del MVP

- Aurora brinda acompañamiento informativo; no diagnostica, no prescribe y no sustituye la atención profesional.
- La fecha probable de parto y la semana mostrada son orientativas.
- El directorio comunica cuando un centro no tiene verificación institucional registrada. Confirma teléfono, horario y servicios directamente con el establecimiento antes de acudir.
- El rol `auditor` está modelado en la base de datos, pero su interfaz dedicada no forma parte del MVP actual.

## Estado actual

El MVP del commit `13f7d36` incluye flujos funcionales de gestante, autenticación y roles, panel administrativo, persistencia MySQL, recursos visuales locales y PWA básica. Para cambios posteriores, verifica el estado de la rama con `git status` antes de editar o desplegar.
