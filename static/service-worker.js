const CACHE_NAME = 'aurora-shell-v4';
const APP_SHELL = [
  '/manifest.json',
  '/static/css/style.css',
  '/static/css/mvp.css',
  '/static/js/app.js',
  '/static/assets/inicio/aurora-logo.png',
  '/static/assets/inicio/guide-image.png',
  '/static/assets/inicio/notification.svg',
  '/static/assets/inicio/pregnancy-progress-ring.svg',
  '/static/assets/inicio/location.svg',
  '/static/assets/inicio/chevron.svg',
  '/static/assets/inicio/register-control.svg',
  '/static/assets/inicio/calendar.svg',
  '/static/assets/inicio/appointment-action.svg',
  '/static/assets/inicio/alert-icon.svg',
  '/static/assets/inicio/asset-05.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => { if (event.request.method === 'GET') event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request))); });
