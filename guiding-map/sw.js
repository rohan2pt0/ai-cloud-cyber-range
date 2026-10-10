/* SecuRAX Guiding Map — offline app shell. Cache-first for the shell, network passthrough
   for everything else (API calls to the gateway are never cached). Bump CACHE on each change. */
const CACHE = 'guiding-map-v3';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon.svg'];
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Only serve the app shell from cache; let API/cross-origin calls go straight to network.
  if (e.request.method === 'GET' && url.origin === location.origin) {
    e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).catch(() => caches.match('./index.html'))));
  }
});
