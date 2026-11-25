// test163: the shared water (guiding-map/shared/water.js, owner 2026-11-23): real water in real glass. The physics is a pure
// height field (volume kept, settles, leans to the low side), with real gravity-wave dispersion and Stokes bubbles; no
// animation loop runs in tests; the SVG fallback stays.
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
  // real physics: the slosh period matches the dispersion of gravity waves in a round glass, T = 2 pi / sqrt(g k tanh(k h))
  const sl = W.make(d); run(sl, 900, 1); const halves = () => half(sl, 1) - half(sl, 0); const ups = []; let pv = halves(), tt = 0;
  for (let i = 0; i < 720; i++) { W.step(sl, 1 / 240, 0); tt += 1 / 240; const nv = halves(); if (pv < 0 && nv >= 0) ups.push(tt - nv / (nv - pv) / 240); pv = nv; }
  const kS = 1.8412 / 0.042, Tth = 2 * Math.PI / Math.sqrt(9.81 * kS * Math.tanh(kS * d / 1000)), Tsim = ups.length > 1 ? (ups[ups.length - 1] - ups[0]) / (ups.length - 1) : 0;
  ok("slosh period within 15% of the dispersion formula (" + Tth.toFixed(3) + " s)", Tsim > 0 && Math.abs(Tsim - Tth) / Tth < 0.15, Tsim.toFixed(3) + " s vs " + Tth.toFixed(3));
  ok("the engine's own period uses g = 9.81 and the round glass's slosh wavenumber", Math.abs(W.slosh(d) - Tth) / Tth < 0.03 && Math.abs(W.kSlosh - kS) < 1e-6 && W.G === 9.81, W.slosh(d));
  ok("deeper water sloshes faster (tanh k h), as real water does", W.slosh(W.depth(1)) < W.slosh(W.depth(0.1)));
  // bubbles: Stokes' terminal velocity where Stokes holds; measured tap-water speeds where the bubble is larger
  const st = r => 2 * (998 - 1.2) * 9.81 * Math.pow(r / 1000, 2) / (9 * 1.0e-3) * 1000;
  ok("a small bubble rises at Stokes' velocity, within 15%", Math.abs(W.rise(0.03) - st(0.03)) / st(0.03) < 0.15 && Math.abs(W.stokes(0.2) - st(0.2)) < 1e-9, W.rise(0.03) + " vs " + st(0.03));
  ok("a 0.5 mm bubble rises near 5.5 cm/s and a 1 mm one near 10 cm/s, as measured in tap water (within 20%)", Math.abs(W.rise(0.25) - 55) / 55 < 0.2 && Math.abs(W.rise(0.5) - 100) / 100 < 0.2, W.rise(0.25).toFixed(1) + ", " + W.rise(0.5).toFixed(1));
  ok("the meniscus curls up over water's capillary length, about 2.7 mm", Math.abs(W.LC - 2.73) < 0.03 && W.MEN > 2 && W.MEN < 4, W.LC);
  const wsrc0 = fs.readFileSync(path.join(__dirname, '..', 'shared', 'water.js'), 'utf8');
  ok("the tracer uses measured optics: water 1.333, soda-lime 1.52, pure water's absorption, the gold's studio, ACES", /NW=1\.333/.test(wsrc0) && /NG=1\.52/.test(wsrc0) && /vec3\(\.45,\.06,\.01\)/.test(wsrc0) && /SXMat\.STUDIO/.test(wsrc0) && /aces\(/.test(wsrc0) && !!w.SXMat && /vec3 env\(/.test(w.SXMat.STUDIO));
  // the speed guard (owner 2026-11-24, tuned for real phones): only animating frames are timed; the median of the last 8 over
  // 20 ms halves the resolution; the 2D water only when it stays over 45 ms at half resolution, and it says why
  const G = () => ({ lvl: 0, ms: [] }), feed = (g, list, anim) => { list.forEach(m => W.guard(g, m, anim === undefined ? true : anim)); return g.lvl; };
  ok("the guard's thresholds are 20 ms (half) and 45 ms (2D) over the median of 8", W.GUARD_HALF === 20 && W.GUARD_2D === 45 && W.GUARD_N === 8);
  ok("a phone at 30-60 fps keeps full resolution (16 ms frames)", feed(G(), Array(40).fill(16)) === 0);
  ok("still frames are never timed: 40 slow calm frames change nothing", feed(G(), Array(40).fill(90), false) === 0);
  ok("a few slow frames do not trip it (it reads the median of 8)", feed(G(), [8, 8, 60, 8, 8, 70, 8, 8, 8, 90, 8, 8]) === 0);
  ok("8 animating frames over 20 ms drop to half resolution", feed(G(), Array(8).fill(25)) === 1);
  ok("half resolution at 25-40 ms stays traced (no fall to 2D)", feed(G(), Array(8).fill(25).concat(Array(40).fill(40))) === 1);
  ok("still over 45 ms at half resolution: the 2D water, with the reason", (() => { const g = G(); feed(g, Array(16).fill(60)); return g.lvl === 2 && /too slow \(60 ms a frame at half resolution\)/.test(g.why); })());
  ok("a shader not ready in 1.5 s (parallel compile) means half resolution, never back to full", (() => { const g = G(); W.guardLate(g); return g.lvl === 1 && feed(g, Array(8).fill(5)) === 1; })());
  ok("the 2D water is final for the page", (() => { const g = { lvl: 2, ms: [] }; return feed(g, Array(16).fill(1)) === 2; })());
  // the reason, stored with the version that decided it; a new version tries the traced water again
  ok("every fall to 2D has a reason a person can read", /no WebGL/.test(W.why2d("nogl")) && /high-precision/.test(W.why2d("precision")) && /context was lost/.test(W.why2d("lost")) && /did not compile \(ERROR: x\)/.test(W.why2d("link", "ERROR: x")));
  ok("the session key keeps the reason and the version", W.storedWhy(JSON.stringify({ v: "2|v1", why: "the GPU context was lost" }), "2|v1") === "the GPU context was lost");
  ok("a new app version clears the old decision (and the old bare '1' flag)", W.storedWhy(JSON.stringify({ v: "2|v1", why: "slow" }), "2|v2") === null && W.storedWhy("1", "2|v1") === null && W.storedWhy("{bad", "2|v1") === null && W.GUARD_KEY === "sx_water_2d");
  // the diagnosis line a long press shows
  ok("the long press says what drew the water: traced full or half", W.drawnLine({ ok: true, lvl: 0 }) === "Drawn with: traced water (full)" && W.drawnLine({ ok: true, lvl: 1, gpu: "Adreno (TM) 610" }) === "Drawn with: traced water (half). GPU: Adreno (TM) 610");
  ok("or 2D, and why", W.drawnLine({ ok: false, why: "this browser gave no WebGL" }) === "Drawn with: 2D because this browser gave no WebGL" && /compiles/.test(W.drawnLine({ ok: "pending" })));
  // the compile: in the background with the extension, else at the first idle moment after the first paint; never 2D for good
  const ws = fs.readFileSync(path.join(__dirname, '..', 'shared', 'water.js'), 'utf8');
  ok("no parallel-compile extension still compiles, in an idle callback after the first paint", /KHR_parallel_shader_compile/.test(ws) && /requestIdleCallback\(f/.test(ws) && /else idle\(function \(\) \{ if \(GL\.ok !== "pending"\) return; glCompile\(\); glReady\(\); \}\)/.test(ws) && !/if \(!GL\.ext && !noGuard\(\)\) \{ GL\.ok = false/.test(ws));
  ok("the session key stores the reason and the version, and a long press explains it", /sessionStorage\.setItem\(GUARD_KEY, JSON\.stringify\(\{ v: waterVer\(\), why: why \}\)\)/.test(ws) && /"contextmenu"/.test(ws) && /WEBGL_debug_renderer_info/.test(ws) && /render\(v, full \? null[^\n]*, true\)/.test(ws));
  ok("the 2D water uses the tracer's camera: the lip and the base are ellipses seen from above", (() => { const t = W.ell(138, 45), b = W.ell(0, 45); return t.ry > 3 && b.ry > t.ry && Math.abs(t.x - 75) < 1e-9 && t.rx > 40; })());
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
