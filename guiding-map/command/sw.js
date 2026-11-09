/* The Command Center door: keep a copy of the page on this device, so it opens with the site host down and with no network.
   The cache is named after the build the page registered (sw.js?b=<commit>), so a new release installs a new worker and drops the
   old cache by itself. Only this site's own files are touched: the probes to your machines are other sites and pass straight through. */
const BUILD = new URL(self.location.href).searchParams.get("b") || "dev";
const CACHE = "securax-door-" + BUILD;
const SHELL = ["./", "./index.html", "./door.css", "./serif.woff2", "./door-logic.js", "./door.js", "./manifest.json", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.all(SHELL.map(u => fetch(u, { cache: "no-store" }).then(r => { if (r.ok) return c.put(u, r); }).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;          // the probes are other sites: never touched
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {}); }
      return res;
    }).catch(() => caches.match(req).then(hit => hit || caches.match("./index.html")))
  );
});
