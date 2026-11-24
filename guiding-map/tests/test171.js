// test171: the lock's Scene choice (owner, 2026-11-24): Sky (default) or Sea beside the Privacy lock card, one tap,
// remembered in gm_lock_scene. The lock mounts SXSea when sea is chosen and SXSky as before when sky; the sea is silent
// on the lock and starts no loop in a test DOM. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-05", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, ret: 60, tsav: 20, example: false, earners: 1 };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false");
    w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true");
    w.localStorage.setItem("gm_lock", JSON.stringify({ id: "ZmFrZQ", salt: "ZmFrZQ", hash: "ZmFrZQ", off: true }));
    w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    try { Object.defineProperty(w.navigator, "credentials", { configurable: true, value: { get: function () { return Promise.resolve({}); } } }); } catch (e) {}
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("ops"); w.renderAll();
  let card = d.querySelector(".gm-lock-set");
  ok("the Privacy lock card shows", !!card);
  let sky = card && card.querySelector('[data-scene="sky"]'), sea = card && card.querySelector('[data-scene="sea"]');
  ok("a Scene choice shows Sky and Sea", !!sky && !!sea && /Sky/.test(sky.textContent) && /Sea/.test(sea.textContent));
  ok("Sky is the default", !!sky && sky.getAttribute("aria-checked") === "true" && sea.getAttribute("aria-checked") === "false");
  ok("the choice uses the shared segmented control", !!card.querySelector(".sx-seg") && sky.getAttribute("role") === "radio" && sea.getAttribute("role") === "radio");
  sea.click();
  ok("choosing Sea remembers it", w.localStorage.getItem("gm_lock_scene") === "sea");
  card = d.querySelector(".gm-lock-set");
  ok("the card shows Sea chosen", card.querySelector('[data-scene="sea"]').getAttribute("aria-checked") === "true" && card.querySelector('[data-scene="sky"]').getAttribute("aria-checked") === "false");
  w.localStorage.setItem("gm_lock_scene", "nonsense"); w.renderAll();
  card = d.querySelector(".gm-lock-set");
  ok("a damaged scene falls back to Sky", card.querySelector('[data-scene="sky"]').getAttribute("aria-checked") === "true" && card.querySelector('[data-scene="sea"]').getAttribute("aria-checked") === "false");
  card.querySelector('[data-scene="sea"]').click();
  const seaMount = w.SXSea.mount, skyMount = w.SXSky.mount;
  let seaCalls = [], skyCalls = [], seaStops = 0, seaHandle = null;
  w.SXSea.mount = function (el, opts) { seaCalls.push(el); var h = seaMount.call(w.SXSea, el, opts); seaHandle = h; if (h && h.stop) { var os = h.stop; h.stop = function () { seaStops++; return os.apply(h, arguments); }; } return h; };
  w.SXSky.mount = function (el, opts) { skyCalls.push(el); return skyMount.call(w.SXSky, el, opts); };
  w.localStorage.setItem("gm_lock", JSON.stringify({ id: "ZmFrZQ", salt: "ZmFrZQ", hash: "ZmFrZQ" }));
  w.gmLockNow();
  let lock = d.getElementById("gmLock");
  ok("the lock shows", !!lock);
  ok("the sea fills the lock", seaCalls.length === 1 && seaCalls[0] === lock && skyCalls.length === 0, "sea " + seaCalls.length + ", sky " + skyCalls.length);
  ok("the sea is silent on the lock", !lock.querySelector(".sx-sea-snd"));
  ok("the sea starts no loop in a test DOM", !!seaHandle && seaHandle.mode === "svg", seaHandle && seaHandle.mode);
  w.gmUnlock().then(function () { return new Promise(function (res) { setTimeout(res, 40); }); }).then(function () {
    ok("unlocking stops the sea", seaStops >= 1, "stops " + seaStops);
    ok("the lock is gone", !d.getElementById("gmLock"));
    card = d.querySelector(".gm-lock-set");
    ok("the card is back after unlocking", !!card);
    w.localStorage.setItem("gm_lock_scene", "nonsense"); w.renderAll();
    card = d.querySelector(".gm-lock-set");
    ok("a damaged scene falls back to Sky after unlocking", card.querySelector('[data-scene="sky"]').getAttribute("aria-checked") === "true");
    w.gmLockNow();
    const lock2 = d.getElementById("gmLock");
    ok("the sky mounts as before", skyCalls.length === 1 && skyCalls[0] === lock2 && seaCalls.length === 1, "sea " + seaCalls.length + ", sky " + skyCalls.length);
    console.log("test171 lock scene: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
  }).catch(function (err) {
    F++; e.push("unlocking threw :: " + (err && err.message));
    console.log("test171 lock scene: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(1);
  });
}, 400);
