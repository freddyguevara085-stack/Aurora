<div align="center">
  <img src="logo%20para%20el%20readme.png" alt="Logo de Aurora" width="260">
  <h1>Aurora</h1>
  <p><strong>Acompañamiento prenatal claro, cercano y organizado.</strong></p>
  <p>Una aplicación web para ayudar a las gestantes a comprender su etapa de embarazo, organizar sus controles y encontrar orientación para buscar atención.</p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white" alt="Flask 3">
  <img src="https://img.shields.io/badge/MySQL-8.x-4479A1?logo=mysql&logoColor=white" alt="MySQL 8">
  <img src="https://img.shields.io/badge/Tests-pytest-2ea44f" alt="Pruebas con pytest">
</p>

> Aurora ofrece información y organización del seguimiento prenatal. No diagnostica, no prescribe y no sustituye la atención de profesionales de la salud.

## Contenido

- [Qué incluye](#qué-incluye)
- [Tecnologías](#tecnologías)
- [Requisitos](#requisitos)
- [Instalación local](#instalación-local)
- [Base de datos](#base-de-datos)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Pruebas](#pruebas)
- [Despliegue](#despliegue)
- [Estructura](#estructura)
- [Roles](#roles)
- [PWA y modo offline](#pwa-y-modo-offline)
- [Seguridad](#seguridad)
- [Limitaciones y próximos pasos](#limitaciones-y-próximos-pasos)

## Qué incluye

### Para gestantes

- Registro público de cuenta con asignación automática del rol `usuario` y creación del perfil inicial.
- Inicio y cierre de sesión, recuperación segura de contraseña y cambio de contraseña autenticado.
- Perfil de embarazo y ubicación opcional; los datos personales y contactos adicionales son opcionales.
- Registro y edición del embarazo activo, con cálculo orientativo de semana gestacional, trimestre y FPP.
- Registro, consulta, edición y reprogramación de controles prenatales.
- Estados de control: programado, realizado, reprogramado y cancelado.
- Organización de citas y preguntas para conversar con personal de salud; Aurora no prescribe.
- Calendario de controles y recordatorios personales, de control o informativos.
- Guía prenatal, señales de alerta y directorio de centros de atención.

### Para administración

- Panel protegido para gestionar contenidos, señales de alerta, centros y servicios.
- Publicación y desactivación de contenidos del MVP.
- Registro de actividad administrativa mediante auditoría.

## Tecnologías

| Tecnología | Uso |
| --- | --- |
| Python | Lenguaje principal |
| Flask | Aplicación web y blueprints |
| Flask-SQLAlchemy | Modelos y persistencia ORM |
| Flask-Login | Autenticación y sesiones |
| Flask-WTF | Protección CSRF |
| MySQL | Base de datos relacional |
| Jinja2 | Plantillas HTML |
| Service Worker | Caché del shell y fallback offline |
| Waitress | Servidor WSGI para producción en Windows |
| Pytest | Pruebas automatizadas |

## Requisitos

- Python 3.10 o superior.
- MySQL 8.x disponible localmente o en un servidor accesible.
- Git, opcional para clonar el repositorio.
- PowerShell o CMD en Windows.

## Instalación local

Clona el repositorio y entra en la carpeta del proyecto:

```powershell
git clone https://github.com/freddyguevara085-stack/Aurora.git
cd Aurora
```

Crea y activa el entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno, puedes ejecutar directamente `.\.venv\Scripts\python.exe` sin activarlo.

## Base de datos

Aurora usa MySQL y distribuye dos scripts:

- [Aurora_BD.sql](Aurora_BD.sql): crea la base de datos, tablas, relaciones, roles, permisos e índices.
- [database/Aurora_MVP_seed.sql](database/Aurora_MVP_seed.sql): carga contenidos, señales y servicios iniciales.

Desde CMD:

```cmd
mysql -u root -p < Aurora_BD.sql
mysql -u root -p aurora < database\Aurora_MVP_seed.sql
```

Desde PowerShell:

```powershell
Get-Content Aurora_BD.sql | mysql -u root -p
Get-Content database\Aurora_MVP_seed.sql | mysql -u root -p aurora
```

Para producción, utiliza un usuario MySQL dedicado con privilegios mínimos. No uses `root` ni una contraseña vacía.

## Configuración

Copia la plantilla y crea un archivo `.env` local:

```powershell
Copy-Item .env.example .env
```

Variables principales:

```dotenv
SECRET_KEY=una-clave-larga-y-aleatoria
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=aurora
MYSQL_USER=aurora_app
MYSQL_PASSWORD=tu-contraseña
```

Para producción añade:

```dotenv
AURORA_ENV=production
AURORA_DEBUG=0
PORT=5000
SESSION_COOKIE_SECURE=1
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=usuario-smtp
MAIL_PASSWORD=contraseña-smtp
MAIL_DEFAULT_SENDER=Aurora <no-reply@example.com>
```

Nunca publiques `.env`, contraseñas, tokens ni claves SMTP. El archivo está excluido por `.gitignore`.

## Ejecución

### Desarrollo

Con el entorno virtual activo:

```powershell
$env:AURORA_ENV="development"
$env:AURORA_DEBUG="1"
python app.py
```

También puedes ejecutar `run.bat`.

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Crear un usuario administrativo local

```powershell
flask --app app create-user
```

El comando solicita los datos de forma interactiva y nunca recibe la contraseña como argumento.

## Pruebas

Ejecuta la suite desde la raíz del proyecto:

```powershell
python -m pytest -q
```

La suite cubre, entre otros casos:

- Cálculo de semana gestacional y validación de fechas.
- Protección del panel administrativo.
- Protección de rutas de recordatorios.
- Registro y recuperación de contraseña.
- Invalidación de tokens de recuperación reutilizados.
- Cabeceras HTTP de seguridad.

## Despliegue

En Windows, `run.bat` selecciona el modo mediante `AURORA_ENV`:

```cmd
set AURORA_ENV=production
set SESSION_COOKIE_SECURE=1
run.bat
```

En producción, [wsgi.py](wsgi.py) inicia Waitress en `0.0.0.0` y usa la variable `PORT`:

```powershell
$env:AURORA_ENV="production"
$env:PORT="5000"
python wsgi.py
```

Coloca HTTPS delante de Waitress mediante un proxy o balanceador, configura copias de seguridad de MySQL y verifica la restauración antes de aceptar datos reales.

## Estructura

```text
Aurora/
├── app.py                         # Inicialización Flask y registro de extensiones
├── wsgi.py                        # Entrada WSGI con Waitress
├── config.py                      # Configuración desde variables de entorno
├── extensions.py                  # Base de datos, login y CSRF
├── commands.py                    # Comandos CLI de Flask
├── controllers/
│   ├── auth.py                    # Login, registro y recuperación
│   ├── routes.py                  # Flujos de gestante y PWA
│   └── admin.py                   # Panel administrativo
├── models/                        # Modelos SQLAlchemy
├── services/                      # Consultas y servicios de negocio
├── templates/                     # Vistas Jinja2
├── static/                        # CSS, JavaScript, fuentes, assets y PWA
├── tests/                         # Pruebas pytest
├── Aurora_BD.sql                  # Esquema principal MySQL
├── database/Aurora_MVP_seed.sql   # Datos iniciales
├── requirements.txt               # Dependencias
└── run.bat                        # Arranque local o producción en Windows
```

## Roles

| Rol | Acceso |
| --- | --- |
| `usuario` | Perfil, embarazo, controles, recordatorios, calendario, guía, alertas y centros propios/disponibles. |
| `administrador` | Panel de contenidos, señales, centros, servicios y auditoría reciente. |
| `auditor` | Definido en el esquema, pero sin interfaz funcional dedicada en el MVP. |

## PWA y disponibilidad sin conexión

El navegador registra el Service Worker desde [static/js/app.js](static/js/app.js). Se almacenan algunos recursos estáticos y una página general de contingencia. La disponibilidad sin conexión es parcial: perfiles, controles, guía dinámica, centros y recordatorios requieren conexión. Aurora no envía notificaciones en segundo plano; los recordatorios se consultan dentro de la aplicación.

El directorio de demostración solo incluye centros tomados del listado oficial del MINSA (nombre, tipo y ubicación). Teléfonos, horarios, coordenadas y servicios no aparecen en la fuente y no se muestran. `seed-demo` no asigna servicios ni registra fechas de verificación y solo se ejecuta con `AURORA_DEMO=1`. Confirma directamente con el establecimiento antes de acudir.

## Demo para revisión clínica

El contenido clínico no se publica: guía, señales e Inicio permanecen deshabilitados (fail-closed) hasta que exista un proceso de revisión clínica documentado. Para revisarlo con profesionales existe una vista separada, restringida al rol `administrador` y marcada como demo.

Los datos de demostración (perfil ficticio y centros oficiales del MINSA) solo se cargan en una base de demo. `seed-demo` exige `AURORA_DEMO=1`; sin esa variable se cancela para no ensuciar la base real.

1. Activar el modo demo (solo en la base/entorno de demo):
   - PowerShell: `$env:AURORA_DEMO = "1"`
   - Linux/macOS: `export AURORA_DEMO=1`
2. Cargar datos ficticios y centros oficiales: `flask --app app seed-demo`
3. Crear una cuenta revisora con rol `administrador`; la contraseña se pide de forma interactiva y no queda escrita en el código:
   `flask --app app create-user` → elegir el id del rol `administrador`.
4. Iniciar la aplicación: `python app.py`
5. Ingresar en `http://localhost:5000/login` con la cuenta revisora y abrir `http://localhost:5000/demo/revision-clinica`.

La vista muestra el aviso **PENDIENTE DE REVISIÓN CLÍNICA — NO USAR PARA ATENCIÓN** y cita el nombre de la fuente, la URL directa y la fecha de consulta de cada dato. Las fechas de consulta no son fechas de revisión clínica.

## Seguridad

- Contraseñas almacenadas con hash de Werkzeug.
- Protección CSRF global para formularios POST.
- Rutas protegidas con Flask-Login.
- Separación de acceso administrativo mediante rol.
- Tokens de recuperación firmados, temporales y ligados al hash actual de la contraseña.
- Tokens de recuperación enviados por SMTP o mostrados únicamente en la consola local cuando `DEBUG` está activo.
- Cookies HttpOnly, SameSite y `Secure` configurable para HTTPS.
- Cabeceras `nosniff`, `SAMEORIGIN`, Referrer-Policy, XSS Protection y HSTS en modo seguro.
- Consultas ORM parametrizadas y aislamiento de controles/embarazos por usuario autenticado.

## Limitaciones y próximos pasos

Antes de publicar con datos reales, se recomienda completar:

- Migraciones versionadas con Alembic/Flask-Migrate.
- Rate limiting para login, registro y recuperación de contraseña.
- MFA para cuentas administrativas.
- Invalidación centralizada de sesiones al cambiar contraseña o desactivar cuentas.
- Pruebas de integración contra MySQL y pruebas de aislamiento entre usuarios.
- Monitorización, backups y restauración comprobada.
- Política de privacidad, retención y eliminación de datos personales antes de cualquier uso real.
- Revisión clínica responsable, fuentes concretas y validación local del directorio y de teléfonos de emergencia antes de publicar información de salud.

## Licencia

Este repositorio no incluye actualmente un archivo de licencia. Define una licencia antes de distribuirlo públicamente.
