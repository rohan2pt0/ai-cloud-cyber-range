// v137: box breathing is followed full screen (owner, 2026-11-18; queue visual-guides, slice 1 of 3). The guide's
// breathing card opens one full-screen pacer with the word and the count, so it can be followed on a phone or an iPad
// without reading a small square. Under reduced motion the square stays still. The 1-second timer runs only in a real
// browser (never jsdom, never a driver); this test drives gmBreathe.step() itself. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("guide");
  const cards = [...d.querySelectorAll("#sections .guide-card")];
  const box = cards.find(c => /Box breathing/.test(c.textContent));
  ok("the breathing guide has a card", !!box);
  const starts = box ? [...box.querySelectorAll("button")].filter(b => b.textContent.trim() === "Start breathing") : [];
  ok("the breathing guide card has one Start breathing button", starts.length === 1, starts.length + " buttons");
  const svg = box && box.querySelector("svg");
  ok("the guide keeps its inline square, capped at 360px",
    !!svg && /max-width:360px/.test(svg.getAttribute("style") || ""), svg && svg.getAttribute("style"));

  w.gmBreathe();
  const el = d.getElementById("gmBreathe");
  ok("gmBreathe opens one full-screen dialog", !!el && d.querySelectorAll("#gmBreathe").length === 1);
  ok("the dialog is modal and named", !!el && el.getAttribute("role") === "dialog" && el.getAttribute("aria-modal") === "true" && el.getAttribute("aria-label") === "Box breathing");
  const word = () => (el && el.querySelector(".gm-breathe-word") || {}).textContent;
  const count = () => (el && el.querySelector(".gm-breathe-count") || {}).textContent;
  ok("it starts on Inhale, counting 4", word() === "Inhale" && count() === "4", word() + " " + count());
  const seq = [];
  for (let i = 0; i < 16; i++) { w.gmBreathe.step(); seq.push(word() + count()); }
  ok("step counts 4,3,2,1 through Inhale, Hold, Exhale, Hold",
    seq.slice(0, 4).join(",") === "Inhale3,Inhale2,Inhale1,Hold4" &&
    seq.slice(4, 8).join(",") === "Hold3,Hold2,Hold1,Exhale4" &&
    seq.slice(8, 12).join(",") === "Exhale3,Exhale2,Exhale1,Hold4" &&
    seq.slice(12, 16).join(",") === "Hold3,Hold2,Hold1,Inhale4", seq.join(","));

  const css = (d.getElementById("gmBreatheCss") || {}).textContent || "";
  ok("the square is sized for a phone or an iPad", /min\(78vw,62vh\)/.test(css));
  const fm = /\.gm-breathe-word\{[^}]*font-size:(\d+)px/.exec(css);
  ok("the word is at least 32px", !!fm && +fm[1] >= 32, fm && fm[1]);
  ok("reduced motion keeps the square still", /prefers-reduced-motion:reduce\)\{#gmBreathe \.gm-breathe-square\{[^}]*transform:none/.test(css));

  el.querySelector(".gm-breathe-done").click();
  ok("Done removes the dialog and stops its timer", !d.getElementById("gmBreathe") && w.gmBreathe.timer == null);
  w.gmBreathe();
  d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok("Escape also closes it", !d.getElementById("gmBreathe"));

  console.log("test137 full-screen box breathing: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
