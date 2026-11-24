// test167: the breathing sea (guiding-map/shared/sea.js, owner 2026-11-24): the box-breathing pacer is a live sea whose long
// swell rises with the in-breath, holds, falls with the out-breath and holds. Real ocean physics, checked as numbers:
// deep-water dispersion, the Pierson-Moskowitz height, the 4-4-4-4 swell; no loop in a test DOM; the words stay. No network.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
let rafs = 0, ivs = 0, canv = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, S = w.SXSea;
  ok("the sea engine is built in", !!S && typeof S.mount === "function");
  if (!S) return done();
  const g = S.G, T = 16;
  // 1. dispersion: deep water w^2 = g k, so a 16 s swell travels at g T / 2 pi (about 25 m/s), and long waves outrun short ones
  const c16 = S.phaseSpeed(T), want = g * T / (2 * Math.PI);
  ok("a 16 s swell's phase speed is g·T/2π ≈ 25 m/s (within 2%)", Math.abs(c16 - want) / want < 0.02 && Math.abs(c16 - 24.98) < 0.5, c16);
  ok("the breath swell's wavenumber obeys ω² = g·k", Math.abs(Math.pow(2 * Math.PI / T, 2) - g * S.SWELL_K) < 1e-9, S.SWELL_K);
  const W = S.spectrum();
  ok("24 to 48 Gerstner waves", W.length >= 24 && W.length <= 48, W.length);
  ok("every wave obeys ω² = g·k", W.every(x => Math.abs(x.w * x.w - g * x.k) < 1e-9));
  ok("long waves travel faster", W.every((x, i) => i === 0 || x.w / x.k < W[i - 1].w / W[i - 1].k + 1e-12));
  // 2. the spectrum: a gentle breeze (4 to 6 m/s); its significant wave height is the Pierson-Moskowitz value, 0.21 U²/g
  const hs = S.hsOf(W), pm = S.hsPM(S.WIND);
  ok("the wind is a gentle breeze (4 to 6 m/s)", S.WIND >= 4 && S.WIND <= 6, S.WIND);
  ok("Hs of the 40 waves is within 25% of Pierson-Moskowitz", Math.abs(hs - pm) / pm < 0.25, hs.toFixed(3) + " vs " + pm.toFixed(3));
  ok("the spectrum peaks at 0.877 g/U", Math.abs(S.peak(S.WIND) - 0.877 * g / S.WIND) < 0.01);
  ok("the glitter's roughness is the slope the waves leave unresolved (Cox-Munk)", S.slopeVar(W) < S.coxMunk(S.WIND) && S.slopeVar(W) > 0.5 * S.coxMunk(S.WIND));
  let foam = 0; for (let i = 0; i < 4000; i++) if (S.jacobian(W, (i * 37.1) % 200, (i * 91.7) % 200, i * 0.13) < 0.45) foam++;
  ok("foam only on the steepest crests (under 1% of the surface)", foam / 4000 < 0.01, foam);
  // 3. the swell follows the box breath at the viewer: rises in 0-4 s, holds 4-8, falls 8-12, holds 12-16; eased, never jerky
  const h = t => S.swellAt(0, 0, t), seg = (a, b) => { const v = []; for (let t = a; t <= b + 1e-9; t += 0.1) v.push(h(t)); return v; };
  const up = seg(0.05, 3.95), hold = seg(4.05, 7.95), down = seg(8.05, 11.95), rest = seg(12.05, 15.95);
  ok("it rises during the in-breath", up.every((v, i) => i === 0 || v > up[i - 1]) && h(4) - h(0) > 1.1, h(4) - h(0));
  ok("it holds level at the top", Math.max(...hold) - Math.min(...hold) < 1e-9);
  ok("it falls during the out-breath", down.every((v, i) => i === 0 || v < down[i - 1]) && h(8) - h(12) > 1.1);
  ok("it holds level at the bottom", Math.max(...rest) - Math.min(...rest) < 1e-9);
  ok("eased: it starts and ends each move gently", Math.abs(h(0.1) - h(0)) < 0.01 && Math.abs(h(4) - h(3.9)) < 0.01 && Math.abs(h(8.1) - h(8)) < 0.01);
  ok("one swell = one breath: the phase moves 2π a breath (true mean speed)", Math.abs(S.swellPhase(32) - S.swellPhase(16) - 2 * Math.PI) < 1e-9);
  // 4. the words
  const words = [1, 5, 9, 13].map(t => S.breath(t).word);
  ok("the pacer says Breathe in, Hold, Breathe out, Hold", words.join("|") === "Breathe in|Hold|Breathe out|Hold", words.join("|"));
  ok("it counts 4, 3, 2, 1", [0, 1, 2, 3].map(t => S.breath(t).count).join("") === "4321");
  // 5. the Life OS: the guide holds the sea, the words and the SVG pacer as the last fallback; no loop, no canvas in jsdom
  w.goTab("guide"); w.renderAll && w.renderAll();
  const sea = d.querySelector("[data-sx-sea]");
  ok("the breathing guide holds the sea", !!sea && /Box breathing with the sea/.test(sea.getAttribute("aria-label") || ""));
  ok("it says Breathe in, large, and the SVG says every phase", sea && sea.querySelector(".sx-sea-word").textContent === "Breathe in"
    && /Breathe in 4s/.test(sea.textContent) && /Hold 4s/.test(sea.textContent) && /Breathe out 4s/.test(sea.textContent));
  ok("the SVG dot pacer stays inside as the last fallback", !!(sea && sea.querySelector(".sx-sea-fb svg animateMotion")));
  ok("the sound is off by default and one tap away", !!(sea && sea.querySelector(".sx-sea-snd[aria-pressed=false][hidden]")));
  const raf = w.requestAnimationFrame, si = w.setInterval, cr = d.createElement.bind(d);
  w.requestAnimationFrame = (f) => { rafs++; return raf ? raf.call(w, f) : 0; };
  w.setInterval = (...a) => { ivs++; return si.apply(w, a); };
  d.createElement = (n, o) => { if (String(n).toLowerCase() === "canvas") canv++; return cr(n, o); };
  const det = sea && sea.closest("details"); if (det) det.open = true;
  const hd = S.mount(sea);
  ok("no loop and no canvas start in jsdom (the SVG stays)", rafs === 0 && ivs === 0 && canv === 0 && hd.mode === "svg" && !sea.classList.contains("sx-sea-on"), [rafs, ivs, canv, hd.mode].join());
  hd.stop();
  // 6. one meaning in the shared world, one signature
  ok("the sea is in the world's catalog: calm and the breath, never money or alarms", w.SXWorld.CATALOG.some(c => c.id === "sea" && /breath/.test(c.means) && /money/.test(c.avoid) && /alarm/.test(c.avoid)));
  const sig = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'governance', 'signatures.json'), 'utf8'));
  ok("registered as the breath-sea signature", sig.features.some(f => f.id === "breath-sea" && f.where.includes("guiding-map/shared/sea.js") && f.proof.includes("guiding-map/tests/test167.js")));
  done();
  function done() { console.log("test167 breathing sea: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); } process.exit(0); }
}, 400);
