/* The Guiding Map — offline shell.
   Bump CACHE whenever you redeploy; old caches are dropped on activate. */
const CACHE = "guiding-map-securax-v14.7.0";   // bump on any PWA change so clients drop the old cache
const SHELL = [
  "./",
  "./index.html",
  "./hub.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png"
];

// ---- Access-aware install: never let a redirect poison the precache ----
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c =>
      Promise.all(SHELL.map(u =>
        fetch(new Request(u, { credentials: "same-origin", redirect: "follow" }))
          .then(res => {
            if (!cacheable(res)) return;            // 302 to Access, opaque, or error
            return c.put(u, res.clone());
          })
          .catch(() => {})                          // one bad asset must not fail install
      ))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// A response is cacheable only if it is a real, non-redirected, OK, basic response.
// opaqueredirect / redirected / !ok are exactly how a stale shell gets pinned forever.
function cacheable(res) {
  if (!res) return false;
  if (res.type === "opaqueredirect" || res.type === "opaque") return false;
  if (res.redirected) return false;
  if (!res.ok) return false;
  return true;
}

function isAccessRedirect(res) {
  try {
    return res.redirected && new URL(res.url).hostname.endsWith("cloudflareaccess.com");
  } catch (err) { return false; }
}

function tellClients(msg) {
  return self.clients.matchAll({ type: "window", includeUncontrolled: true })
    .then(cs => cs.forEach(c => c.postMessage(msg)));
}

// Network-first for the app shell so a redeploy lands immediately;
// cache is the fallback, so a dead connection still opens the app.
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  let url;
  try { url = new URL(req.url); } catch (err) { return; }
  if (url.origin !== location.origin) return; // let fonts/CDN fail silently offline

  e.respondWith(
    fetch(new Request(req, { credentials: "same-origin", redirect: "follow", cache: "no-cache" }))   // revalidate: skip the browser's heuristic freshness
      .then(res => {
        if (isAccessRedirect(res)) {
          // The Access session is gone. A service worker cannot complete an
          // interactive email-OTP login, so hand it back to the page.
          tellClients({ type: "AUTH_EXPIRED" });
          return new Response("", {
            status: 401,
            statusText: "Access session expired",
            headers: { "Cache-Control": "no-store" }
          });
        }
        if (cacheable(res)) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() => caches.match(req).then(r => r || caches.match("./index.html")))
  );
});


// ---- Web Push (sent by the companion Cloudflare Worker, see push-worker.js) ----
self.addEventListener("push", e => {
  let d = { title: "The Guiding Map", body: "Time for your check-in." };
  try { if (e.data) d = Object.assign(d, e.data.json()); } catch (err) {}
  e.waitUntil(self.registration.showNotification(d.title, {
    body: d.body,
    icon: "./icon-192.png",
    badge: "./icon-192.png",
    tag: d.tag || "gm-nudge",
    renotify: false,
    data: { url: d.url || "./index.html" }
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const target = (e.notification.data && e.notification.data.url) || "./index.html";
  e.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(cs => {
      for (const c of cs) if ("focus" in c) return c.focus();
      return self.clients.openWindow(target);
    })
  );
});
