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
  // The lock (queue app-lock, threat model "kit-lock"): with a biometric lock whose browser supports the WebAuthn PRF
  // extension, every value except the few device keys in PLAIN is stored encrypted ("enc1:" + AES-GCM), and decrypted
  // only into CACHE while unlocked. Without PRF the lock is a screen gate only, and says so.
  var PLAIN = { "~lock": 1, "~lang": 1, "~theme": 1, "~discreet": 1 };   // device keys that say nothing about the person
  var DK = null, CACHE = null, WQ = Promise.resolve();
  function sealed(k) { return !!CACHE && !PLAIN[k]; }
  function rawDisk(k) { try { return localStorage.getItem(PFX + k); } catch (e) { return MEM[k] === undefined ? null : MEM[k]; } }
  function raw(k) {
    if (sealed(k)) return Object.prototype.hasOwnProperty.call(CACHE, k) ? CACHE[k] : null;
    var s = rawDisk(k);
    return s && s.indexOf("enc1:") === 0 ? null : s;                      // locked: an encrypted value reads as absent
  }
  function put(k, s) {
    if (sealed(k)) { CACHE[k] = s; var key = DK; WQ = WQ.then(function () { return seal(key, s); }).then(function (c) { try { localStorage.setItem(PFX + k, c); } catch (e) { MEM[k] = c; } }); return; }
    try { localStorage.setItem(PFX + k, s); } catch (e) { MEM[k] = s; }
  }
  function drop(k) { if (CACHE) delete CACHE[k]; try { localStorage.removeItem(PFX + k); } catch (x) { delete MEM[k]; } }
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
    if (!e) { K.toast(K.t("core.nothing_undo", "Nothing to undo.")); return; }
    put("~undo", JSON.stringify(u));
    if (e.v === null) drop(e.k); else put(e.k, e.v);
    var m = K.get("~meta", {}); m[e.k] = Date.now(); put("~meta", JSON.stringify(m));
    K.syncSoon(); K.render(); K.toast(K.t("core.undone", "Undone") + (e.w ? ": " + e.w : "") + ".");
  };
  K.keys = function () {
    var out = [];
    try { for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k.indexOf(PFX) === 0) out.push(k.slice(PFX.length)); } }
    catch (e) { out = Object.keys(MEM); }
    return out;
  };

  /* ── the lock: device biometrics, encryption at rest, no new password ─────────────────────────
     Unlock is the device's own Face ID, fingerprint or Windows Hello (a WebAuthn platform credential made on this device,
     user verification required). Where the browser supports PRF, the authenticator's secret output derives the key that
     wraps a random data key; a one-time recovery phrase (PBKDF2, 310,000 rounds) wraps it too, so no one is ever locked
     out. Nothing is sent anywhere: no server, no account. Locks after IDLE seconds away; the screen is veiled when hidden. */
  var SUB = window.crypto && window.crypto.subtle, ENC = new TextEncoder(), DEC = new TextDecoder();
  function rnd(n) { var a = new Uint8Array(n); window.crypto.getRandomValues(a); return a; }
  function b64(u) { var s = ""; u = new Uint8Array(u); for (var i = 0; i < u.length; i++) s += String.fromCharCode(u[i]); return btoa(s); }
  function unb64(t) { var s = atob(t), u = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u; }
  function seal(key, text) {
    var iv = rnd(12);
    return SUB.encrypt({ name: "AES-GCM", iv: iv }, key, ENC.encode(text)).then(function (ct) {
      var o = new Uint8Array(12 + ct.byteLength); o.set(iv); o.set(new Uint8Array(ct), 12); return "enc1:" + b64(o); });
  }
  function unseal(key, c) { var u = unb64(c.slice(5)); return SUB.decrypt({ name: "AES-GCM", iv: u.slice(0, 12) }, key, u.slice(12)).then(function (p) { return DEC.decode(p); }); }
  function kekPrf(prf, salt) {
    return SUB.importKey("raw", prf, "HKDF", false, ["deriveKey"]).then(function (k) {
      return SUB.deriveKey({ name: "HKDF", hash: "SHA-256", salt: salt, info: ENC.encode("securax-kit-lock-v1") }, k, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]); });
  }
  function kekPhrase(phrase, salt) {
    return SUB.importKey("raw", ENC.encode(String(phrase).toUpperCase().replace(/[^A-Z2-7]/g, "")), "PBKDF2", false, ["deriveKey"]).then(function (k) {
      return SUB.deriveKey({ name: "PBKDF2", hash: "SHA-256", salt: salt, iterations: 310000 }, k, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]); });
  }
  function wrapDK(kek, dkRaw) { return seal(kek, b64(dkRaw)); }
  function unwrapDK(kek, w) {
    return unseal(kek, w).then(function (t) { return SUB.importKey("raw", unb64(t), "AES-GCM", true, ["encrypt", "decrypt"]); });
  }
  function phrase() { var A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567", r = rnd(20), s = ""; for (var i = 0; i < 20; i++) { s += A[r[i] % 32]; if (i % 4 === 3 && i < 19) s += "-"; } return s; }
  function lockRec() { try { return JSON.parse(localStorage.getItem(PFX + "~lock") || "null"); } catch (e) { return null; } }
  function loadCache(dk) {
    var c = {}, ks = K.keys().filter(function (k) { return !PLAIN[k]; });
    return Promise.all(ks.map(function (k) {
      var s = rawDisk(k); if (s === null) return null;
      if (s.indexOf("enc1:") !== 0) { c[k] = s; return null; }
      return unseal(dk, s).then(function (t) { c[k] = t; });
    })).then(function () { return c; });
  }
  K.lockInfo = function () { var r = lockRec(); return { on: !!r, mode: r ? r.mode : "off", idle: (r && r.idle) || 300, prf: K.prfSupported() }; };
  K.locked = !!lockRec();
  K.prfSupported = function () { return !!(window.PublicKeyCredential && navigator.credentials && SUB); };
  function webauthnGet(rec) {
    var opt = { publicKey: { challenge: rnd(32), userVerification: "required", timeout: 60000,
      allowCredentials: [{ type: "public-key", id: unb64(rec.cred), transports: ["internal"] }] } };
    if (rec.mode === "encrypted") opt.publicKey.extensions = { prf: { eval: { first: unb64(rec.salt) } } };
    return navigator.credentials.get(opt);
  }
  function prfOf(cred) { var x = cred && cred.getClientExtensionResults ? cred.getClientExtensionResults() : {}; return x && x.prf && x.prf.results && x.prf.results.first; }
  // Turn the lock on: one biometric prompt (two on browsers that only give PRF on sign-in), then the recovery phrase once.
  K.lockEnable = function () {
    if (!K.prfSupported()) return Promise.reject(new Error(K.t("lock.unsupported", "This browser cannot use the device lock.")));
    var salt = rnd(32), user = rnd(16);
    return navigator.credentials.create({ publicKey: { challenge: rnd(32), rp: { name: ED.name || "SecuRAX" },
      user: { id: user, name: (ED.name || "SecuRAX") + " on this device", displayName: K.get("profile", {}).name || (ED.name || "SecuRAX") },
      pubKeyCredParams: [{ type: "public-key", alg: -7 }, { type: "public-key", alg: -257 }], timeout: 60000,
      authenticatorSelection: { authenticatorAttachment: "platform", userVerification: "required", residentKey: "preferred" },
      extensions: { prf: { eval: { first: salt } } } } }).then(function (cred) {
      var rec = { v: 1, cred: b64(cred.rawId), salt: b64(salt), idle: 300, mode: "encrypted" };
      var x = cred.getClientExtensionResults ? cred.getClientExtensionResults() : {};
      if (!(x.prf && x.prf.enabled)) { rec.mode = "gate"; return rec; }
      var out = prfOf(cred);
      return out ? (rec.prf0 = out, rec) : webauthnGet(rec).then(function (c2) { var o = prfOf(c2); if (!o) rec.mode = "gate"; else rec.prf0 = o; return rec; });
    }).then(function (rec) {
      var pass = phrase(), out = rec.prf0; delete rec.prf0;
      if (rec.mode === "gate") { localStorage.setItem(PFX + "~lock", JSON.stringify(rec)); K.locked = false; return { phrase: null, mode: "gate" }; }
      return SUB.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]).then(function (dk) {
        var rsalt = rnd(16);
        return SUB.exportKey("raw", dk).then(function (dkRaw) {
          return Promise.all([kekPrf(out, unb64(rec.salt)).then(function (k) { return wrapDK(k, dkRaw); }),
                              kekPhrase(pass, rsalt).then(function (k) { return wrapDK(k, dkRaw); })]);
        }).then(function (w) {
          rec.wrapped = w[0]; rec.rwrapped = w[1]; rec.rsalt = b64(rsalt);
          return loadCache(dk).then(function (c) {
            DK = dk; CACHE = c;
            Object.keys(c).forEach(function (k) { put(k, c[k]); });          // every existing value, re-written encrypted
            return WQ.then(function () { localStorage.setItem(PFX + "~lock", JSON.stringify(rec)); K.locked = false; return { phrase: pass, mode: "encrypted" }; });
          });
        });
      });
    });
  };
  function opened(dk) { return loadCache(dk).then(function (c) { DK = dk; CACHE = c; K.locked = false; K.render(); }); }
  K.unlock = function () {
    var rec = lockRec(); if (!rec) { K.locked = false; return Promise.resolve(); }
    return webauthnGet(rec).then(function (cred) {
      if (rec.mode !== "encrypted") { K.locked = false; K.render(); return; }
      var out = prfOf(cred); if (!out) throw new Error(K.t("lock.failed", "That did not unlock. Try again, or use your recovery phrase."));
      return kekPrf(out, unb64(rec.salt)).then(function (k) { return unwrapDK(k, rec.wrapped); }).then(opened);
    });
  };
  K.unlockPhrase = function (p) {
    var rec = lockRec(); if (!rec || rec.mode !== "encrypted") return Promise.reject(new Error("no recovery phrase"));
    return kekPhrase(p, unb64(rec.rsalt)).then(function (k) { return unwrapDK(k, rec.rwrapped); }).then(opened)
      .catch(function () { throw new Error(K.t("lock.bad_phrase", "That recovery phrase does not match.")); });
  };
  // Turn it off: only while unlocked; every value goes back to plain storage first, then the lock record goes.
  K.lockDisable = function () {
    if (K.locked) return Promise.reject(new Error("unlock first"));
    var c = CACHE || {};
    return WQ.then(function () {
      CACHE = null; DK = null;
      Object.keys(c).forEach(function (k) { try { localStorage.setItem(PFX + k, c[k]); } catch (e) { MEM[k] = c[k]; } });
      localStorage.removeItem(PFX + "~lock"); K.render();
    });
  };
  K.lockNow = function () { if (!lockRec()) return; DK = null; CACHE = null; K.locked = true; K.render(); };
  K.lockIdle = function (sec) { var r = lockRec(); if (!r) return; r.idle = sec; localStorage.setItem(PFX + "~lock", JSON.stringify(r)); };
  // Away too long: lock. Hidden: veil the screen, so the app switcher and a glance over the shoulder show nothing.
  var hiddenAt = 0;
  document.addEventListener("visibilitychange", function () {
    if (!lockRec()) return;
    if (document.hidden) { hiddenAt = Date.now(); document.body.classList.add("osk-veil"); return; }
    document.body.classList.remove("osk-veil");
    if (!K.locked && hiddenAt && Date.now() - hiddenAt > K.lockInfo().idle * 1000) K.lockNow();
  });
  K.lockScreen = function () {
    var rec = lockRec(), enc = rec && rec.mode === "encrypted";
    return K.card("", (window.SXSky ? SXSky.seal() : "") + "<h3>" + K.esc(K.t("lock.title", "Locked")) + "</h3>"
      + "<p>" + K.esc(K.t("lock.body", "Unlock with this device's Face ID, fingerprint or Windows Hello.")) + "</p>"
      + '<button class="primary sx-glint" data-a="unlock">' + K.esc(K.t("lock.unlock", "Unlock")) + "</button>"
      + (enc ? '<details><summary>' + K.esc(K.t("lock.use_phrase", "Use your recovery phrase")) + '</summary><label for="lkPhrase">'
        + K.esc(K.t("lock.phrase", "Recovery phrase")) + '</label><input id="lkPhrase" autocomplete="off" autocapitalize="characters" spellcheck="false">'
        + '<button data-a="unlockPhrase">' + K.esc(K.t("lock.unlock", "Unlock")) + "</button></details>" : ""), "hero");
  };
  // Turn on from Settings or the Today invitation: one biometric prompt, then the recovery phrase shown once.
  K.lockStart = function () {
    K.lockEnable().then(function (r) { K._phrase = r.phrase; K._lockMode = r.mode; K.go("settings"); })
      .catch(function (e) { K.toast((e && e.name === "NotAllowedError") ? K.t("lock.cancelled", "Not turned on. You can try again any time.") : (e && e.message) || "Error"); });
  };
  K.lockCard = function () {
    var i = K.lockInfo(), T = function (k, d, v) { return K.esc(K.t(k, d, v)); };
    if (K._phrase) return K.card(T("lock.phrase_title", "Your recovery phrase"),
      "<p>" + T("lock.phrase_body", "If this device's Face ID or fingerprint ever changes, this phrase opens your data. Keep it somewhere safe, away from this device. It is shown once.") + "</p>"
      + '<p class="big" style="font-family:ui-monospace,monospace;letter-spacing:.06em;word-break:break-all">' + K.esc(K._phrase) + "</p>"
      + '<button class="primary" data-a="lockSaved">' + T("lock.saved", "I have saved it") + "</button>", "hero");
    if (!i.on) return K.card(T("lock.title_off", "Lock"),
      "<p>" + T("lock.offer", "Keep this private: unlock with this device's Face ID, fingerprint or Windows Hello. No new password.") + "</p>"
      + (i.prf ? '<button class="primary" data-a="lockOn">' + T("lock.turn_on", "Turn on") + "</button>"
               : '<p class="muted">' + T("lock.unsupported", "This browser cannot use the device lock.") + "</p>"));
    var idle = i.idle, opt = function (sec, lab) { return '<button data-a="lockIdleSet" data-x="' + sec + '" aria-pressed="' + (idle === sec) + '"' + (idle === sec ? ' class="on"' : "") + ">" + lab + "</button>"; };
    return K.card(T("lock.title_on", "Lock is on"),
      "<p>" + (i.mode === "encrypted" ? T("lock.mode_enc", "Your data on this device is encrypted, and opens only with your face, fingerprint or recovery phrase.")
                                        : T("lock.mode_gate", "Screen lock only: this browser cannot encrypt with the device lock, so the data itself is not encrypted.")) + "</p>"
      + "<p>" + T("lock.idle", "Lock after being away for") + '</p><div class="btns">' + opt(60, "1 min") + opt(300, "5 min") + opt(900, "15 min") + "</div>"
      + '<div class="btns"><button data-a="lockNowBtn">' + T("lock.lock_now", "Lock now") + '</button><button class="ghost" data-a="lockOff">' + T("lock.turn_off", "Turn off") + "</button></div>");
  };
  K.acts.unlock = function () { K.unlock().catch(function (e) { K.toast(e && e.message ? e.message : K.t("lock.failed", "That did not unlock. Try again, or use your recovery phrase.")); }); };
  K.acts.unlockPhrase = function () { K.unlockPhrase(K.val("lkPhrase")).catch(function (e) { K.toast(e.message); }); };

  /* ── small helpers ───────────────────────────────────────────────── */
  K.esc = function (s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); };
  K.ymd = function (d) { d = d || new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); };
  K.days = function (a, b) { return Math.round((Date.parse(b || K.ymd()) - Date.parse(a)) / 864e5); };   // whole days from a to b
  K.addDays = function (d, n) { var x = new Date(Date.parse(d) + n * 864e5); return K.ymd(x); };
  K.uid = function () { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); };
  K.quarter = function (d) { d = d || new Date(); return d.getFullYear() + "-Q" + (Math.floor(d.getMonth() / 3) + 1); };
  // The edition's own word for a thing ("goals" -> "Security OKRs"); the module's default otherwise.
  K.term = function (k, d) { return (ED.terms && ED.terms[k]) || d || k; };

  /* ── languages (queue multilingual) ─────────────────────────────────────────────────────────────
     K.t("today.do", "Do it now") gives the chosen language's text, or the English written in the code: never a blank and
     never a raw key. The language is the person's choice (Settings), else the device's own if a catalog exists, else
     English. Catalogs are baked into the app at build (kit/i18n/<lang>.json), so they work offline. */
  K.langs = function () { var L = { en: { name: "English", locale: "en-IN", status: "source" } };
    Object.keys(ED.i18n || {}).forEach(function (k) { L[k] = (ED.i18n[k] || {})._meta || { name: k }; }); return L; };
  K.lang = (function () {
    var cat = ED.i18n || {}, pick = null;
    try { pick = JSON.parse(localStorage.getItem(PFX + "~lang") || "null"); } catch (e) { pick = null; }
    if (pick && (pick === "en" || cat[pick])) return pick;
    var dev = String((navigator.languages && navigator.languages[0]) || navigator.language || "en").slice(0, 2).toLowerCase();
    return cat[dev] ? dev : "en";
  })();
  // The edition's own words in the chosen language: an overlay (kit/i18n/editions/<id>.<lang>.json) is merged over a
  // pristine copy, string over string, only where oskit's check allowed it (TRANSLATABLE keys); list items match by id.
  var ED0 = JSON.parse(JSON.stringify(ED));
  function mergeWords(base, over) {
    if (Array.isArray(over) && Array.isArray(base)) {
      over.forEach(function (v, i) {
        var b = v && typeof v === "object" && v.id ? base.filter(function (x) { return x && x.id === v.id; })[0] : null;
        if (b) mergeWords(b, v); else if (typeof v === "string" && typeof base[i] === "string") base[i] = v; else if (base[i] && typeof base[i] === "object") mergeWords(base[i], v);
      });
    } else if (over && typeof over === "object" && base && typeof base === "object") {
      Object.keys(over).forEach(function (k) {
        if (!(k in base) || k === "id") return;
        if (typeof over[k] === "string") { if (typeof base[k] === "string") base[k] = over[k]; }
        else mergeWords(base[k], over[k]);
      });
    }
  }
  K.applyLang = function () {
    Object.keys(ED).forEach(function (k) { if (k !== "i18n" && k !== "i18n_ed") delete ED[k]; });
    Object.keys(ED0).forEach(function (k) { if (k !== "i18n" && k !== "i18n_ed") ED[k] = JSON.parse(JSON.stringify(ED0[k])); });
    var ov = (ED.i18n_ed || {})[K.lang];
    if (ov) mergeWords(ED, ov);
  };
  K.applyLang();
  K.locale = function () { return (K.langs()[K.lang] || {}).locale || "en-IN"; };
  K.t = function (key, en, vars) {
    var c = (ED.i18n || {})[K.lang], s = (c && c.strings && c.strings[key]) || en || key;
    if (vars) Object.keys(vars).forEach(function (v) { s = s.split("{" + v + "}").join(vars[v]); });
    return s;
  };
  K.num = function (n, opt) { try { return new Intl.NumberFormat(K.locale(), opt).format(n); } catch (e) { return String(n); } };
  K.setLang = function (l) { K.set("~lang", l); K.lang = l; K.applyLang(); document.documentElement.lang = l; K.render(); };
  try { document.documentElement.lang = K.lang; } catch (e) {}
  K.cfg = function (mod) { return (ED.modules && ED.modules[mod]) || null; };
  K.val = function (id) { var e = document.getElementById(id); return e ? String(e.value || "").trim() : ""; };
  K.toast = function (msg) {
    var t = document.getElementById("oskToast"); if (!t) return;
    t.innerHTML = K.esc(msg) + (K.get("~undo", []).length ? ' <button data-a="undo">' + K.esc(K.t("core.undo", "Undo")) + '</button>' : "");
    t.className = "on"; clearTimeout(K._tt); K._tt = setTimeout(function () { t.className = ""; }, 5000);
  };
  /* The calendar contract (principle `in-the-calendar`), shared by every kit app: one .ics writer. Each event's UID is
     permanent (securax-<edition>-<id>@local), its start is fixed (the first occurrence on or after 2026-01-01, so every export
     of the same version is identical), its version goes out as SEQUENCE, and a retired item ends with UNTIL plus CANCELLED.
     Import into the same calendar each time: apps match events by UID within a calendar, so a newer file updates in place. */
  var CAL_DAYS = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"];
  K.icsText = function (t) { return String(t).replace(/\\/g, "\\\\").replace(/;/g, "\;").replace(/,/g, "\\,").replace(/\n/g, "\\n"); };
  function icsFold(line) { var out = [], s = line; while (s.length > 74) { out.push(s.slice(0, 74)); s = " " + s.slice(74); } out.push(s); return out.join("\r\n"); }
  function icsStamp(d, hh, mm) { function z(n) { return (n < 10 ? "0" : "") + n; } return d.getFullYear() + z(d.getMonth() + 1) + z(d.getDate()) + "T" + z(hh) + z(mm) + "00"; }
  K.calFirst = function (match) {                        // the first day on or after the fixed epoch that matches the rule
    var e = new Date(2026, 0, 1);
    for (var add = 0; add < 800; add++) { var t = new Date(2026, 0, 1 + add); if (match(t)) return t; }
    return e;
  };
  // events: [{ id, v, name, desc, rule, start (Date), hh, mins, retired }]
  K.ics = function (title, events) {
    var now = new Date(), stamp = icsStamp(now, now.getHours(), now.getMinutes());
    var L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//SecuRAX//" + K.icsText(ED.name || "OS kit") + " calendar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", icsFold("X-WR-CALNAME:" + K.icsText(title))];
    events.forEach(function (e) {
      var end = new Date(e.start); end.setHours(e.hh, e.mins || 30, 0, 0);
      L.push("BEGIN:VEVENT", "UID:securax-" + ED.id + "-" + e.id + "@local", "SEQUENCE:" + (e.v || 1), "DTSTAMP:" + stamp,
        "DTSTART:" + icsStamp(e.start, e.hh, 0), "DTEND:" + icsStamp(end, end.getHours(), end.getMinutes()),
        "RRULE:" + e.rule + (e.retired ? ";UNTIL=" + String(e.retired).replace(/-/g, "") + "T235959" : ""),
        "STATUS:" + (e.retired ? "CANCELLED" : "CONFIRMED"),
        icsFold("SUMMARY:" + K.icsText(e.name)), icsFold("DESCRIPTION:" + K.icsText(e.desc || "")),
        "BEGIN:VALARM", "ACTION:DISPLAY", icsFold("DESCRIPTION:" + K.icsText(e.name)), "TRIGGER:-PT30M", "END:VALARM", "END:VEVENT");
    });
    L.push("END:VCALENDAR");
    return L.join("\r\n") + "\r\n";
  };
  K.icsDays = CAL_DAYS;
  K.edition = function () { return ED; };
  K.download = function (name, text, type) {
    try {
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([text], { type: type || "text/plain" }));
      a.download = name; document.body.appendChild(a); a.click(); a.remove();
    } catch (e) { /* a browser without downloads still keeps the app working */ }
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
  // The lock screen is a night sky (the shared engine in shared/sky.js, the look in shared/lux.css): on while locked, gone on unlock.
  function night(on) {
    var b = document.body, sky = document.getElementById("oskSky");
    b.classList.toggle("osk-locked", !!on);
    if (on && !sky) {
      sky = document.createElement("div"); sky.id = "oskSky"; sky.setAttribute("aria-hidden", "true"); b.insertBefore(sky, b.firstChild);
      try { if (window.SXSky) SXSky.mount(sky, { comet: true }); } catch (e) {}
    }
    if (!on && sky) sky.parentNode.removeChild(sky);    // the sky's loop ends by itself once its element has gone
  }
  K.render = function () {
    night(K.locked);
    if (K.locked) {                                                     // locked: nothing of the person's on screen
      document.getElementById("oskMain").innerHTML = K.lockScreen();
      document.getElementById("oskNav").innerHTML = ""; document.getElementById("oskMore").innerHTML = "";
      var w = document.getElementById("oskWho"); if (w) w.textContent = "";
      return;
    }
    var tabs = K.tabs();
    if (!K.tab || !tabs.some(function (t) { return t.id === K.tab; })) K.tab = tabs.length ? tabs[0].id : null;
    var parts = (K.tab || "").split(":"), m = K.mods[parts[0]];
    var main = document.getElementById("oskMain");
    try { main.innerHTML = m ? m.render(parts[1]) : "<p>" + K.esc(K.t("core.no_modules", "No modules are switched on in this edition.")) + "</p>"; }
    catch (e) { main.innerHTML = K.card(K.esc(K.t("core.problem", "This screen hit a problem")), "<p>" + K.esc(e.message) + "</p><p>" + K.esc(K.t("core.problem_note", "Your data is safe. Try another screen, or Undo the last change.")) + "</p>"); if (window.console) console.error(e); }
    navRender(tabs);
    var h = document.getElementById("oskWho"); if (h) h.textContent = K.get("profile", {}).name || "";
    var sk = document.querySelector(".skip"); if (sk) sk.textContent = K.t("core.skip", "Skip to content");
    var th = document.querySelector('[data-a="theme"]');
    if (th) { th.textContent = K.t("core.theme", "Theme"); th.setAttribute("aria-label", K.t("core.theme_label", "Switch light or dark")); }
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
    if (s) h += '<button data-a="more"' + (inMore ? ' class="on"' : "") + ' aria-haspopup="true">' + K.esc(K.t("core.more", "More")) + '</button>';
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
    try { f(el.getAttribute("data-x"), el); } catch (e) { K.toast(K.t("core.failed", "That did not work: ") + e.message); if (window.console) console.error(e); }
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
  // Locked: no sync at all. A push would read every encrypted value as absent and send a copy of nulls, and a merge would
  // write the estate's plain copy over the encrypted one (both found in review, 2026-11-11). Sync resumes on unlock.
  K.merge = function (payload, rmeta) {
    if (K.locked) return 0;
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
    var c = syncCfg(); if (K.locked || !c || !window.fetch) return Promise.resolve(false);
    var m = K.get("~meta", {}), payload = {}, meta = {};
    K.keys().forEach(function (k) { if (k.charAt(0) === "~") return; payload[PFX + k] = raw(k); meta[PFX + k] = m[k] || Date.now(); });
    return fetch(stateURL(c), { method: "PUT", headers: hdrs(c), credentials: "same-origin", body: JSON.stringify({ payload: payload, meta: meta, updated_at: new Date().toISOString(), device: K.dev() }) })
      .then(function (r) { if (!r.ok) throw new Error("the estate said " + r.status); K.set("~synced", new Date().toISOString().slice(0, 16).replace("T", " ")); K.set("~syncFails", 0); return true; })
      .catch(function () { K.set("~syncFails", K.get("~syncFails", 0) + 1); return false; });
  };
  K.pull = function () {
    var c = syncCfg(); if (K.locked || !c || !window.fetch || (navigator.onLine === false)) return Promise.resolve(0);
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
