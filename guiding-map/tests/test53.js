// v53: the tactile feel (human-first). A press is mechanical: raised at rest, it sinks and springs back; a ripple starts
// where the finger lands; a habit tick bounces; a light haptic fires unless the person turned it off. All of it stays
// still under reduced motion, and the choice lives on Ops as one switch.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000, nw: 2500000, kids: [], loans: [] };
const calls = [];
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    Object.defineProperty(w.navigator, "vibrate", { value: ms => calls.push(ms), configurable: true }); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("ops");
  const sec = d.getElementById("sections");
  const btn = sec.querySelector(".btn-sm");
  ok("Ops has a button to press", !!btn);
  calls.length = 0;
  btn.dispatchEvent(new w.PointerEvent("pointerdown", { bubbles: true, clientX: 5, clientY: 5 }));
  ok("a pointerdown adds .gm-ripple to the control", !!btn.querySelector(".gm-ripple"), btn.innerHTML.slice(0, 80));
  ok("…and gives one light haptic (6 ms)", calls.length === 1 && calls[0] === 6, JSON.stringify(calls));
  w.localStorage.setItem("gm_haptics", "false");
  calls.length = 0;
  const btn2 = [...sec.querySelectorAll(".btn-sm")].find(b => b !== btn) || btn;
  btn2.dispatchEvent(new w.PointerEvent("pointerdown", { bubbles: true, clientX: 5, clientY: 5 }));
  ok("with gm_haptics false there is no vibration", calls.length === 0, JSON.stringify(calls));
  const css = [...d.querySelectorAll("style")].map(s => s.textContent).join("\n");
  ok("the stylesheet honours prefers-reduced-motion", /prefers-reduced-motion/.test(css));
  ok("the stylesheet has a :active rule that presses down with translateY", /:active[^{]*\{[^}]*translateY\(2px\)/.test(css));
  w.localStorage.removeItem("gm_haptics"); w.goTab("ops");
  const t = d.getElementById("sections").textContent;
  ok("Ops shows the Haptics switch", /Haptics \(a light tap feel\)/.test(t));
  w.gmToggleHaptics();
  ok("the switch turns haptics off and remembers it", w.localStorage.getItem("gm_haptics") === "false");
  console.log("test53 tactile feel: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
