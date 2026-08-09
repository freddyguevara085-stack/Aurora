const CACHE_NAME = 'aurora-cache-v2';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/js/app.js',
  '/static/icons/icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
