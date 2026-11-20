// test151: an optional breathing sound in the full-screen box-breathing pacer (owner, 2026-11-20). A "Sound" toggle
// beside Done plays a soft filtered-noise breath with no audio file: rising on the inhale, silent on each hold, falling
// on the exhale, timed to the existing phase timer. The choice is remembered in gm_breath_sound, stopped on Done and
// when the tab is hidden, and nothing happens where Web Audio is absent. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
function fakeAudio() {
  const rec = { contexts: 0, closed: 0, gains: [] };
  function Param() { this.value = 0; }
  Param.prototype.setTargetAtTime = function (v) { this.value = v; };
  function Node() { this.gain = new Param(); this.frequency = new Param(); }
  Node.prototype.connect = function () { return this; };
  Node.prototype.disconnect = function () {};
  function AC() {
    rec.contexts++;
    this.sampleRate = 44100; this.currentTime = 0; this.destination = {};
    this.createBuffer = (ch, len) => ({ getChannelData: () => new Float32Array(len) });
    this.createBufferSource = () => { const n = new Node(); n.start = () => { n.started = true; }; n.stop = () => { n.stopped = true; }; return n; };
    this.createBiquadFilter = () => new Node();
    this.createGain = () => { const n = new Node(); rec.gains.push(n); return n; };
    this.resume = () => Promise.resolve();
    this.close = () => { this.closed = true; rec.closed++; return Promise.resolve(); };
  }
  return { AC, rec };
}
const mk = (audio) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    if (audio) w.AudioContext = audio.AC;
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });

const au = fakeAudio();
const d1 = mk(au);
setTimeout(() => {
  const w = d1.window, d = w.document, ls = w.localStorage;
  const gain = () => w.gmBreathe.audio && w.gmBreathe.audio.gain.gain.value;
  w.gmBreathe();
  let el = d.getElementById("gmBreathe");
  let sbtn = el.querySelector(".gm-breathe-sound");
  ok("the pacer has a Sound button beside Done", !!sbtn && sbtn.textContent.trim() === "Sound" && !!el.querySelector(".gm-breathe-done"));
  ok("Sound starts off, with no sound running", sbtn.getAttribute("aria-pressed") === "false" && w.gmBreathe.audio == null && au.rec.contexts === 0);

  sbtn.click();
  ok("turning Sound on starts the noise and remembers it", w.gmBreathe.audio != null && au.rec.contexts === 1 && ls.getItem("gm_breath_sound") === "1" && sbtn.getAttribute("aria-pressed") === "true");
  const v0 = gain(); w.gmBreathe.step(); const v1 = gain(); w.gmBreathe.step(); w.gmBreathe.step(); const v2 = gain();
  ok("the breath rises through the inhale", v0 > 0 && v0 < v1 && v1 < v2, [v0, v1, v2].join(","));
  w.gmBreathe.step();
  ok("each hold is silent", gain() === 0, gain());
  for (let i = 0; i < 4; i++) w.gmBreathe.step();
  const x0 = gain(); w.gmBreathe.step(); const x1 = gain();
  ok("the exhale falls away", x0 > x1 && x1 > 0, x0 + "->" + x1);

  const gn = au.rec.gains[0];
  sbtn.click();
  ok("turning Sound off silences it and closes the context", w.gmBreathe.audio == null && gn.gain.value === 0 && au.rec.closed >= 1 && ls.getItem("gm_breath_sound") === "0");

  sbtn.click();
  ok("a second on starts a fresh context", w.gmBreathe.audio != null && au.rec.contexts === 2);
  el.querySelector(".gm-breathe-done").click();
  ok("Done stops the sound and closes it", w.gmBreathe.audio == null && au.rec.closed >= 2 && !d.getElementById("gmBreathe"));

  ls.setItem("gm_breath_sound", "1");
  w.gmBreathe();
  el = d.getElementById("gmBreathe");
  ok("a remembered choice starts the sound when the pacer opens", w.gmBreathe.audio != null && el.querySelector(".gm-breathe-sound").getAttribute("aria-pressed") === "true");
  el.querySelector(".gm-breathe-done").click();

  w.gmBreathe();
  el = d.getElementById("gmBreathe");
  ok("the remembered choice keeps the sound on when it reopens", w.gmBreathe.audio != null);
  Object.defineProperty(d, "hidden", { configurable: true, get: () => true });
  d.dispatchEvent(new w.Event("visibilitychange"));
  ok("a hidden tab stops the sound", w.gmBreathe.audio == null);
  el.querySelector(".gm-breathe-done").click();
  ls.setItem("gm_breath_sound", "0");

  const d2 = mk(null);
  setTimeout(() => {
    const w2 = d2.window, d2d = d2.window.document;
    w2.gmBreathe();
    const b = d2d.querySelector(".gm-breathe-sound");
    let threw = false;
    try { b.click(); } catch (x) { threw = true; }
    ok("without Web Audio the toggle does nothing and never throws", !threw && w2.gmBreathe.audio == null && b.getAttribute("aria-pressed") === "true");
    w2.gmBreathe.close();
    console.log("test151 breathing sound: " + P + " passed, " + F + " failed");
    e.forEach(x => console.log("  " + x));
    process.exit(F ? 1 : 0);
  }, 1200);
}, 1200);
