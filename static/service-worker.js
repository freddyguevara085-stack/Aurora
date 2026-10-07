const CACHE_NAME = 'aurora-shell-v24';
const APP_SHELL = [
  '/manifest.json',
  '/offline.html',
  '/static/css/tokens.css',
  '/static/css/base.css',
  '/static/css/components.css',
  '/static/css/pages.css',
  '/static/css/print.css',
  '/static/js/app.js',
  '/static/fonts/poppins/poppins-400.woff2',
  '/static/fonts/poppins/poppins-500.woff2',
  '/static/fonts/poppins/poppins-600.woff2',
  '/static/fonts/poppins/poppins-700.woff2',
  '/static/fonts/material-symbols/material-symbols-outlined.ttf',
  '/static/icons/app-icon-192.png',
  '/static/images/madre-amorosa.jpg'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim())));
// Red primero para archivos estáticos: así los cambios de CSS/JS se ven al
// instante y, cuando no hay conexión, se responde con la copia en caché.
// El HTML autenticado nunca se guarda en caché para no dejar datos privados
// en un dispositivo compartido.
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  const esEstatico = url.origin === self.location.origin && url.pathname.startsWith('/static/');
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (esEstatico && response && response.ok) {
          const copia = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copia)).catch(() => {});
        }
        return response;
      })
      .catch(() => caches.match(event.request, { ignoreSearch: true }).then(cached => cached || (
        event.request.mode === 'navigate' ? caches.match('/offline.html') : Response.error()
      )))
  );
});
