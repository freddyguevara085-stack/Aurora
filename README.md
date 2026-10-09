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
- [Despliegue en Azure Virtual Machine](#despliegue-en-azure-virtual-machine)
- [Estructura](#estructura)
- [Roles](#roles)
- [PWA y disponibilidad sin conexión](#pwa-y-disponibilidad-sin-conexión)
- [APK para Android](#apk-para-android)
- [Seguridad](#seguridad)
- [Limitaciones y próximos pasos](#limitaciones-y-próximos-pasos)

## Alcance del producto

- **Qué es:** un puente organizativo entre la vida diaria de una gestante y su atención prenatal.
- **Qué ofrece:** etapa orientativa del embarazo, agenda de controles, preguntas para la consulta, plan de traslado y apoyo, contactos personales y fichas imprimibles.
- **Qué no ofrece:** diagnóstico, interpretación de síntomas, tratamientos, protocolos clínicos ni sustitución de la atención profesional.

El seguimiento individual de puerperio, lactancia y recién nacido sigue fuera de los módulos de la aplicación. Para las cuatro cuentas ficticias, la guía de demostración muestra un panorama general desde la atención prenatal hasta el seguimiento postnatal, basado únicamente en materiales oficiales MINSA de 2020–2022 y marcado como pendiente de revisión clínica; no contiene pautas personalizadas.

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
- [database/migrations/20261008_seguimiento_nacimiento.sql](database/migrations/20261008_seguimiento_nacimiento.sql): agrega la fecha real del nacimiento al seguimiento del embarazo.

Desde CMD:

```cmd
mysql -u root -p < Aurora_BD.sql
mysql -u root -p aurora < database\Aurora_MVP_seed.sql
mysql -u root -p aurora < database\migrations\20260925_preguntas_consulta.sql
mysql -u root -p aurora < database\migrations\20260926_plan_parto.sql
mysql -u root -p aurora < database\migrations\20260926_red_comunitaria.sql
mysql -u root -p aurora < database\migrations\20261008_seguimiento_nacimiento.sql
```

Desde PowerShell:

```powershell
Get-Content Aurora_BD.sql | mysql -u root -p
Get-Content database\Aurora_MVP_seed.sql | mysql -u root -p aurora
Get-Content database\migrations\20260925_preguntas_consulta.sql | mysql -u root -p aurora
Get-Content database\migrations\20260926_plan_parto.sql | mysql -u root -p aurora
Get-Content database\migrations\20260926_red_comunitaria.sql | mysql -u root -p aurora
Get-Content database\migrations\20261008_seguimiento_nacimiento.sql | mysql -u root -p aurora
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
- Fábrica de aplicación (`create_app`) y registro de rutas (`tests/test_arquitectura.py`).

## Despliegue en Azure Virtual Machine

La demostración de Aurora se despliega en una máquina virtual Ubuntu de Azure.
La arquitectura es:

```text
Teléfono o navegador ── HTTPS :443 ──> Nginx ──> Aurora / Waitress :8000 ──> MySQL local
```

La base de datos permanece dentro de la VM; no se abre su puerto a Internet.
La URL pública de demostración actual es
[`https://158-158-0-166.sslip.io`](https://158-158-0-166.sslip.io). El dominio
`sslip.io` resuelve hacia la IP pública de la VM; en un despliegue permanente se
recomienda usar un dominio propio.

### 1. Crear y preparar la VM

1. En Azure Portal crea una **Virtual Machine** con Ubuntu LTS y un usuario
   administrador, por ejemplo `adminaurora`.
2. En el grupo de seguridad de red (NSG) habilita las reglas entrantes:
   - `22/TCP` para SSH, idealmente limitado a tu IP.
   - `80/TCP` para HTTP y validación de certificados.
   - `443/TCP` para HTTPS.
3. Descarga la clave SSH y conéctate desde Windows:

   ```powershell
   ssh -i "C:\ruta\a\hackton_key.pem" adminaurora@IP_PUBLICA
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

Inicializa una base nueva y aplica todas las migraciones:

```bash
sudo mysql < Aurora_BD.sql
sudo mysql aurora < database/Aurora_MVP_seed.sql
sudo mysql aurora < database/migrations/20260925_preguntas_consulta.sql
sudo mysql aurora < database/migrations/20260926_plan_parto.sql
sudo mysql aurora < database/migrations/20260926_red_comunitaria.sql
sudo mysql aurora < database/migrations/20261008_seguimiento_nacimiento.sql
```

En una base que ya existe, aplica solamente las migraciones aún no ejecutadas.
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

### 6. Crear cuentas administrativas de demostración

Desde `~/Aurora` ejecuta una vez por cada cuenta:

```bash
source .venv/bin/activate
flask --app app create-user
```

Elige el id `2` (`administrador`) cuando el comando pregunte el rol. La
contraseña se solicita de forma oculta; no se escribe en el historial ni en el
repositorio.

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

### Alternativa: ejecución directa en Windows

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

### Alternativa: despliegue en Microsoft Azure App Service

Aurora queda preparada para App Service sin cambiar su código. Pasos recomendados
(verifícalos primero en local; este repositorio no crea recursos de Azure):

1. **Runtime:** App Service con Python 3.10–3.12 (Linux o Windows).
2. **Comando de inicio:** en Linux usa un servidor WSGI, por ejemplo
   `gunicorn --bind=0.0.0.0:8000 wsgi:app`; en Windows usa `python wsgi.py`
   (Waitress, ya incluido en `requirements.txt`).
3. **Variables de entorno** (Configuración → Variables de aplicación):
   `SECRET_KEY`, `AURORA_ENV=production`, `AURORA_DEBUG=0`,
   `SESSION_COOKIE_SECURE=1`, `PORT=8000` y las credenciales `MYSQL_*` del
   servidor de Azure Database for MySQL. No subas nunca el archivo `.env`.
4. **Base de datos:** Azure Database for MySQL; aplica `Aurora_BD.sql` y las
   migraciones `database/migrations/*.sql`. La app no crea ni inicializa el
   esquema por sí sola.
5. **HTTPS:** actívalo en App Service; `SESSION_COOKIE_SECURE=1` añade HSTS.
6. **Diagnóstico:** App Service recoge `stdout`/`stderr`; los errores 500 se
   registran con `app.logger.exception` sin exponer datos sensibles al usuario.

> `gunicorn` no se ejecuta en Windows; para desarrollo y producción en Windows
> se mantiene Waitress (`wsgi.py`).

## Estructura

Aurora sigue una organización **MVC** adaptada a Flask:

- **Modelo (`models/`)** — entidades SQLAlchemy y reglas de integridad.
- **Vista (`templates/` + `static/`)** — plantillas Jinja2, estilos, JavaScript y PWA.
- **Controlador (`controllers/`)** — recibe la petición, valida y coordina; no concentra la lógica de negocio.
- **Servicios (`services/`)** — reglas de negocio reutilizables (cálculos de gestación, consultas, auditoría).
- **Decoradores (`controllers/decorators.py`)** — control de acceso por rol compartido.

```text
Aurora/
├── app.py                         # Fábrica create_app() y arranque de desarrollo
├── wsgi.py                        # Entrada WSGI con Waitress (producción)
├── config.py                      # Config por entorno (development/testing/production)
├── extensions.py                  # Base de datos, login y CSRF
├── commands.py                    # Comandos CLI de Flask
├── README.md                      # Guía de instalación, uso y despliegue
├── ARQUITECTURA_MVC.md            # Explicación didáctica de la arquitectura
├── controllers/
│   ├── blueprints.py              # Blueprint principal compartido
│   ├── decorators.py              # admin_required y helpers de rol
│   ├── auth.py                    # Login, registro y recuperación
│   ├── gestante.py                # Flujos de la gestante (embarazo, controles, apoyo, perfil)
│   ├── publicas.py                # Inicio, guía, centros, alertas, información y PWA
│   └── admin/                     # Panel administrativo por recurso
│       ├── dashboard.py
│       ├── contenidos.py
│       ├── senales.py
│       ├── centros.py
│       └── servicios.py
├── models/                        # Modelos SQLAlchemy
├── services/                      # Lógica de negocio (home, mvp, gestacion, auditoria)
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

## APK para Android

El proyecto incluye una envoltura Android en [`android/`](android/). Esta versión
mantiene Flask, las sesiones y MySQL en un servidor HTTPS y abre Aurora dentro
de una aplicación móvil. Antes de compilar, cambia `server_url` en
[`android/app/src/main/res/values/strings.xml`](android/app/src/main/res/values/strings.xml)
por el dominio público de producción. Después abre `android/` en Android Studio
y usa **Build > Build APK(s)**. El resultado se genera normalmente en
`android/app/build/outputs/apk/debug/app-debug.apk`. No uses `localhost`, `127.0.0.1` ni HTTP: desde
el teléfono esas direcciones no apuntan al servidor y el módulo bloquea tráfico
sin cifrado.

Para el entregable de descarga, la APK publicada se almacena como
[`static/downloads/Aurora.apk`](static/downloads/Aurora.apk). La landing pública
incluye el botón de descarga y Aurora la entrega desde:

```text
https://DOMINIO_PUBLICO/descargar/aurora.apk
```

Cada vez que cambies `server_url` o el proyecto Android, genera una APK nueva,
reemplaza `static/downloads/Aurora.apk`, realiza `git commit` y aplica el
proceso de actualización de Azure descrito arriba.

El directorio de demostración replica el listado oficial de la Red de Salud del MINSA (consultado el 2026-10-06): 438 establecimientos entre hospitales (con su subtipo: primario, departamental, regional o de referencia nacional), casas maternas, centros de salud y Clínicas Médicas Previsionales, cubriendo los 15 departamentos y 2 regiones autónomas de toda Nicaragua (153 municipios), con SILAIS, departamento, municipio, localidad y zona urbano/rural tal como los publica la fuente. Teléfonos, horarios, coordenadas y servicios no aparecen en el listado y no se importan. Las CMP son previsionales y aplican según convenios con el INSS: confirma elegibilidad y disponibilidad directamente con MINSA. La fecha de consulta no equivale a una verificación del establecimiento.

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

## Demo y revisión de contenido clínico

Para facilitar la revisión manual por parte de profesionales de salud en esta versión de prueba, la guía incluye 24 orientaciones detalladas que abarcan tanto el calendario prenatal como la resolución de dudas sobre las señales de alerta y emergencias obstétricas (sangrado vaginal, dolor de cabeza intenso con visión borrosa/zumbidos por preeclampsia, salida de líquido amniótico, disminución de movimientos fetales, fiebre e infecciones, contracciones prematuras, hinchazón súbita, dolor epigástrico y convulsiones), así como el rol del plan de parto y las Casas Maternas ante un traslado urgente.

En modo de demostración (`AURORA_DEMO=1`), las cuentas de prueba y administradores pueden consultar los datos ficticios de la guía y el panel de revisión clínica en `/demo/revision-clinica`. En producción, `/guia` muestra las orientaciones que administración publicó y `/alertas` muestra las señales que administración activó.

Los datos de demostración (cuatro perfiles ficticios, centros oficiales del MINSA
y catálogo de alertas) se cargan con `seed-demo`. Esta operación requiere
`AURORA_DEMO=1` y debe ejecutarse únicamente en una base de demostración separada;
no la ejecutes en la base de producción de Azure porque crea o restablece cuentas
y datos ficticios.

1. Activar el modo demo (solo en la base/entorno de demo):
   - PowerShell: `$env:AURORA_DEMO = "1"`
   - Linux/macOS: `export AURORA_DEMO=1`
2. En el entorno de demostración, cargar perfiles ficticios, agenda y centros:
   `flask --app app seed-demo`. En la VM de Azure, primero entra a `~/Aurora`,
   activa `.venv` y configura `AURORA_DEMO=1` en el entorno de demostración antes
   de ejecutar el comando. Para actualizar únicamente los centros en Azure usa
   `flask --app app seed-centros`, descrito arriba.
3. Crear una cuenta revisora con rol `administrador`; la contraseña se pide de forma interactiva y no queda escrita en el código:
   `flask --app app create-user` → elegir el id del rol `administrador`.
4. Iniciar la aplicación: `python app.py`
5. Ingresar en `http://localhost:5000/login` con la cuenta revisora o de prueba y abrir `/guia`, `/alertas` o `/demo/revision-clinica`.

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
