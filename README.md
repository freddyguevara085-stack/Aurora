<div align="center">
  <img src="static/images/aurora-logo.png" alt="Logo de Aurora" width="260">
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
- [Despliegue en Azure Virtual Machine](#despliegue-en-azure-virtual-machine)
- [Estructura](#estructura)
- [Roles](#roles)
- [PWA y disponibilidad sin conexión](#pwa-y-disponibilidad-sin-conexión)
- [Contenido de salud y directorio](#contenido-de-salud-y-directorio)
- [Seguridad](#seguridad)
- [Limitaciones y próximos pasos](#limitaciones-y-próximos-pasos)

## Alcance del producto

- **Qué es:** un puente organizativo entre la vida diaria de una gestante y su atención prenatal.
- **Qué ofrece:** etapa orientativa del embarazo, agenda de controles, preguntas para la consulta, plan de traslado y apoyo, contactos personales y fichas imprimibles.
- **Qué no ofrece:** diagnóstico, interpretación de síntomas, tratamientos, protocolos clínicos ni sustitución de la atención profesional.

El seguimiento individual de puerperio, lactancia y recién nacido sigue fuera de los módulos de la aplicación.

## Qué incluye

Aurora está diseñada como un **medio sencillo de organización** entre la gestante, su familia y la atención profesional. Su alcance se limita a tareas prácticas que la usuaria puede preparar sin convertir la aplicación en un servicio médico.

### 1. Embarazo y controles
- Registro y seguimiento del embarazo activo con cálculo orientativo de semana gestacional, trimestre y FPP.
- Registro y corrección de la fecha real del nacimiento, conservando por separado la FPP como estimación.
- Registro, reprogramación y consulta de controles prenatales (programados, realizados, reprogramados).
- **Preguntas para la consulta:** dudas anotadas por la gestante para conversar con el personal de salud.
- Hoja imprimible de preparación de la cita (`/consulta/imprimir`).

### 2. Traslado y apoyo familiar
- **Plan de traslado y apoyo (`/plan-parto`):** lugar previsto, acompañante, persona a cargo del hogar, transporte y preparativos básicos.
- **Contactos personales (`/red-comunitaria`):** familiares, personas de confianza y transporte confirmados por la usuaria, con enlace de llamada `tel:`.
- **Ficha familiar (`/plan-parto/imprimir`):** hoja compacta con la logística y los contactos registrados.

### 3. Para administración
- Panel protegido para gestionar contenidos, señales de alerta, centros y servicios.
- Las orientaciones marcadas como **publicadas** y las señales marcadas como **activas** se muestran en la guía y en las alertas. Cada registro exige fuente y fecha de revisión.
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
| Waitress | Servidor WSGI para la aplicación |
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

- [Aurora_BD.sql](Aurora_BD.sql): crea la base de datos e incluye el esquema actual completo (todas las tablas, relaciones, roles, permisos e índices) para instalaciones nuevas.
- [database/Aurora_MVP_seed.sql](database/Aurora_MVP_seed.sql): carga contenidos, señales y servicios iniciales.
- `database/migrations/`: scripts incrementales exclusivos para actualizar bases de datos creadas con versiones anteriores del esquema:
  - [database/migrations/20260925_preguntas_consulta.sql](database/migrations/20260925_preguntas_consulta.sql): agrega el hilo de preguntas a bases existentes.
  - [database/migrations/20260926_plan_parto.sql](database/migrations/20260926_plan_parto.sql): tabla `planes_parto` para la logística de traslado y apoyo.
  - [database/migrations/20260926_red_comunitaria.sql](database/migrations/20260926_red_comunitaria.sql): tabla `contactos_comunitarios` para los contactos personales de apoyo.
  - [database/migrations/20261008_seguimiento_nacimiento.sql](database/migrations/20261008_seguimiento_nacimiento.sql): agrega la fecha real del nacimiento al seguimiento del embarazo.

Para una **instalación nueva** desde CMD (no requiere ejecutar `database/migrations/`):

```cmd
mysql -u root -p < Aurora_BD.sql
mysql -u root -p aurora < database\Aurora_MVP_seed.sql
```

Desde PowerShell:

```powershell
Get-Content Aurora_BD.sql | mysql -u root -p
Get-Content database\Aurora_MVP_seed.sql | mysql -u root -p aurora
```

Si estás actualizando una **base de datos existente** de una versión previa, aplica únicamente las migraciones de `database/migrations/` que aún no se hayan ejecutado.

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

Instala las dependencias de desarrollo antes de ejecutar las pruebas:

```powershell
python -m pip install -r requirements-dev.txt
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
- Fábrica de aplicación (`create_app`) y registro de rutas (`tests/test_arquitectura.py`).

## Despliegue en Azure Virtual Machine

Aurora se despliega en una máquina virtual Ubuntu de Azure.
La arquitectura es:

```text
Teléfono o navegador ── HTTPS :443 ──> Nginx ──> Aurora / Waitress :8000 ──> MySQL local
```

La base de datos permanece dentro de la VM; no se abre su puerto a Internet.
Configura un dominio propio para el entorno y no publiques direcciones IP de la
infraestructura en este repositorio.

### 1. Crear y preparar la VM

1. En Azure Portal crea una **Virtual Machine** con Ubuntu LTS y un usuario
   administrador, por ejemplo `adminaurora`.
2. En el grupo de seguridad de red (NSG) habilita las reglas entrantes:
   - `22/TCP` para SSH, idealmente limitado a tu IP.
   - `80/TCP` para HTTP y validación de certificados.
   - `443/TCP` para HTTPS.
3. Descarga la clave SSH y conéctate desde Windows:

   ```powershell
   ssh -i "C:\ruta\a\aurora_key.pem" adminaurora@IP_PUBLICA
   ```

   Si OpenSSH indica que la clave tiene permisos demasiado abiertos, limita sus
   permisos en Windows antes de conectar. Nunca subas el archivo `.pem` al
   repositorio.
4. Ya dentro de la VM instala las dependencias del sistema:

   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-venv python3-pip mysql-server nginx git certbot python3-certbot-nginx
   ```

### 2. Descargar Aurora e instalar sus dependencias

```bash
cd ~
git clone https://github.com/freddyguevara085-stack/Aurora.git
cd Aurora
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Crear la base de datos y aplicar el esquema

Usa MySQL local solo desde la VM. El siguiente ejemplo crea un usuario limitado
para Aurora; reemplaza `CONTRASENA_SEGURA` por un secreto propio:

```bash
sudo mysql
```

```sql
CREATE DATABASE aurora CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'aurora_app'@'localhost' IDENTIFIED BY 'CONTRASENA_SEGURA';
GRANT ALL PRIVILEGES ON aurora.* TO 'aurora_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Inicializa una base nueva (`Aurora_BD.sql` ya incluye el esquema completo actual):

```bash
sudo mysql < Aurora_BD.sql
sudo mysql aurora < database/Aurora_MVP_seed.sql
```

En una base que ya existe de una versión anterior, aplica únicamente las migraciones de `database/migrations/` aún no ejecutadas.
Por ejemplo, la columna de fecha real de nacimiento se puede comprobar con:

```bash
sudo mysql aurora -e "SHOW COLUMNS FROM embarazos LIKE 'fecha_nacimiento_real';"
```

### 4. Configurar secretos y ejecutar Aurora como servicio

Crea `/home/adminaurora/Aurora/.env` con permisos privados. No lo añadas a Git:

```dotenv
SECRET_KEY=una-clave-larga-generada-aleatoriamente
AURORA_ENV=production
AURORA_DEBUG=0
SESSION_COOKIE_SECURE=1
PORT=8000
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=aurora
MYSQL_USER=aurora_app
MYSQL_PASSWORD=CONTRASENA_SEGURA
```

```bash
chmod 600 .env
```

Crea el servicio `/etc/systemd/system/aurora.service`:

```ini
[Unit]
Description=Aurora Flask application
After=network.target mysql.service

[Service]
User=adminaurora
WorkingDirectory=/home/adminaurora/Aurora
EnvironmentFile=/home/adminaurora/Aurora/.env
ExecStart=/home/adminaurora/Aurora/.venv/bin/python /home/adminaurora/Aurora/wsgi.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Actívalo y verifica su estado:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aurora
sudo systemctl status aurora
```

El estado esperado es `active (running)`.

### 5. Publicar con Nginx, firewall y HTTPS

Crea `/etc/nginx/sites-available/aurora` y sustituye `DOMINIO_PUBLICO` por tu
dominio o por el host `sslip.io` de tu IP:

```nginx
server {
    listen 80;
    server_name DOMINIO_PUBLICO;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/aurora /etc/nginx/sites-enabled/aurora
sudo nginx -t
sudo systemctl reload nginx
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
sudo certbot --nginx -d DOMINIO_PUBLICO
```

Verifica el despliegue desde la VM o desde tu equipo:

```bash
curl -I https://DOMINIO_PUBLICO
sudo systemctl status aurora
sudo ufw status
```

### 6. Crear la cuenta administrativa inicial

Desde `~/Aurora` crea la cuenta administrativa inicial:

```bash
source .venv/bin/activate
flask --app app create-user
```

Elige el id `2` (`administrador`) cuando el comando pregunte el rol. La
contraseña se solicita de forma oculta; no se escribe en el historial ni en el
repositorio. No se incluyen usuarios ni datos ficticios en la instalación.

### 7. Actualizar Azure después de cambios locales

En tu computadora, desde la raíz del repositorio:

```powershell
git add .
git commit -m "Describe el cambio"
git push origin main
```

Después conéctate a la VM y actualiza el código:

```bash
cd ~/Aurora
git pull --ff-only origin main
# Ejecuta aquí cada migración nueva que acompañe el cambio.
sudo systemctl restart aurora
sudo systemctl status aurora
```

Nginx no necesita reiniciarse cuando cambian solo Python, HTML, CSS o archivos
estáticos. Usa `sudo nginx -t && sudo systemctl reload nginx` únicamente si
cambiaste su configuración.

## Estructura

Aurora sigue una organización **MVC** adaptada a Flask:

- **Modelo (`models/`)** — entidades SQLAlchemy y reglas de integridad.
- **Vista (`templates/` + `static/`)** — plantillas Jinja2, estilos, JavaScript y PWA.
- **Controlador (`controllers/`)** — recibe la petición, valida y coordina; no concentra la lógica de negocio.
- **Servicios (`services/`)** — reglas de negocio reutilizables (cálculos de gestación, consultas, catálogo MINSA, semillas, auditoría).
- **Decoradores (`controllers/decorators.py`)** — control de acceso por rol compartido.

```text
Aurora/
├── app.py                         # Fábrica create_app() y arranque de desarrollo
├── wsgi.py                        # Entrada WSGI con Waitress (producción)
├── config.py                      # Config por entorno (development/testing/production)
├── extensions.py                  # Base de datos, login y CSRF
├── commands.py                    # Comandos CLI de Flask
├── README.md                      # Guía de instalación, uso y despliegue
├── controllers/
│   ├── blueprints.py              # Blueprint principal compartido
│   ├── decorators.py              # admin_required, usuario_gestante y helpers de rol
│   ├── auth.py                    # Login, registro y recuperación
│   ├── publicas.py                # Inicio, guía, centros, alertas, información y PWA
│   ├── gestante/                  # Flujos de la gestante por dominio
│   │   ├── embarazo.py
│   │   ├── controles.py
│   │   ├── plan_parto.py
│   │   ├── red_comunitaria.py
│   │   ├── preguntas.py
│   │   ├── calendario.py
│   │   └── perfil.py
│   └── admin/                     # Panel administrativo por recurso
│       ├── _common.py
│       ├── dashboard.py
│       ├── contenidos.py
│       ├── senales.py
│       ├── centros.py
│       └── servicios.py
├── models/                        # Modelos SQLAlchemy
├── services/                      # Lógica de negocio (admin, auditoria, auth, catalogo_minsa, gestacion, home, mvp, seed)
├── templates/                     # Vistas Jinja2
├── static/                        # CSS, JavaScript, fuentes, íconos, imágenes y PWA
├── tests/                         # Suite modular de pruebas (pytest y node --test)
│   ├── conftest.py
│   ├── test_admin.py
│   ├── test_arquitectura.py
│   ├── test_auth.py
│   ├── test_gestante.py
│   ├── test_publicas.py
│   ├── test_services.py
│   ├── test_smoke_rutas.py
│   ├── test_print_sheet.cjs
│   └── test_pwa_install.cjs
├── Aurora_BD.sql                  # Esquema completo MySQL para instalaciones nuevas
├── database/                      # Seeds y migraciones incrementales
│   ├── Aurora_MVP_seed.sql        # Datos iniciales SQL
│   ├── seeds/                     # Catálogos JSON de centros y fuentes MINSA
│   └── migrations/                # Actualizaciones incrementales para bases anteriores
├── requirements.txt               # Dependencias
├── requirements-dev.txt           # Dependencias de pruebas y desarrollo
└── run.bat                        # Arranque local en Windows
```

La configuración se selecciona con `AURORA_ENV` (`development`, `testing` o
`production`). Cada controlador importa solo lo que necesita y la lógica
compartida vive en `services/`, evitando dependencias entre controladores.

## Roles

| Rol | Acceso |
| --- | --- |
| `usuario` | Perfil, embarazo, controles, preguntas, traslado y contactos personales de apoyo. |
| `administrador` | Panel de contenidos, señales, centros, servicios y auditoría reciente. Puede publicar orientaciones y activar señales visibles para las gestantes. |
| `auditor` | Definido en el esquema, pero sin interfaz funcional dedicada en el MVP. |

## PWA y disponibilidad sin conexión

El navegador registra el Service Worker desde [static/js/app.js](static/js/app.js). Se almacenan algunos recursos estáticos y una página general de contingencia. La disponibilidad sin conexión es parcial: perfil, embarazo, controles, preguntas, traslado, contactos y recordatorios requieren conexión y no se guardan en caché. La página de contingencia no muestra datos de la cuenta. Aurora no envía notificaciones en segundo plano; los recordatorios se consultan dentro de la aplicación.

El directorio replica el listado oficial de la Red de Salud del MINSA (consultado el 2026-10-06): 438 establecimientos entre hospitales (con su subtipo: primario, departamental, regional o de referencia nacional), casas maternas, centros de salud y Clínicas Médicas Previsionales, cubriendo los 15 departamentos y 2 regiones autónomas de toda Nicaragua (153 municipios), con SILAIS, departamento, municipio, localidad y zona urbano/rural tal como los publica la fuente. Teléfonos, horarios, coordenadas y servicios no aparecen en el listado y no se importan. Las CMP son previsionales y aplican según convenios con el INSS: confirma elegibilidad y disponibilidad directamente con MINSA. La fecha de consulta no equivale a una verificación del establecimiento.

Para poblar o actualizar el directorio en la base de datos de Azure, conéctate
por SSH a la VM y ejecuta el comando desde la carpeta del proyecto. `seed-centros`
solo sincroniza los establecimientos del MINSA; no crea cuentas ficticias:

```bash
cd ~/Aurora
source .venv/bin/activate
flask --app app seed-centros
sudo systemctl restart aurora
```

Comprueba el resultado en el directorio público de Aurora. No ejecutes el comando
desde `~`: Git y Flask necesitan estar dentro de `~/Aurora`.

## Contenido de salud y directorio

La instalación no publica contenido clínico ni carga cuentas ficticias. La guía
y las señales de alerta solo muestran registros que administración haya
publicado o activado; cada registro debe contar con una fuente y una fecha de
revisión. No publiques orientaciones hasta completar una revisión profesional
responsable. El directorio MINSA tampoco confirma teléfonos, horarios ni
servicios: valida esos datos directamente con cada establecimiento.

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

## Presentación en Railway

El archivo `railway.toml` prepara la base y arranca `python wsgi.py` con Waitress,
utilizando el `PORT` asignado por Railway. `/health` comprueba también MySQL.

En las variables del servicio web configura:

- `AURORA_ENV=production`
- `SECRET_KEY`: una clave aleatoria privada y estable.
- `SESSION_COOKIE_SECURE=1` para el dominio HTTPS.
- `MYSQL_URL=${{MySQL.MYSQL_URL}}`, ajustando `MySQL` al nombre del servicio de base de datos.

También se admiten las variables individuales de Railway (`MYSQLHOST`,
`MYSQLPORT`, `MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD`) o las variables locales
con guiones bajos. No se necesita importar un SQL que fuerce el nombre `aurora`:
`prepare-deploy` crea las tablas faltantes en la base seleccionada, agrega la
columna de nacimiento si falta y carga el directorio si está vacío. Conserva
las cuentas y registros existentes. No publica contenidos clínicos de ejemplo.

### Cuenta ficticia de presentación

```bash
python -m flask --app app create-demo
```

El comando solicita una contraseña de al menos 12 caracteres sin mostrarla.
Crea `maria.demo@example.com`, con perfil de María, embarazo de 24 semanas,
tres controles anteriores, una próxima cita, preguntas, recordatorio y plan de
traslado. Todos los datos personales son ficticios; se omiten cédulas y teléfonos
para evitar que correspondan a alguien real. Repetirlo no duplica ni cambia una
cuenta existente. Las fechas se calculan al crear la cuenta, en hora de Managua.

Para crearlo automáticamente en una **base de demostración** de Railway, define
`AURORA_DEMO_PASSWORD` en sus variables privadas antes de desplegar. Si la cuenta
ya existe, no se modifica ni se cambia su contraseña. Retira esa variable después
de la presentación. Las contraseñas y bases locales no se incluyen en Git.
