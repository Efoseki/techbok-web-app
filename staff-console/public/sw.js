const CACHE_NAME = 'techbok-shell-v3';
const APP_SHELL = ['/', '/manifest.webmanifest'];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('techbok-shell-') && k !== CACHE_NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).then(response => { const copy=response.clone(); caches.open(CACHE_NAME).then(cache=>cache.put('/',copy)); return response; }).catch(() => caches.match('/').then(cached => cached || new Response('TechBoK is offline. Reopen the application when connected at least once.', {status: 503, headers:{'Content-Type':'text/plain'}}))));
    return;
  }
  event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => { if(response.ok) { const copy=response.clone(); caches.open(CACHE_NAME).then(cache=>cache.put(request,copy)); } return response; })));
});
