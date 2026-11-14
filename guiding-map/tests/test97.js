// test97: the lock's aurora is rendered at device resolution with smooth vertical gradients, not stacked bands.
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const src = fs.readFileSync(path.join(__dirname, "..", "shared", "sky.js"), "utf8");
const dom = new JSDOM("<!doctype html><html><body></body></html>", { runScripts: "outside-only", pretendToBeVisual: true, url: "https://localhost/" });
const w = dom.window, doc = w.document;
w.devicePixelRatio = 2;
const calls = new Map();
function ctxFor(cv) {
  let c = calls.get(cv);
  if (!c) {
    c = { canvas: cv, linear: [], radial: [], rects: [], filters: [] };
    c.addColorStop = function (g) { return function (off, col) { g.stops.push([off, col]); }; };
    ["scale", "setTransform", "clearRect", "drawImage", "beginPath", "arc", "fill", "moveTo", "lineTo", "quadraticCurveTo", "stroke", "save", "restore", "translate", "rotate", "closePath"].forEach((k) => { c[k] = function () {}; });
    c.createLinearGradient = function () { const g = { stops: [] }; g.addColorStop = c.addColorStop(g); c.linear.push(g); return g; };
    c.createRadialGradient = function () { const g = { stops: [] }; g.addColorStop = c.addColorStop(g); c.radial.push(g); return g; };
    c.fillRect = function (x, y, ww, hh) { c.rects.push([x, y, ww, hh]); };
    Object.defineProperty(c, "filter", { set(v) { c.filters.push(v); }, get() { return ""; } });
    calls.set(cv, c);
  }
  return c;
}
w.HTMLCanvasElement.prototype.getContext = function () { return ctxFor(this); };
w.eval(src);
function mountSky(width, height) {
  const el = doc.createElement("div");
  el.getBoundingClientRect = () => ({ width: width, height: height, top: 0, left: 0, right: width, bottom: height });
  doc.body.appendChild(el);
  const h = w.SXSky.mount(el, { aurora: true, galaxy: false, comet: false, seed: 1 });
  const aurora = Array.from(calls.values()).filter((c) => c.canvas.tagName === "CANVAS" && !(c.canvas.width === width * 2 && c.canvas.height === height * 2));
  return { h: h, aurora: aurora[aurora.length - 1] };
}
try {
  const a = mountSky(800, 600);
  ok(!!a.aurora, "the aurora canvas is sized at device resolution (not the CSS half-width)");
  if (a.aurora) {
    ok(a.aurora.canvas.width === 800 && a.aurora.canvas.height === 504, "canvas is " + a.aurora.canvas.width + "x" + a.aurora.canvas.height + ", expected 800x504 at DPR 2");
    const g = a.aurora.linear;
    ok(g.length >= 2, "one gradient per column strip and curtain: " + g.length);
    ok(g.length > 0 && g.every((x) => x.stops.length >= 6), "every gradient has at least 6 smooth stops: " + (g[0] ? g[0].stops.length : 0));
    const all = g.map((x) => x.stops.map((s) => s[1]).join(" ")).join(" ");
    ok(/120,255,170/.test(all), "oxygen green 557.7 nm is present");
    ok(/255,90,70/.test(all), "faint oxygen red is present at the top");
    ok(/90,40,255/.test(all), "nitrogen violet is present at the base");
    const byX = {};
    a.aurora.rects.forEach((r) => { byX[r[0]] = (byX[r[0]] || 0) + 1; });
    const worst = Math.max(0, ...Object.values(byX));
    ok(worst <= 2, "no 12 stacked bands per column: at most " + worst + " fills per strip, one per curtain");
    ok(a.aurora.rects.length > 0 && a.aurora.rects.every((r) => r[2] <= 2), "each strip is at most 2 device px wide");
    const main = ctxFor(doc.querySelector(".sx-sky-cv"));
    ok(main.filters.indexOf("blur(4.8px)") > -1, "the blur scales with DPR: " + main.filters.join(","));
  }
  a.h.stop();
  const big = mountSky(4000, 3000);
  ok(!!big.aurora, "a large screen still draws the aurora");
  if (big.aurora) {
    ok(big.aurora.canvas.width * big.aurora.canvas.height <= 1200000, "the cache is capped at 1.2 million pixels: " + (big.aurora.canvas.width * big.aurora.canvas.height));
  }
  big.h.stop();
} catch (e) { fail++; console.log("FAIL threw " + e.stack); }
console.log("test97 aurora render: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
