// v186: simple mode shows only the numbers that need attention (owner, 2026-11-26; queue simple-only-red-amber, slice 1).
// In simple Today the red and amber vitals stay in view right after the daily three, worst first (low before watch), and
// every number that is fine waits inside More for today. With nothing red or amber, one calm line says all the numbers
// are fine and no vital number shows.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const mixed = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const good = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 1000000,
  nw: 50000000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
function dkey(d) { const p = (x) => (x < 10 ? "0" + x : "" + x); return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()); }
function boot(pr, extra) {
  return new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.localStorage.setItem("sovP", JSON.stringify(pr));
      if (extra) Object.keys(extra).forEach((k) => w.localStorage.setItem(k, JSON.stringify(extra[k])));
      w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
}
const daily = {}; daily[dkey(new Date())] = ["ex", "mf", "fm"];
const stack = {}; ["L0", "L1", "L2", "L3", "L4"].forEach((id) => { const o = {}; for (let i = 0; i < 40; i++) o[i] = true; stack[id] = o; });
const doms = [boot(mixed), boot(good, { sovS: { daily: daily }, gm_stack: stack })];
setTimeout(() => {
  const [m, g] = doms.map(x => { x.window.goTab("today"); return x.window; });
  const md = m.document, ms = md.querySelector("#sections .section.active"), md3 = ms.querySelector(".gm-d3");
  const mfold = ms.querySelector("details.gm-simple-more"), att = ms.querySelector(".gm-vitals-attn");
  const attTiles = att ? [...att.children].filter(x => x.getAttribute("data-state")) : [];
  const states = attTiles.map(x => x.getAttribute("data-state"));
  ok("simple: the numbers at risk sit right after the daily three", !!att && !!md3 && md3.nextElementSibling === att && !mfold.contains(att), att ? "not after the three" : "no strip");
  ok("simple: only red and amber numbers are in view", states.length > 0 && states.every(s => s === "low" || s === "watch"), states.join(","));
  ok("simple: worst first, red before amber", states.indexOf("low") >= 0 && (states.indexOf("watch") < 0 || states.indexOf("low") < states.indexOf("watch")), states.join(","));
  const allTiles = [...md.querySelectorAll("#gmVitals > div, .gm-vitals-attn > div")];
  const risk = allTiles.filter(x => { const s = x.getAttribute("data-state"); return s === "low" || s === "watch"; });
  ok("simple: every red and amber number is in view", !!att && risk.length === attTiles.length && risk.every(x => att.contains(x)), risk.length + " risk, " + attTiles.length + " shown");
  const greens = [...md.querySelectorAll("#gmVitals > div")].filter(x => x.getAttribute("data-state") === "good");
  ok("simple: every number that is fine waits in More for today", greens.length > 0 && greens.every(x => mfold.contains(x) && !(att && att.contains(x))), greens.length + " good in view or loose");

  const gd = g.document, gs = gd.querySelector("#sections .section.active"), gd3 = gs.querySelector(".gm-d3"), gfold = gs.querySelector("details.gm-simple-more");
  ok("all fine: no number at risk is in view", !gs.querySelector(".gm-vitals-attn"));
  const calm = gs.querySelector(".gm-all-fine");
  ok("all fine: one calm line right after the daily three", !!calm && gs.querySelectorAll(".gm-all-fine").length === 1 && gd3.nextElementSibling === calm && /fine/i.test(calm.textContent), calm ? calm.textContent : "none");
  const gv = gd.getElementById("gmVitals");
  ok("all fine: nothing else numeric shows; the numbers wait in More for today", !!gv && gfold.contains(gv) && !gs.querySelector(":scope > #gmVitals"), gv ? "loose" : "no vitals");
  console.log("test186 simple: only red and amber in view: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
