<div align="center">
  <img src="logo%20para%20el%20readme.png" alt="Logo de Aurora" width="260">
  <h1>Aurora</h1>
  <p><strong>Un puente entre la vida diaria y la atención prenatal.</strong></p>
  <p>Una aplicación web para organizar controles, preparar preguntas y coordinar el traslado y la red de apoyo de una gestante.</p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white" alt="Flask 3">
  <img src="https://img.shields.io/badge/MySQL-8.x-4479A1?logo=mysql&logoColor=white" alt="MySQL 8">
  <img src="https://img.shields.io/badge/Tests-pytest-2ea44f" alt="Pruebas con pytest">
</p>

> Aurora organiza la preparación para la atención prenatal. No interpreta síntomas, diagnostica, prescribe ni sustituye al personal o a los servicios de salud.

## Contenido

- [Alcance del producto](#alcance-del-producto)
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
- [PWA y disponibilidad sin conexión](#pwa-y-disponibilidad-sin-conexión)
- [Seguridad](#seguridad)
- [Limitaciones y próximos pasos](#limitaciones-y-próximos-pasos)

## Alcance del producto

- **Qué es:** un puente organizativo entre la vida diaria de una gestante y su atención prenatal.
- **Qué ofrece:** etapa orientativa del embarazo, agenda de controles, preguntas para la consulta, plan de traslado y apoyo, contactos personales y fichas imprimibles.
- **Qué no ofrece:** diagnóstico, interpretación de síntomas, tratamientos, protocolos clínicos ni sustitución de la atención profesional.

Quedaron **fuera del producto** el seguimiento de preeclampsia y el de puerperio, lactancia y recién nacido: sus rutas devuelven 404 y no aparecen en la navegación. El contenido clínico (guía y señales) permanece cerrado al público hasta contar con revisión clínica documentada.

## Qué incluye

Aurora está diseñada como un **medio sencillo de organización** entre la gestante, su familia y la atención profesional. Su alcance se limita a tareas prácticas que la usuaria puede preparar sin convertir la aplicación en un servicio médico.

### 1. Embarazo y controles
- Registro y seguimiento del embarazo activo con cálculo orientativo de semana gestacional, trimestre y FPP.
- Registro, reprogramación y consulta de controles prenatales (programados, realizados, reprogramados).
- **Preguntas para la consulta:** dudas anotadas por la gestante para conversar con el personal de salud.
- Hoja imprimible de preparación de la cita (`/consulta/imprimir`).

### 2. Traslado y apoyo familiar
- **Plan de traslado y apoyo (`/plan-parto`):** lugar previsto, acompañante, persona a cargo del hogar, transporte y preparativos básicos.
- **Contactos personales (`/red-comunitaria`):** familiares, personas de confianza y transporte confirmados por la usuaria, con enlace de llamada `tel:`.
- **Ficha familiar (`/plan-parto/imprimir`):** hoja compacta con la logística y los contactos registrados.

### 3. Para administración
- Panel protegido para gestionar contenidos, señales de alerta, centros y servicios.
- El contenido sanitario permanece cerrado al público hasta tener revisión clínica documentada.
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

Aurora usa MySQL y distribuye su esquema maestro y scripts de migración:

- [Aurora_BD.sql](Aurora_BD.sql): crea la base de datos, tablas maestro, relaciones, roles, permisos e índices.
- [database/Aurora_MVP_seed.sql](database/Aurora_MVP_seed.sql): carga contenidos, señales y servicios iniciales.
- [database/migrations/20260925_preguntas_consulta.sql](database/migrations/20260925_preguntas_consulta.sql): agrega el hilo de preguntas a bases existentes.
- [database/migrations/20260926_plan_parto.sql](database/migrations/20260926_plan_parto.sql): tabla `planes_parto` para la logística de traslado y apoyo.
- [database/migrations/20260926_red_comunitaria.sql](database/migrations/20260926_red_comunitaria.sql): tabla `contactos_comunitarios` para los contactos personales de apoyo.

Desde CMD:

```cmd
mysql -u root -p < Aurora_BD.sql
mysql -u root -p aurora < database\Aurora_MVP_seed.sql
mysql -u root -p aurora < database\migrations\20260925_preguntas_consulta.sql
mysql -u root -p aurora < database\migrations\20260926_plan_parto.sql
mysql -u root -p aurora < database\migrations\20260926_red_comunitaria.sql
```

Desde PowerShell:

```powershell
Get-Content Aurora_BD.sql | mysql -u root -p
Get-Content database\Aurora_MVP_seed.sql | mysql -u root -p aurora
Get-Content database\migrations\20260925_preguntas_consulta.sql | mysql -u root -p aurora
Get-Content database\migrations\20260926_plan_parto.sql | mysql -u root -p aurora
Get-Content database\migrations\20260926_red_comunitaria.sql | mysql -u root -p aurora
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

Ejecuta la suite completa de pruebas desde la raíz del proyecto:

```powershell
python -m pytest -q
```

Para las pruebas de impresión PWA y eventos en JavaScript:

```powershell
node --test tests/test_print_sheet.cjs tests/test_pwa_install.cjs
node --check static/js/app.js
```

La suite de Python y las pruebas de JavaScript nativo cubren:

- Cálculo orientativo de semana gestacional.
- Plan de traslado, transporte y ficha familiar.
- Contactos personales de apoyo y aislamiento entre cuentas.
- Exclusión de rutas de seguimiento clínico fuera del alcance del MVP.
- Fichas imprimibles offline y disparador nativo de impresión.
- Protección del panel administrativo y roles de acceso.
- Registro, recuperación de contraseña y cabeceras HTTP de seguridad.

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
├── README.md                      # Guía de instalación, uso y despliegue
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
├── database/                      # Seed y migraciones incrementales
│   ├── Aurora_MVP_seed.sql         # Datos iniciales
│   └── migrations/                 # Cambios para bases existentes
├── requirements.txt               # Dependencias
└── run.bat                        # Arranque local o producción en Windows
```

## Roles

| Rol | Acceso |
| --- | --- |
| `usuario` | Perfil, embarazo, controles, preguntas, traslado y contactos personales de apoyo. |
| `administrador` | Panel de contenidos, señales, centros, servicios y auditoría reciente. |
| `auditor` | Definido en el esquema, pero sin interfaz funcional dedicada en el MVP. |

## PWA y disponibilidad sin conexión

El navegador registra el Service Worker desde [static/js/app.js](static/js/app.js). Se almacenan algunos recursos estáticos y una página general de contingencia. La disponibilidad sin conexión es parcial: perfil, embarazo, controles, preguntas, traslado, contactos y recordatorios requieren conexión y no se guardan en caché. La página de contingencia no muestra datos de la cuenta. Aurora no envía notificaciones en segundo plano; los recordatorios se consultan dentro de la aplicación.

Los centros de demostración provienen del listado oficial del MINSA (nombre, tipo y ubicación; consultado el 2026-10-06). Teléfonos, horarios, coordenadas y servicios no aparecen en la fuente y no se muestran. `seed-demo` solo se ejecuta con `AURORA_DEMO=1` y no registra fechas de verificación; confirma directamente con el establecimiento antes de acudir.

## Demo y revisión de contenido clínico

El contenido clínico no se publica: la guía y las señales permanecen deshabilitadas (fail-closed) hasta que exista un proceso de revisión clínica documentado. Para revisarlo con profesionales existe una vista separada, restringida al rol `administrador` y marcada como demo.

Los datos de demostración (cuatro perfiles ficticios y centros oficiales del MINSA) solo se cargan en una base de demo. `seed-demo` exige `AURORA_DEMO=1`; sin esa variable se cancela para no ensuciar la base real. El comando muestra contraseñas aleatorias; guárdalas y compártelas en privado, porque una nueva ejecución las cambia.

1. Activar el modo demo (solo en la base/entorno de demo):
   - PowerShell: `$env:AURORA_DEMO = "1"`
   - Linux/macOS: `export AURORA_DEMO=1`
2. Cargar cuatro cuentas ficticias y centros oficiales: `flask --app app seed-demo`
   - Railway (solo para este comando): `railway ssh -s web -- env AURORA_DEMO=1 flask --app app seed-demo`
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
- Revisión clínica responsable y fuentes concretas antes de publicar cualquier contenido de salud; validación local del directorio de centros.
- Definir si se incorporan nuevas funciones: solo entran si ayudan a recordar, preparar, coordinar o llevar información a una consulta sin interpretar datos clínicos.

## Licencia

Este repositorio no incluye actualmente un archivo de licencia. Define una licencia antes de distribuirlo públicamente.
