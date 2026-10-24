/* OS kit offline shell for edition vantage: network first, the cached copy when there is no network.
   Its own cache and its own scope (this folder), so it never touches another app's worker on the same address. */
const CACHE = "osk-vantage-88043f475e76";
const SHELL = ["./", "./index.html", "./manifest.json", "./icon-192.png", "./icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u =>
    fetch(new Request(u, { credentials: "same-origin" })).then(r => { if (r.ok && !r.redirected) return c.put(u, r.clone()); }).catch(() => {})
  ))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.indexOf("osk-vantage-") === 0 && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin || !url.pathname.startsWith(new URL("./", self.location).pathname)) return;
  e.respondWith(fetch(req, { cache: "no-cache" }).then(r => {
    if (r.ok && !r.redirected && r.type === "basic") { const c = r.clone(); caches.open(CACHE).then(k => k.put(req, c)).catch(() => {}); }
    return r;
  }).catch(() => caches.match(req).then(r => r || caches.match("./index.html"))));
});
