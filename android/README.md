# APK de Aurora

Este módulo contiene una envoltura Android para la aplicación Flask existente.
El backend, las sesiones y MySQL continúan ejecutándose en un servidor HTTPS.

## Configuración

1. Publica Aurora detrás de HTTPS (por ejemplo, `https://aurora.tudominio.com`).
2. Abre `app/src/main/res/values/strings.xml`.
3. Cambia `server_url` por la URL pública, incluyendo la barra final.
4. Abre la carpeta `android` desde Android Studio.
5. Espera la sincronización de Gradle y ejecuta **Build > Build APK(s)**.

El APK no debe apuntar a `127.0.0.1`, `localhost` ni a una URL HTTP. En un
teléfono, `localhost` apunta al propio teléfono y no al servidor de desarrollo.

## Prueba en un teléfono

Activa las opciones de desarrollador y la depuración USB, conecta el teléfono
y usa **Run** en Android Studio. Para distribuir el APK, configura además una
firma de lanzamiento desde **Build > Generate Signed Bundle / APK**.

La aplicación web ya incluye manifest y service worker; esta envoltura conserva
la navegación, autenticación y soporte offline que pueda ofrecer el servidor.
