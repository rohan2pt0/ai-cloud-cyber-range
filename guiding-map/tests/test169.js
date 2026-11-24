// test169: the full-screen breathing guide has the live sea and a breath sound (owner, 2026-11-24). The sea (shared/sea.js)
// fills the guide behind its square, its swell driven by the guide's own phase; one Sound choice (Off, Sea, Sea + breath) is
// remembered; the breath's envelope is a pure function (inhale rises, hold near silent, exhale longer and softer); no audio
// before a tap; no loop in a test DOM. Sound itself cannot be heard here: the graph is a stub and the envelope is checked as numbers.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000, nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const mm = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
let ctxs = 0, offs = 0, sets = [], ivs = 0, raf = 0;
function FakeParam() { this.value = 0; } ["setValueAtTime", "linearRampToValueAtTime", "setTargetAtTime", "cancelScheduledValues"].forEach(k => { FakeParam.prototype[k] = function () {}; });
function node() { return { connect() {}, disconnect() {}, start() {}, stop() {}, gain: new FakeParam(), frequency: new FakeParam(), Q: new FakeParam(), buffer: null, loop: false, type: "" }; }
function FakeAC() { ctxs++; this.sampleRate = 8000; this.currentTime = 0; this.destination = {}; this.state = "running"; }
FakeAC.prototype.createBuffer = function (c, n) { const a = new Float32Array(n); return { getChannelData() { return a; } }; };
["createGain", "createBufferSource", "createBiquadFilter"].forEach(k => { FakeAC.prototype[k] = node; });
FakeAC.prototype.resume = function () {}; FakeAC.prototype.close = function () { offs++; };
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.AudioContext = FakeAC;
    const si = w.setInterval; w.setInterval = function () { ivs++; return si.apply(w, arguments); };
    const ra = w.requestAnimationFrame; w.requestAnimationFrame = function () { raf++; return ra.apply(w, arguments); }; } });
setTimeout(() => {
  const w = dom.window, d = w.document, S = w.SXSea;
  const ivBefore = ivs, rafBefore = raf, ctxBefore = ctxs;
  ok("no AudioContext exists before anything is tapped", ctxBefore === 0, ctxBefore);
  w.gmBreathe();
  const el = d.getElementById("gmBreathe");
  ok("the guide opens", !!el);
  const sea = el && el.querySelector(".sx-sea");
  ok("the guide holds the sea's wrapper, filling the screen", !!sea && sea.hasAttribute("data-sx-sea") && sea.classList.contains("sx-sea-full") && sea.getAttribute("aria-hidden") === "true");
  ok("the sea's fallback frame is there (an SVG or still frame in a test DOM)", !!(sea && sea.querySelector(".sx-sea-fb")));
  ok("the sea sits behind the square", !!sea && el.firstElementChild === sea);
  ok("the square is a thin gold frame, not a plain block", /\.gm-breathe-square\{[^}]*border:1\.5px solid #f0d696/.test((d.getElementById("gmBreatheCss") || {}).textContent || ""));
  ok("the sea's clock is the guide's own phase", S.clock === w.gmBreathe.clock && w.gmBreathe.clock() === 0, S.clock && S.clock());
  const seq = []; for (let i = 0; i < 6; i++) { w.gmBreathe.step(); seq.push(S.clock()); }
  ok("the clock follows the words and the count: Inhale 3,2,1, then Hold 4,3,2 = 1..6 s", seq.join() === "1,2,3,4,5,6", seq.join());
  const b = S.breath(seq[3]); ok("at the clock's 4 s the sea is at the top of its breath", b.b === 1 && b.word === "Hold");
  // the Sound control
  const seg = el.querySelector("[role=radiogroup][aria-label=Sound]");
  const btns = seg ? [...seg.querySelectorAll("button[role=radio]")] : [];
  ok("a Sound control with Off, Sea and Sea + breath", btns.map(x => x.textContent).join("|") === "Off|Sea|Sea + breath", btns.map(x => x.textContent).join("|"));
  ok("it defaults to Off on first use", btns[0] && btns[0].getAttribute("aria-checked") === "true" && !w.localStorage.getItem("gm_breathe_sound"));
  ok("every choice is at least 44px tall by the shared segmented style", /\.sx-seg button\{min-height:44px/.test(html));
  ok("opening the guide did not create audio", ctxs === 0, ctxs);
  ok("no timer and no frame loop started in a test DOM", ivs === ivBefore && raf === rafBefore && w.gmBreathe.timer == null, (ivs - ivBefore) + " intervals, " + (raf - rafBefore) + " frames");
  btns[1].click();
  ok("a tap on Sea starts the one sound graph", ctxs === 1 && w.gmBreathe.audio && btns[1].getAttribute("aria-checked") === "true" && btns[0].getAttribute("aria-checked") === "false", ctxs);
  ok("the choice is remembered", w.localStorage.getItem("gm_breathe_sound") === "sea");
  btns[2].click();
  ok("Sea + breath retunes the same graph (one engine, never two)", ctxs === 1 && w.localStorage.getItem("gm_breathe_sound") === "both" && btns[2].getAttribute("aria-checked") === "true", ctxs);
  btns[0].click();
  ok("Off stops it", w.gmBreathe.audio == null && w.localStorage.getItem("gm_breathe_sound") === "off");
  btns[2].click(); const g1 = w.gmBreathe.audio; ok("tapping again starts it", !!g1 && ctxs === 2);
  el.querySelector(".gm-breathe-done").click();
  ok("Done stops the sound and closes the guide", !d.getElementById("gmBreathe") && w.gmBreathe.audio == null && S.clock == null);
  // a remembered choice shows on the next open, and still waits for a tap in a test DOM (no user activation here)
  const c0 = ctxs; w.gmBreathe();
  const el2 = d.getElementById("gmBreathe"), b2 = [...el2.querySelectorAll("button[role=radio]")];
  ok("the remembered choice is shown on the next open", b2[2].getAttribute("aria-checked") === "true" && b2[0].getAttribute("aria-checked") === "false");
  ok("but no audio starts without a tap", ctxs === c0, ctxs - c0);
  // a hidden page stops the sound
  b2[1].click(); ok("sound on again", !!w.gmBreathe.audio);
  Object.defineProperty(d, "hidden", { configurable: true, get: () => true }); d.dispatchEvent(new w.Event("visibilitychange"));
  ok("a hidden page stops the sound", w.gmBreathe.audio == null);
  Object.defineProperty(d, "hidden", { configurable: true, get: () => false });
  w.gmBreathe.close();
  ok("the sea is let go on close (nothing runs while closed)", !d.getElementById("gmBreathe") && S.current() == null);
  // the breath's envelope: a pure function of time in the 16 s box
  const E = S.breathEnv, at = (a, z, k) => { const v = []; for (let t = a; t <= z + 1e-9; t += 0.05) v.push(E(t)[k]); return v; };
  const inh = at(0, 3.6, "g"), hold1 = at(4.1, 7.9, "g"), exh = at(8.3, 13.5, "g");
  ok("inhale: the gain rises all the way", inh.every((v, i) => i === 0 || v >= inh[i - 1]) && inh[inh.length - 1] > 0.15 && inh[0] < 0.01, inh[0] + ".." + inh[inh.length - 1]);
  ok("inhale: the pitch rises", at(0, 4, "f").every((v, i, a) => i === 0 || v >= a[i - 1]) && E(4).f > E(0).f + 0.9);
  ok("hold: near silence", Math.max(...hold1) < 0.01 && Math.max(...at(13.6, 15.95, "g")) < 0.01, Math.max(...hold1));
  ok("exhale: the gain falls all the way", exh.every((v, i) => i === 0 || v <= exh[i - 1] + 1e-12) && exh[0] > 0.08 && exh[exh.length - 1] < 0.02);
  ok("exhale: the pitch falls", at(8.3, 13.5, "f").every((v, i, a) => i === 0 || v <= a[i - 1] + 1e-12));
  const peakIn = Math.max(...at(0, 4, "g")), peakEx = Math.max(...at(8, 14, "g"));
  ok("the exhale is softer than the inhale", peakEx < peakIn * 0.75, peakEx + " vs " + peakIn);
  const audible = (a, z) => at(a, z, "g").filter(v => v > 0.01).length * 0.05;
  ok("and longer than the inhale", audible(8, 14) > audible(0, 4) + 0.8, audible(8, 14) + " vs " + audible(0, 4));
  ok("it repeats every 16 s and is defined for negative time", Math.abs(E(2.5).g - E(18.5).g) < 1e-9 && isFinite(E(-3).g) && E(-3).g >= 0);
  ok("the gain never leaves 0 to 0.16", at(0, 16, "g").every(v => v >= 0 && v <= 0.16 + 1e-9));
  // reduced motion: still sea, words and sound still work
  dom.window.matchMedia = q => Object.assign(mm(q), { matches: /reduce/.test(q) });
  w.gmBreathe(); const el3 = d.getElementById("gmBreathe");
  w.gmBreathe.step(); ok("reduced motion: words and count still change, the square stays", el3.querySelector(".gm-breathe-count").textContent === "3" && el3.querySelector(".gm-breathe-square").style.transform === "");
  el3.querySelectorAll("button[role=radio]")[1].click(); ok("reduced motion: sound still works", !!w.gmBreathe.audio);
  w.gmBreathe.close();
  console.log("test169 full-screen sea and breath sound: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
