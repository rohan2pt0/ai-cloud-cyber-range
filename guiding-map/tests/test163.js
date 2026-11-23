// test163: the shared water (guiding-map/shared/water.js, owner 2026-11-23): real water in real glass. The physics is a pure
// height field (volume kept, settles, leans to the low side); no animation loop runs in tests; the SVG fallback stays.
// Fake data only; no network.
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
  const w = dom.window, W = w.SXWater;
  ok("the shared water is built into the app", !!W && typeof W.step === "function" && typeof W.make === "function");
  const d = W.depth(0.5), run = (s, n, tilt) => { for (let i = 0; i < n; i++) W.step(s, 1 / 60, tilt || 0); return s; };
  // volume: a splash and 600 steps leave the mean exactly where it was
  const a = W.make(d); W.splash(a, 20, 1.2); run(a, 600);
  ok("volume is conserved: the mean level is unchanged after 600 steps with a splash", Math.abs(W.mean(a.h) - d) / d < 0.005, W.mean(a.h) + " vs " + d);
  const b = W.make(d); W.splash(b, 30, 1.2); let peak = 0; for (let i = 0; i < 40; i++) { W.step(b, 1 / 60, 0); peak = Math.max(peak, W.energy(b)); }
  ok("a splash really moves the surface", peak > 0.2, peak);
  run(b, 560);
  ok("a splash settles: energy after 600 steps is under 5% of its peak", W.energy(b) < peak * 0.05, W.energy(b) + " vs " + peak);
  // tilt: the surface leans to the low side
  const t1 = run(W.make(d), 300, 1), t2 = run(W.make(d), 300, -1), half = (s, r) => { const n = s.n / 2; let x = 0; for (let i = r ? n : 0; i < (r ? s.n : n); i++) x += s.h[i]; return x / n; };
  ok("tilted right, the water stands higher on the right", half(t1, 1) > half(t1, 0) + 1, half(t1, 1).toFixed(2) + " vs " + half(t1, 0).toFixed(2));
  ok("tilted left, the water stands higher on the left", half(t2, 0) > half(t2, 1) + 1);
  ok("the tilted surface also keeps its volume", Math.abs(W.mean(t1.h) - d) / d < 0.005);
  ok("a shallow pool never leans through the floor", (() => { const s = run(W.make(W.depth(0.05)), 300, 1); return Math.min.apply(null, s.h) > 0; })());
  // no loop, no canvas in tests: the SVG with its words remains
  const r0 = rafs; W.scan(w.document); W.step(W.make(d), 1 / 60, 0);
  ok("no animation frame is requested by the water in tests", rafs === r0, rafs - r0);
  w.goTab("money"); w.renderAll();
  const wrap = w.document.querySelector(".gm-vessel .sx-water"), svg = wrap && wrap.querySelector("svg");
  ok("the vessel is a wrapper that says its level, state and aim", !!wrap && wrap.getAttribute("data-f") && /^(good|watch|low)$/.test(wrap.getAttribute("data-state")) && wrap.getAttribute("data-aim") !== null && wrap.getAttribute("role") === "img");
  ok("the SVG fallback with its aria-label remains", !!svg && /Buffer: [\d.]+ months of \d+ aimed for/.test(svg.getAttribute("aria-label")) && svg.getAttribute("aria-label") === wrap.getAttribute("aria-label") && /\d+m/.test(svg.textContent));
  ok("no canvas replaces it where there is no 2D context", !wrap.querySelector("canvas") && wrap.getAttribute("data-sxw") === null);
  const wsrc = fs.readFileSync(path.join(__dirname, '..', 'shared', 'water.js'), 'utf8');
  ok("the loop is shared and only runs when a person can see it", /IntersectionObserver/.test(wsrc) && /document\.hidden/.test(wsrc) && /prefers-reduced-motion/.test(wsrc) && (wsrc.match(/requestAnimationFrame\(/g) || []).length === 2);
  console.log("test163 shared water: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); } process.exit(0);
}, 400);
