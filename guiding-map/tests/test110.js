// v110: ambient light in dark (owner, 2026-11-15: "like a luxury car at night, calm light on every button"). In dark the
// primary is an obsidian control with a champagne rim, never an ivory slab; ambient light adds a light line, a halo, lit
// hairlines, a light strip on the bottom bar and lit fields, and has an off switch in Menu, Settings. A bare small button
// never shows the browser's grey in either theme. The Map's label pills become a gold eyebrow (they clipped "QUARTERLY"
// and were gold on gold), and the materials engine no longer paints them. jsdom sees the stylesheet text, not the
// rendered colours: the real-browser audits (ui_audit, the dark sweep) hold the look. Fake data only.
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
const mat = fs.readFileSync(path.join(__dirname, '..', 'shared', 'materials.js'), 'utf8');
setTimeout(() => {
  const w = dom.window, d = w.document, css = () => (d.getElementById("gmPremiumCss") || {}).textContent || "";
  ok("the dark primary is obsidian with a champagne rim, not var(--text)",
    /html\[data-theme=dark\] \.btn-p[^{]*\{background:linear-gradient\(180deg,#2c2925,#1c1a18\)!important;color:#f3e2b8/.test(css()));
  ok("ambient light gives the primary a halo", /html\[data-theme=dark\]:not\(\.gm-amb-off\) \.btn-p[^{]*\{box-shadow:[^}]*0 0 22px rgba\(233,201,138,\.26\)/.test(css()));
  ok("the bottom bar carries a light strip", /:not\(\.gm-amb-off\) #gmNav::before\{content:''/.test(css()));
  ok("fields light up while typing", /:not\(\.gm-amb-off\) #sections input[^{]*:focus[^{]*\{border-color:rgba\(233,201,138,\.68\)/.test(css()));
  ok("a bare small button never shows the browser grey", /\.btn-sm:not\(\[style\*=background\]\):not\(\.btn-p\)\{background:transparent!important/.test(css()));
  ok("reduced motion removes the press glow", /prefers-reduced-motion:reduce\)\{[^}]*gm-amb-off[^}]*\{transition:none!important\}/.test(css()));
  ok("ambient light is on by default", !d.documentElement.classList.contains("gm-amb-off"));
  w.gmToggleAmbient();
  ok("the switch turns it off (and remembers)", d.documentElement.classList.contains("gm-amb-off") && w.localStorage.getItem("gm_ambient") === "false");
  const menu = d.body.innerHTML;
  ok("Settings shows the switch and counts five", /Ambient light in dark: off/.test(menu) && /Settings \(5\)/.test(menu));
  w.gmToggleAmbient();
  ok("and on again", !d.documentElement.classList.contains("gm-amb-off"));
  ok("the materials engine no longer paints the Map labels", mat.indexOf('".stk-k"') < 0);
  ok("a chosen chip skips the small gold surface in dark", /dark && sel === "\.chip\.on"/.test(mat));
  w.goTab("map");
  const k = [...d.querySelectorAll("#sections .stk-k")];
  ok("the Map labels render", k.length >= 7, k.length + " labels");
  ok("each label sits above its title as one line (the row is a block, not a 64 px column)",
    k.length && k.every(x => w.getComputedStyle(x.parentElement).display === "block" && w.getComputedStyle(x).display === "block"),
    k[0] && w.getComputedStyle(k[0].parentElement).display);
  console.log("test110 ambient light and Map labels: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
