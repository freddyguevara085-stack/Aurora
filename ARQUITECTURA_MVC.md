# 🧩 Aurora explicada para principiantes
## Cómo queda organizado el código y para qué sirve cada parte

> Esta guía está escrita para que la entienda cualquier persona, aunque nunca haya
> programado. Si ya sabes programar, al final verás la tabla con los nombres
> técnicos reales y la estructura exacta del proyecto.

---

## 1. La idea en una sola frase

Una aplicación web es una máquina que:

1. **Recibe** un pedido (por ejemplo, "muéstrame mi calendario").
2. **Piensa** y busca la información necesaria.
3. **Devuelve** una página bonita con la respuesta.

Todo el truco de una buena arquitectura (como la **MVC**) es **separar esas tres tareas**
para que cada parte haga *una sola cosa* y sea fácil de entender, arreglar y ampliar.

---

## 2. La analogía del restaurante 🍽️

Imagina que Aurora es un **restaurante**. Cada vez que alguien entra, pasa esto:

| Persona | Rol en el restaurante | Qué hace | Su nombre técnico |
|---|---|---|---|
| 🧑‍🍳 **El cocinero** | Cocina los platos | Sabe *cómo* se prepara cada plato, mezcla ingredientes, sigue la receta | **Servicio / Lógica de negocio** |
| 🗄️ **La despensa** | Guarda los ingredientes | Donde están las materias primas (harina, tomate, queso) | **Modelo / Base de datos** |
| 🧾 **El mesero** | Atiende al cliente | Recibe el pedido, lo lleva a cocina, trae el plato terminado | **Controlador** |
| 🍽️ **El plato servido** | Lo que ve el cliente | La presentación final: el plato decorado y listo para comer | **Vista / Plantilla HTML** |
| 👮 **El portero** | Deja pasar solo a quien debe | Revisa si la persona puede entrar a cada zona | **Decoradores / Control de acceso** |

**La regla de oro:** el mesero (controlador) **no cocina**, y el cocinero (servicio)
**no atiende al cliente**. Cada uno hace lo suyo y se pasa la información de mano en mano.

---

## 3. El plano del código (carpetas reales)

Así queda organizada la casa de Aurora:

```
Aurora/
├── app.py                       # La fábrica: enciende la aplicación (create_app)
├── wsgi.py                      # La puerta de entrada para producción (Waitress)
├── config.py                    # Los ajustes según el entorno (desarrollo/pruebas/producción)
├── extensions.py                # Herramientas comunes: base de datos, login, CSRF
├── commands.py                  # Comandos que se ejecutan desde la terminal
├── demo_nicaragua.py            # 📚 Los datos oficiales del MINSA (centros, señales)
├── controllers/                 # 🧾 Los meseros (reciben pedidos y responden)
│   ├── blueprints.py            #    El "mostrador" común donde se registran las rutas
│   ├── decorators.py            # 👮 Los porteros (quién puede entrar a cada zona)
│   ├── auth.py                  #    Entrar, registrarse, recuperar contraseña
│   ├── gestante.py              #    Embarazo, controles, traslado, apoyo y perfil
│   ├── publicas.py              #    Inicio, guía, centros, alertas, información y PWA
│   └── admin/                   #    Panel de administración, un archivo por recurso
│       ├── dashboard.py
│       ├── contenidos.py
│       ├── senales.py
│       ├── centros.py
│       └── servicios.py
├── models/                      # 🗄️ Las mesas de la despensa (los datos y sus reglas)
├── services/                    # 🧑‍🍳 Los cocineros (la lógica del negocio)
│   ├── home.py                  #    Cálculos de la página de inicio (semana, trimestre)
│   ├── gestacion.py             #    Reglas de fechas, centros y red de apoyo
│   ├── mvp.py                   #    Consultas reutilizables del MVP
│   └── auditoria.py             #    Registrar acciones administrativas
├── templates/                   # 🍽️ Los platos servidos (páginas HTML)
├── static/                      # 🎨 La decoración: estilos, dibujos, fuentes, PWA
├── tests/                       # 🔍 Los inspectores (comprueban que todo funciona)
├── database/                    # 🏗️ Planos e instrucciones para la base de datos
├── Aurora_BD.sql                #    El plano principal de la base de datos
├── requirements.txt             # 🛒 La lista de compras (librerías necesarias)
├── README.md                    # 📖 El manual de instrucciones
└── ARQUITECTURA_MVC.md          # 📘 Esta explicación
```

No te asustes: **no necesitas memorizar todo**. Solo entiende que cada carpeta tiene
**una misión** y que las misiones no se mezclan.

---

## 4. Cada carpeta, explicada como para un bebé 👶

### 🧾 `controllers/` — Los meseros

**Qué son:** los que reciben el "hola, quiero ver mi embarazo" del navegador.

**Qué hacen (y solo esto):**
- Reciben la petición HTTP (la dirección que escribe el navegador).
- Llaman al servicio correcto para obtener la información.
- Deciden **a qué página** redirigir y **qué mensajes** mostrar ("Guardado con éxito").
- Responden con la plantilla HTML lista.

**Qué NO hacen:** no escriben consultas complicadas a la base de datos, no calculan
fechas, no validan formularios a mano. Por eso están **divididos en archivos pequeños**:

- `auth.py`: entrar, registrarse, recuperar contraseña.
- `gestante.py`: embarazo, controles, plan de parto, red de apoyo, preguntas y perfil.
- `publicas.py`: inicio, guía, centros, alertas, información y archivos de la PWA.
- `admin/`: el panel, un archivo por recurso (contenidos, señales, centros, servicios).

Todos se registran en el **mismo mostrador** (`blueprints.py`), así las direcciones
no cambian.

---

### 👮 `controllers/decorators.py` — Los porteros

**Qué hacen:** revisan quién puede entrar. Por ejemplo, `admin_required` deja pasar
solo a administradores, y `usuario_gestante` solo a usuarias gestantes.

**Por qué están aparte:** antes un controlador tenía que importar al otro; ahora la
regla de acceso vive en un solo lugar compartido.

---

### 🗄️ `models/` — La despensa (los datos)

**Qué son:** la descripción de **cada "tabla"** donde se guarda la información.

**Qué hacen:**
- Definen qué datos existen (un `Usuario` tiene nombre, correo, contraseña).
- Definen las **relaciones** ("un embarazo pertenece a un perfil de gestante").
- Definen las **reglas de integridad** ("el correo debe ser único").

**Qué NO hacen:** no pintan HTML, no calculan semanas, no hablan con el navegador.

**Analogía:** la despensa tiene estantes etiquetados. El modelo es la **etiqueta** de
cada estante.

---

### 🧑‍🍳 `services/` — Los cocineros (la lógica de negocio)

**Qué son:** el lugar donde vive **el "cómo se hace"** de la aplicación.

**Qué hacen:**
- Las operaciones que se repiten y tienen reglas propias.
- Por ejemplo: calcular la semana de embarazo, validar fechas, ordenar centros de salud
  o armar el resumen del inicio.

**Qué NO hacen:** no reciben peticiones HTTP directamente, no pintan HTML.

**Ejemplo real:** `services/gestacion.py` guarda las reglas de fechas y de la red de
apoyo; `services/home.py` calcula la semana gestacional.

---

### 🍽️ `templates/` + `static/` — La Vista (lo que se ve)

- **`templates/`** son las **plantillas HTML** (el plato servido). Son "moldes" que se
  rellenan con datos: `Hola, {{ nombre }}`.
- **`static/`** es la **decoración fija**: CSS, animaciones (JS), fuentes, íconos y PWA.

**Regla de oro:** la Vista **solo muestra**. No consulta la base de datos ni calcula
nada importante.

---

### 🔍 `tests/` — Los inspectores de calidad

**Qué hacen:** ejecutan la aplicación por dentro y comprueban que todo sigue
funcionando después de cada cambio. `tests/test_arquitectura.py` vigila que la fábrica
y las rutas sigan completas.

**Analogía:** un inspector prueba cada plato antes de servirlo.

---

### 🏗️ `database/` y `Aurora_BD.sql` — El plano de la despensa

**Qué son:** las instrucciones para **crear** la base de datos (tablas y reglas).

**Regla de oro:** en la reorganización **no se borra ni se reinicia** la base de datos.
Los datos se conservan tal cual.

---

## 5. El viaje de una petición (paso a paso) 🚶

Sigamos una visita real: la usuaria entra a **"Mi embarazo"**.

```
1. El navegador pide:  /embarazo
        │
        ▼
2. 🧾 CONTROLADOR (controllers/gestante.py)
   "Alguien quiere ver su embarazo."
   → el portero verifica que está conectada (login).
        │
        ▼
3. 🧑‍🍳 SERVICIO (services/home.py y services/mvp.py)
   "Necesito el perfil, el embarazo activo y la semana."
   → aplica las reglas de cálculo.
        │
        ▼
4. 🗄️ MODELO (models/gestacion.py)
   "Voy a la despensa a buscar los datos."
   → consulta la base de datos (MySQL).
        │
        ▼
5. 🧑‍🍳 El SERVICIO arma la respuesta ya calculada.
        │
        ▼
6. 🧾 El CONTROLADOR recibe los datos listos.
        │
        ▼
7. 🍽️ La VISTA (templates/embarazo.html + static/)
   pinta la página bonita con esos datos.
        │
        ▼
8. El navegador muestra la página a la usuaria. ✅
```

**Lo importante:** la información viaja **en una sola dirección lógica**:
`Navegador → Controlador → Servicio → Modelo → Servicio → Controlador → Vista → Navegador`.
Nadie se salta al vecino.

---

## 6. Vocabulario clave (resumen técnico)

| Término | Qué es en Aurora | Dónde vive |
|---|---|---|
| **Modelo (M)** | Las entidades y los datos (tablas) | `models/` |
| **Vista (V)** | Lo que se muestra (HTML + CSS + JS) | `templates/` + `static/` |
| **Controlador (C)** | Recibe la petición y coordina | `controllers/` |
| **Servicio** | La lógica de negocio reutilizable | `services/` |
| **Decorador** | Control de acceso por rol | `controllers/decorators.py` |
| **Blueprint** | El "mostrador" que agrupa rutas | `controllers/blueprints.py` |
| **Extensión** | Conexión con librerías (BD, login, CSRF) | `extensions.py` |
| **Configuración** | Ajustes y secretos por entorno | `config.py` + `.env` |
| **Fábrica** | Crea la aplicación al arrancar | `app.py` (`create_app`) |

> Nota sobre **Repositorios**: no se añadieron. En Flask, el ORM (Flask-SQLAlchemy)
> ya hace el acceso a datos; una capa extra solo duplicaría trabajo. La validación y
> las reglas sí se movieron a `services/`.

---

## 7. Reglas de oro 🏆

1. **Cada módulo hace una sola cosa.** Si un archivo hace de todo, se divide.
2. **La Vista no piensa.** Solo muestra lo que ya está calculado.
3. **El Controlador no cocina.** Coordina, no calcula ni consulta a lo bruto.
4. **El Servicio guarda las recetas.** La lógica de negocio vive ahí, una sola vez.
5. **El Modelo es la despensa.** Los datos y sus reglas de integridad.
6. **Los porteros son compartidos.** El control de acceso no se copia en cada archivo.
7. **Nada se borra ni se inventa.** Se conserva el comportamiento actual y los mensajes.
8. **Todo cambio se prueba.** Los inspectores (`tests/`) confirman que nada se rompió.

---

## 8. En una frase final

> **Modelos** guardan los datos, **Servicios** aplican las reglas, **Controladores**
> coordinan las peticiones y **Vistas** muestran el resultado. Separar estas piezas hace
> que el proyecto sea más fácil de entender, mantener y ampliar, sin perder ninguna de
> las funciones que ya existían.
