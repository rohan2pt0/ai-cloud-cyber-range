// test159: the shared world (guiding-map/shared/world.js, owner 2026-11-23): one engine for the real-world objects, used by
// every screen and every app, with a fixed meaning each; the flag is cloth moved by physics. Fake data only; no network.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false, mine: { epf: 500000 } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
let rafs = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    const raf = w.requestAnimationFrame; w.requestAnimationFrame = (f) => { rafs++; return raf ? raf.call(w, f) : 0; }; } });
setTimeout(() => {
  const w = dom.window, X = w.SXWorld;
  ok("the shared world is built into the app", !!X && typeof X.flag === "function");
  ok("every object has one meaning, a use and an avoid", X && X.CATALOG.length === 6 && X.CATALOG.every(c => c.id && c.means && c.use && c.avoid && typeof X[c.id] === "function"));
  // the cloth: physics, not a loop
  const C = X.cloth, run = (kmh) => { const s = C.make(); s.t = 0;   // a fixed gust phase, so a lull at one moment cannot decide it
    for (let i = 0; i < 300; i++) C.step(s, kmh, 1 / 60); return s; };
  const fly = (s) => s.p.filter((p, i) => i % C.cols === C.cols - 1);
  const mx = (s) => fly(s).reduce((a, p) => a + p.x, 0) / C.rows, my = (s) => fly(s).reduce((a, p) => a + p.y, 0) / C.rows;
  const avg = (kmh) => { const s = run(kmh); let x = 0, y = 0; for (let i = 0; i < 240; i++) { C.step(s, kmh, 1 / 60); x += mx(s); y += my(s); } return { s, x: x / 240, y: y / 240 }; };
  const A40 = avg(40), A3 = avg(3), s40 = A40.s;   // averaged over 4 s, so a gust or a lull at one moment does not decide it
  ok("the hoist stays on the pole", s40.p.filter(p => p.pin).every(p => p.x === 0));
  const worst = s40.c.filter(c => c[3] === 1).reduce((m, c) => { const a = s40.p[c[0]], b = s40.p[c[1]]; return Math.max(m, Math.abs(Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z) - c[2]) / c[2]); }, 0);
  ok("the cloth does not tear or stretch in a 40 km/h wind (every edge within 15%)", worst < 0.15, worst.toFixed(3));
  ok("in a strong wind the fly streams out; in a breath of air it hangs", A40.x > A3.x + 6 && A3.y > A40.y + 4, A40.x.toFixed(1) + "," + A40.y.toFixed(1) + " vs " + A3.x.toFixed(1) + "," + A3.y.toFixed(1));
  ok("the cloth moves on its own between steps (gusts, the wake)", (() => { const a = JSON.stringify(s40.p.map(p => p.z.toFixed(3))); C.step(s40, 40, 1 / 30); C.step(s40, 40, 1 / 30); return a !== JSON.stringify(s40.p.map(p => p.z.toFixed(3))); })());
  const f = X.flag(0, 0, { gold: true }), faces = (f.match(/<polygon /g) || []).length;
  ok("the flag is shaded faces of cloth, one per cell", faces === (C.cols - 1) * (C.rows - 1), faces);
  ok("faces are lit, not one flat colour", new Set((f.match(/fill="rgb\([^)]*\)"/g) || [])).size > 8);
  w.document.body.insertAdjacentHTML("beforeend", "<svg>" + f + "</svg>"); const r0 = rafs; X.start();
  ok("no animation loop runs in tests or audits", rafs === r0, rafs - r0);
  // reuse-first: the Life OS draws with the shared engines and keeps no private copy
  const ops = fs.readFileSync(path.join(__dirname, '..', 'ops.js'), 'utf8');
  ok("no private copy of the moon, the bars, the vessel or the rings in ops.js", !/#fbf7ea|#fff1c4|#5fd3c0|#5a3a22/.test(ops));
  ok("the screens use the shared objects", /sx-bars/.test(w.gmGoldBars(4e6, 8e6)) && /sx-vessel/.test(w.gmVessel(3, 6, "watch")) && /SXWorld\.moon/.test(ops));
  ok("objects say their number in words too", /aria-label="4 gold bars of ₹10 lakh, 4 more to the aim"/.test(w.gmGoldBars(4e6, 8e6)));
  console.log("test159 shared world: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); } process.exit(0);
}, 400);
