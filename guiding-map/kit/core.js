/* OS kit core: the parts every edition shares.
   An edition (kit/editions/<id>.json) names the app, its words and its content; the modules do the work.
   Storage: every key is "osk:<edition>:<name>" so two apps on one address never touch each other's data.
   Keys starting with "~" stay on this device (undo, sync settings, device id) and never sync. */
(function () {
  "use strict";
  var ED = window.OSK_EDITION || {};
  var PFX = "osk:" + (ED.id || "app") + ":";
  var MEM = {};
  var K = window.OSK = { ed: ED, pfx: PFX, mods: {}, acts: {}, tab: null };

  /* ── storage ─────────────────────────────────────────────────────── */
  function raw(k) { try { return localStorage.getItem(PFX + k); } catch (e) { return MEM[k] === undefined ? null : MEM[k]; } }
  function put(k, s) { try { localStorage.setItem(PFX + k, s); } catch (e) { MEM[k] = s; } }
  K.get = function (k, d) { var s = raw(k); if (s === null) return d; try { return JSON.parse(s); } catch (e) { return d; } };
  // Every write stamps the key's time (the sync merge rule: newer wins) and keeps the old value for Undo.
  K.set = function (k, v, opt) {
    var old = raw(k), s = JSON.stringify(v);
    if (old === s) return;
    put(k, s);
    if (k.charAt(0) === "~") return;
    var m = K.get("~meta", {}); m[k] = Date.now(); put("~meta", JSON.stringify(m));
    if (!(opt && opt.noUndo)) {
      var u = K.get("~undo", []); u.push({ k: k, v: old, t: Date.now(), w: (opt && opt.what) || "" });
      put("~undo", JSON.stringify(u.slice(-30)));
    }
    K.syncSoon();
  };
  K.undo = function () {
    var u = K.get("~undo", []), e = u.pop();
    if (!e) { K.toast("Nothing to undo."); return; }
    put("~undo", JSON.stringify(u));
    if (e.v === null) { try { localStorage.removeItem(PFX + e.k); } catch (x) { delete MEM[e.k]; } } else put(e.k, e.v);
    var m = K.get("~meta", {}); m[e.k] = Date.now(); put("~meta", JSON.stringify(m));
    K.syncSoon(); K.render(); K.toast("Undone" + (e.w ? ": " + e.w : "") + ".");
  };
  K.keys = function () {
    var out = [];
    try { for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k.indexOf(PFX) === 0) out.push(k.slice(PFX.length)); } }
    catch (e) { out = Object.keys(MEM); }
    return out;
  };

  /* ── small helpers ───────────────────────────────────────────────── */
  K.esc = function (s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); };
  K.ymd = function (d) { d = d || new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); };
  K.days = function (a, b) { return Math.round((Date.parse(b || K.ymd()) - Date.parse(a)) / 864e5); };   // whole days from a to b
  K.addDays = function (d, n) { var x = new Date(Date.parse(d) + n * 864e5); return K.ymd(x); };
  K.uid = function () { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); };
  K.quarter = function (d) { d = d || new Date(); return d.getFullYear() + "-Q" + (Math.floor(d.getMonth() / 3) + 1); };
  // The edition's own word for a thing ("goals" -> "Security OKRs"); the module's default otherwise.
  K.term = function (k, d) { return (ED.terms && ED.terms[k]) || d || k; };
  K.cfg = function (mod) { return (ED.modules && ED.modules[mod]) || null; };
  K.val = function (id) { var e = document.getElementById(id); return e ? String(e.value || "").trim() : ""; };
  K.toast = function (msg) {
    var t = document.getElementById("oskToast"); if (!t) return;
    t.innerHTML = K.esc(msg) + (K.get("~undo", []).length ? ' <button data-a="undo">Undo</button>' : "");
    t.className = "on"; clearTimeout(K._tt); K._tt = setTimeout(function () { t.className = ""; }, 5000);
  };
  K.card = function (title, body, extra) { return '<section class="card' + (extra ? " " + extra : "") + '">' + (title ? "<h3>" + title + "</h3>" : "") + body + "</section>"; };
  K.bar = function (pct) { pct = Math.max(0, Math.min(100, Math.round(pct))); return '<div class="bar" role="img" aria-label="' + pct + ' percent"><i style="width:' + Math.max(pct, 2) + '%"></i></div>'; };

  /* ── modules ─────────────────────────────────────────────────────── */
  // A module: { id, label, icon, render(arg) -> html, next() -> {score, text, go} | null, week() -> [{n, what}] }
  K.module = function (m) { K.mods[m.id] = m; if (m.acts) Object.keys(m.acts).forEach(function (a) { K.acts[a] = m.acts[a]; }); };
  K.on = function (id) { return !!K.cfg(id) && !!K.mods[id]; };
  K.tabs = function () {
    var t = [];
    (ED.nav || []).forEach(function (id) {
      var base = id.split(":")[0], m = K.mods[base];
      if (!m || !K.cfg(base)) return;
      t.push({ id: id, label: m.label(id.split(":")[1]), icon: m.icon || "" });
    });
    return t;
  };
  K.go = function (id) { K.tab = id; try { history.replaceState(null, "", "#" + id); } catch (e) {} K.render(); window.scrollTo(0, 0); };
  K.render = function () {
    var tabs = K.tabs();
    if (!K.tab || !tabs.some(function (t) { return t.id === K.tab; })) K.tab = tabs.length ? tabs[0].id : null;
    var parts = (K.tab || "").split(":"), m = K.mods[parts[0]];
    var main = document.getElementById("oskMain");
    try { main.innerHTML = m ? m.render(parts[1]) : "<p>No modules are switched on in this edition.</p>"; }
    catch (e) { main.innerHTML = K.card("This screen hit a problem", "<p>" + K.esc(e.message) + "</p><p>Your data is safe. Try another screen, or Undo the last change.</p>"); if (window.console) console.error(e); }
    navRender(tabs);
    var h = document.getElementById("oskWho"); if (h) h.textContent = K.get("profile", {}).name || "";
  };
  function navRender(tabs) {
    var nav = document.getElementById("oskNav"), more = document.getElementById("oskMore");
    var n = ED.nav_main || 4, h = "", s = "";
    tabs.forEach(function (t, i) {
      var on = t.id === K.tab ? ' class="on" aria-current="page"' : "";
      var lab = (ED.nav_short && ED.nav_short[t.id]) || t.label;   // the bottom menu has room for a short word
      var b = '<button data-a="go" data-x="' + K.esc(t.id) + '"' + on + (lab !== t.label ? ' aria-label="' + K.esc(t.label) + '"' : "") + '>' + K.esc(lab) + '</button>';
      if (i < n) h += b; else s += b;
    });
    var inMore = tabs.slice(n).some(function (t) { return t.id === K.tab; });
    if (s) h += '<button data-a="more"' + (inMore ? ' class="on"' : "") + ' aria-haspopup="true">More</button>';
    nav.innerHTML = h; more.innerHTML = '<div class="sheet" role="menu">' + s + "</div>";
  }

  /* ── one click handler for the whole app ─────────────────────────── */
  // Buttons carry data-a (action) and data-x (argument), never inline code: an id can never break out into script.
  K.acts.go = function (x) { document.getElementById("oskMore").className = ""; K.go(x); };
  K.acts.more = function () { var m = document.getElementById("oskMore"); m.className = m.className ? "" : "on"; };
  K.acts.undo = function () { K.undo(); };
  K.acts.theme = function () {
    var t = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", t); K.set("~theme", t);
  };
  document.addEventListener("click", function (ev) {
    var el = ev.target.closest ? ev.target.closest("[data-a]") : null;
    if (!el) { var mo = document.getElementById("oskMore"); if (mo && ev.target === mo) mo.className = ""; return; }
    var f = K.acts[el.getAttribute("data-a")];
    if (!f) return;
    ev.preventDefault();
    try { f(el.getAttribute("data-x"), el); } catch (e) { K.toast("That did not work: " + e.message); if (window.console) console.error(e); }
  });
  document.addEventListener("change", function (ev) {
    var el = ev.target; if (!el.getAttribute) return;
    var f = K.acts[el.getAttribute("data-c")];
    if (f) f(el.getAttribute("data-x"), el);
  });

  /* ── export and import: the backup that always works ─────────────── */
  K.dump = function () {
    var o = { app: ED.id, version: 1, at: new Date().toISOString(), data: {}, meta: K.get("~meta", {}) };
    K.keys().forEach(function (k) { if (k.charAt(0) !== "~") o.data[k] = raw(k); });
    return o;
  };
  K.load = function (o) {
    if (!o || o.app !== ED.id || typeof o.data !== "object") throw new Error("this file is not a backup of " + (ED.name || "this app"));
    Object.keys(o.data).forEach(function (k) { if (k.charAt(0) !== "~" && typeof o.data[k] === "string") put(k, o.data[k]); });
    var m = K.get("~meta", {}), now = Date.now(); Object.keys(o.data).forEach(function (k) { m[k] = now; }); put("~meta", JSON.stringify(m));
    K.set("lastImport", K.ymd(), { noUndo: true });
  };

  /* ── sync: the same estate sync the Life OS uses, own keys only ──── */
  // Uses the Life OS pairing on this address (gm_sync_cfg) or this app's own (~sync). The sync service merges per key on its side,
  // so this app sends only its own keys and never overwrites the Life OS's. Newer wins; a tie goes to the larger value, as on the server.
  function syncCfg() {
    var own = K.get("~sync", null); if (own && own.url && (own.key || own.access)) return own;
    try { var g = JSON.parse(localStorage.getItem("gm_sync_cfg") || "null"); if (g && g.url && (g.key || g.access)) return g; } catch (e) {}
    return null;
  }
  K.syncCfg = syncCfg;
  function hdrs(c) { return c.access ? { "Content-Type": "application/json" } : { "Content-Type": "application/json", "Authorization": "Bearer " + c.key }; }
  function stateURL(c) { return String(c.url).replace(/\/+$/, "") + "/state?user=" + encodeURIComponent(c.user || ""); }
  function cpAfter(a, b) {
    var i = 0, j = 0;
    while (i < a.length && j < b.length) { var x = a.codePointAt(i), y = b.codePointAt(j); if (x !== y) return x > y; i += x > 0xFFFF ? 2 : 1; j += y > 0xFFFF ? 2 : 1; }
    return a.length - i > b.length - j;
  }
  K.merge = function (payload, rmeta) {
    var m = K.get("~meta", {}), changed = 0, mine = K.keys().filter(function (k) { return k.charAt(0) !== "~"; }).length, theirs = 0;
    Object.keys(payload).forEach(function (fk) { if (fk.indexOf(PFX) === 0 && fk.charAt(PFX.length) !== "~") theirs++; });
    // A remote copy with far fewer of our keys than we hold is a wrong or damaged row, not a real state: refuse it.
    if (mine > 10 && theirs < mine / 2) { K.set("~syncNote", K.ymd() + ": the estate copy had " + theirs + " items against " + mine + " here; not merged."); return -1; }
    Object.keys(payload).forEach(function (fk) {
      if (fk.indexOf(PFX) !== 0) return;
      var k = fk.slice(PFX.length); if (k.charAt(0) === "~") return;
      var rt = rmeta[fk] || 0, lt = m[k] || 0, rv = String(payload[fk]), lv = raw(k);
      if (lv === rv) return;
      if (lv === null || rt > lt || (rt === lt && cpAfter(rv, String(lv)))) { put(k, rv); m[k] = rt || Date.now(); changed++; }
    });
    if (changed) put("~meta", JSON.stringify(m));
    return changed;
  };
  K.push = function () {
    var c = syncCfg(); if (!c || !window.fetch) return Promise.resolve(false);
    var m = K.get("~meta", {}), payload = {}, meta = {};
    K.keys().forEach(function (k) { if (k.charAt(0) === "~") return; payload[PFX + k] = raw(k); meta[PFX + k] = m[k] || Date.now(); });
    return fetch(stateURL(c), { method: "PUT", headers: hdrs(c), credentials: "same-origin", body: JSON.stringify({ payload: payload, meta: meta, updated_at: new Date().toISOString(), device: K.dev() }) })
      .then(function (r) { if (!r.ok) throw new Error("the estate said " + r.status); K.set("~synced", new Date().toISOString().slice(0, 16).replace("T", " ")); K.set("~syncFails", 0); return true; })
      .catch(function () { K.set("~syncFails", K.get("~syncFails", 0) + 1); return false; });
  };
  K.pull = function () {
    var c = syncCfg(); if (!c || !window.fetch || (navigator.onLine === false)) return Promise.resolve(0);
    return fetch(stateURL(c), { headers: hdrs(c), credentials: "same-origin" })
      .then(function (r) { if (r.status === 404) return { payload: {}, meta: {} }; if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (b) { var n = K.merge((b && b.payload) || {}, (b && b.meta) || {}); if (n > 0) K.render(); return K.push().then(function () { return n; }); })
      .catch(function () { K.set("~syncFails", K.get("~syncFails", 0) + 1); return 0; });
  };
  K.syncSoon = function () { if (!syncCfg()) return; clearTimeout(K._st); K._st = setTimeout(K.push, 3000); };
  K.dev = function () { var d = K.get("~dev", null); if (!d) { d = Math.random().toString(36).slice(2, 10); K.set("~dev", d); } return d; };

  /* ── start ───────────────────────────────────────────────────────── */
  K.start = function () {
    var th = K.get("~theme", null) || (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", th);
    var h = (location.hash || "").slice(1); if (h) K.tab = decodeURIComponent(h);
    if (!K.get("started", null)) K.set("started", K.ymd(), { noUndo: true });
    K.render();
    K.pull();
    document.addEventListener("visibilitychange", function () { if (document.visibilityState === "visible") K.pull(); });
    // Served over http(s) only: opened from a file there is no worker to register.
    if ("serviceWorker" in navigator && location.protocol.indexOf("http") === 0) navigator.serviceWorker.register("sw.js").catch(function () {});
  };
})();
