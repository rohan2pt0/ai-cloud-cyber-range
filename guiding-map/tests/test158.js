// test158: While you were away, the wind flag and the crest glint (owner 2026-11-23). Fake data only; no network: fetch is refused.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false, mine: { epf: 500000 } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
let fetched = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_seen", JSON.stringify({ at: Date.now() - 5 * 864e5, n: 900000, b: null }));
    w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = (u) => { if (/open-meteo/.test(String(u))) fetched++; return Promise.reject(new Error("offline")); }; } });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage;
  w.goTab("today"); w.renderAll();
  const a = d.querySelector(".gm-away");
  ok("after 5 days away, Today says so with the sunrises", !!a && /Welcome back\. 5 sunrises/.test(a.textContent) && a.querySelectorAll("svg circle").length === 10, a && a.textContent);
  ok("and what moved while away", a && /Net worth \+₹1,00,000/.test(a.textContent), a && a.textContent);
  a.querySelector("button").click();
  ok("one tap folds it, and it does not come back today", !d.querySelector(".gm-away"));
  // the wind: never fetched without consent; a stored reading drives the flag; a hostile answer cannot inject HTML
  ok("no wind request without the person's tap", fetched === 0, fetched);
  ok("without consent the cloth flies in a default breeze", /class="sx-cloth" data-gold="0" data-kmh="8"/.test(w.gmFlag(0, 0, false)));
  ls.setItem("gm_wind", JSON.stringify({ ok: true, speed: 30, dir: 90, at: Date.now() }));
  const f = w.gmFlag(0, 0, true);
  ok("a stored strong east wind drives the cloth and points it west", /data-kmh="30"/.test(f) && /scale\(-0\.55 0\.55\)/.test(f), f.slice(0, 200));
  ok("the line says whose wind it is and offers Stop", /30 km\/h from E/.test(w.gmWindLine()) && /Stop/.test(w.gmWindLine()));
  ls.setItem("gm_wind", JSON.stringify({ ok: true, speed: "<img src=x onerror=alert(1)>", dir: 90 }));
  ok("a hostile stored value is not used", w.gmWind() === null && !/onerror/.test(w.gmFlag(0, 0, false)));
  w.gmWindOn(false);
  ok("Stop forgets the place", JSON.parse(ls.getItem("gm_wind")).ok === false && !("lat" in JSON.parse(ls.getItem("gm_wind"))));
  ok("the crest glint rests for reduced motion", /prefers-reduced-motion: reduce\)\{\.sx-crest::after,header \.mark::after\{animation:none/.test(html));
  console.log("test158 away and wind: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
