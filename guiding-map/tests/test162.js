// test162: polished gold (guiding-map/shared/gold.js, owner 2026-11-23): the net-worth bars are real ingots drawn on one canvas, shaded
// with physically based gold and a studio; the light follows the tilt. jsdom has no canvas, so here we hold the pure shading, the
// fallback to the SVG and the rule that no animation loop starts in tests. Fake data only; no network.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false, mine: { epf: 500000 } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
let rafs = 0, probes = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.HTMLCanvasElement.prototype.getContext = function () { probes++; return null; };   // no 2D canvas: the SVG must stay
    const raf = w.requestAnimationFrame; w.requestAnimationFrame = (f) => { rafs++; return raf ? raf.call(w, f) : 0; }; } });
setTimeout(() => {
  const w = dom.window, d = w.document, G = w.SXGold;
  ok("SXGold exists with stack and shade", !!G && typeof G.stack === "function" && typeof G.shade === "function");
  const r0 = rafs; const host = d.createElement("div"); d.body.appendChild(host);
  const drew = G.stack(host, 4, 8, "₹10 lakh"); G.upgrade(d.body);
  ok("stack says no, and draws nothing, where there is no 2D canvas", drew === false && !host.querySelector("canvas"));
  ok("in jsdom gold.js asks for no animation frame", rafs === r0, rafs - r0);
  host.innerHTML = w.SXWorld.goldBars(4, 8, "₹10 lakh"); G.upgrade(host);
  const s = host.querySelector("svg.sx-bars");
  ok("the SVG fallback stays, with its words, when canvas fails", !!s && s.getAttribute("role") === "img" && /4 gold bars of ₹10 lakh, 4 more to the aim/.test(s.getAttribute("aria-label")) && !host.querySelector("canvas"));
  ok("the SVG carries what the canvas needs to upgrade it", s && s.getAttribute("data-have") === "4" && s.getAttribute("data-want") === "8");
  ok("the app's own card still shows its bars", /sx-bars/.test(w.gmGoldBars(4e6, 8e6)) && /aria-label="4 gold bars of ₹10 lakh, 4 more to the aim"/.test(w.gmGoldBars(4e6, 8e6)));
  ok("the pyramid keeps its 36-bar cap", /36 gold bars of .*, 0 more/.test(w.SXWorld.goldBars(99, 99, "x")));
  ok("the canvas was tried", probes > 0);
  // the shading: gold hue, brightest at the mirror angle
  const view = [0, Math.sin(38 * Math.PI / 180), Math.cos(38 * Math.PI / 180)], L = G.lightDir({ x: 0, y: 0 });
  const half = [view[0] + L[0], view[1] + L[1], view[2] + L[2]], mirror = G.shade(half, view, { x: 0, y: 0 });
  const tilt = (a) => { const l = Math.hypot(half[0] + a, half[1], half[2]); return G.shade([(half[0] + a) / l, half[1] / l, half[2] / l], view, { x: 0, y: 0 }); };
  const off = tilt(.9), lum = c => .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
  ok("the mirror angle is gold: red over green over blue", mirror[0] > mirror[1] && mirror[1] > mirror[2], mirror.join(","));
  ok("a slanted face is still gold, not grey", (() => { const c = tilt(.25); return c[0] > c[1] && c[1] > c[2]; })(), tilt(.25).join(","));
  ok("brighter at the mirror angle than off it", lum(mirror) > lum(off) * 2, lum(mirror).toFixed(0) + " vs " + lum(off).toFixed(0));
  ok("the highlight follows the light: tilt it and the mirror angle moves", Math.abs(G.lightDir({ x: .8, y: 0 })[0] - L[0]) > .2);
  ok("the mirror reads warm gold, bright", mirror[0] >= 200 && mirror[2] < mirror[0], mirror.join(","));
  const gj = fs.readFileSync(path.join(__dirname, '..', 'shared', 'gold.js'), 'utf8');
  ok("a loop is armed only outside tests, and only for what is on screen", /if \(!still\(\)\) register\(inst\)/.test(gj) && /IntersectionObserver/.test(gj));
  console.log("test162 polished gold: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); } process.exit(0);
}, 400);
