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
  // the cloth: physics in real units (shared/cloth.js), not a loop. Every check runs the same seeded flag, so it is repeatable.
  const C = X.cloth, Ph = C.PHYS;
  ok("a real flag: 0.9 x 0.6 m of 110 g/m2 polyester as at least 24 x 16 nodes, in real air and gravity",
    Ph.width === 0.9 && Ph.height === 0.6 && Ph.areal === 0.11 && C.cols >= 24 && C.rows >= 16 && Ph.g === 9.81 && Ph.rho === 1.225 && Ph.cd === 1.2, JSON.stringify(Ph));
  const sim = (kmh, secs, seed) => { const s = C.make(seed || 11, kmh); for (let i = 0; i < secs * 60; i++) C.step(s, kmh, 1 / 60); return s; };
  // the angle of the cloth's centre of mass seen from the middle of the hoist, averaged over 2 s
  const lean = (kmh) => { const s = sim(kmh, 2); let v = 0, hz = 0;
    for (let f = 0; f < 120; f++) { C.step(s, kmh, 1 / 60); let x = 0, y = 0; for (let j = 0; j < C.rows; j++) for (let i = 0; i < C.cols; i++) { const q = C.node(s, i, j); x += q[0]; y += q[1]; }
      x = x / (C.cols * C.rows) - C.node(s, 0, 0)[0]; y = y / (C.cols * C.rows) + Ph.height / 2;
      v += Math.atan2(Math.abs(x), -y) * 180 / Math.PI; hz += Math.abs(Math.atan2(-y, x)) * 180 / Math.PI; }
    return { fromVertical: v / 120, fromHorizontal: hz / 120, s }; };
  const L1 = lean(1), L40 = lean(40), s40 = L40.s;
  ok("in a breath of air (1 km/h) the flag hangs: within 30 degrees of vertical", L1.fromVertical < 30, L1.fromVertical.toFixed(1));
  ok("at 40 km/h it streams out: within 25 degrees of horizontal", L40.fromHorizontal < 25, L40.fromHorizontal.toFixed(1));
  const g0 = C.node(s40, 0, 0), g1 = C.node(s40, 0, C.rows - 1), mid = C.node(s40, 0, C.rows >> 1);
  ok("two grommets hold it to the pole; the hoist between them sways a little, not a rigid line",
    g0[1] === 0 && Math.abs(g1[1] + Ph.height * 0.975) < 1e-9 && Math.hypot(mid[0] - g0[0], mid[2] - g0[2]) > 1e-4 && Math.hypot(mid[0] - g0[0], mid[2] - g0[2]) < 0.06, mid.map(v => v.toFixed(3)).join(","));
  // stretch: stiff. In a 50 km/h wind, over 2 s, every row stays within 2% of the flag's length and the cloth on average within 2%
  { const s = sim(50, 2); let rowWorst = 0, sum = 0, n = 0;
    for (let f = 0; f < 120; f++) { C.step(s, 50, 1 / 60);
      for (let j = 0; j < C.rows; j++) { let len = 0; for (let i = 0; i < C.cols - 1; i++) { const a = C.node(s, i, j), b = C.node(s, i + 1, j), e = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]); len += e; sum += e / (Ph.width / (C.cols - 1)) - 1; n++; }
        rowWorst = Math.max(rowWorst, len / Ph.width - 1); } }
    ok("under 2% stretch at 50 km/h (each row's length, and the mean of every edge)", rowWorst < 0.02 && sum / n < 0.02, (rowWorst * 100).toFixed(2) + "% row, " + (sum / n * 100).toFixed(2) + "% mean"); }
  // flutter: the pole's wake drives it at St U / d scaled to the flag, U being the wind the flag felt (the gusts move it, as
  // in a real wind). The power-weighted mean frequency of the fly edge's motion is compared with it.
  const flutter = (kmh, seed) => { const s = sim(kmh, 2, seed), T = 480, zs = []; let felt = 0; for (let j = 0; j < C.rows; j += 3) zs.push([]);
    for (let f = 0; f < T; f++) { C.step(s, kmh, 1 / 60); felt += (1 + s.g) / T; zs.forEach((z, k) => z.push(C.node(s, C.cols - 1, 3 * k)[2])); }
    let sp = 0, sw = 0; for (let fq = 0.3; fq < 15; fq += 0.1) { let pw = 0;
      zs.forEach(z => { const m = z.reduce((a, b) => a + b, 0) / T; let re = 0, im = 0; for (let i = 0; i < T; i++) { const w = (0.5 - 0.5 * Math.cos(2 * Math.PI * i / T)) * (z[i] - m); re += w * Math.cos(2 * Math.PI * fq * i / 60); im += w * Math.sin(2 * Math.PI * fq * i / 60); } pw += re * re + im * im; });
      sp += pw * fq; sw += pw; }
    return { hz: sp / sw, want: Ph.flutterHz(kmh) * felt }; };
  const F40 = flutter(40, 12), F15 = flutter(15, 12);
  ok("the flutter frequency at 40 km/h is within 25% of St U / d scaled to the flag", Math.abs(F40.hz / F40.want - 1) < 0.25, F40.hz.toFixed(2) + " Hz vs " + F40.want.toFixed(2));
  ok("and it rises with the wind, as a real flag's does", F40.hz > F15.hz * 1.6, F15.hz.toFixed(2) + " -> " + F40.hz.toFixed(2));
  ok("the pole sheds at the Strouhal frequency St U / d (St 0.2, d 3 cm)", Math.abs(Ph.sheddingHz(36) - 0.2 * 10 / 0.03) < 1e-9);
  ok("stable at any frame rate: 60, 144 or 10 frames a second run the same small substeps for the same time", (() => {
    const a = sim(30, 1, 5), b = C.make(5, 30), c = C.make(5, 30); for (let i = 0; i < 10; i++) C.step(b, 30, 0.1); for (let i = 0; i < 144; i++) C.step(c, 30, 1 / 144);
    return [a, b, c].every(s => s.x.every(v => isFinite(v)) && Math.abs(s.t - 1) <= Ph.substep * 1.01); })());
  ok("the cloth moves on its own between steps (gusts, the wake)", (() => { const a = Array.from(s40.x).map(v => v.toFixed(4)).join(); C.step(s40, 40, 1 / 30); return a !== Array.from(s40.x).map(v => v.toFixed(4)).join(); })());
  const f = X.flag(0, 0, { gold: true }), faces = (f.match(/<polygon /g) || []).length;
  ok("without WebGL the flag is shaded SVG faces of the same cloth, one per fallback cell", faces === (C.svgCols - 1) * (C.svgRows - 1) && faces >= 80, faces);
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
