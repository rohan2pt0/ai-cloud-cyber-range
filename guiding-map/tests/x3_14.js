// x3_14: Today, calm first screen (owner 2026-11-18; experience-v3, fix 14). In the full view with example data the page used to open
// with a help line and an example banner ABOVE the header, then a decade card and a second example warning. Now: the header is the
// first thing on the page, then the greeting, AT MOST ONE notice, then the daily three; every other notice folds under ONE closed
// "Later (n)". jsdom sees order, text and attributes, not pixels: the real-browser audits hold the look. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = [];
const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
function dayAgo(n) {
  const d = new Date(); d.setDate(d.getDate() - n);
  return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
}
const real = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(Object.assign({}, real, { example: true })));
    w.localStorage.setItem("gm_example_fields", JSON.stringify({ gross: 1, net: 1, exp: 1 }));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_calm", "false");
    w.localStorage.setItem("gm_first_open", JSON.stringify(dayAgo(2)));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const show = () => { try { w.goTab("today"); } catch (x) {} w.renderAll(); };
  const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
  show();
  const header = d.querySelector("header");
  ok("the app header exists", !!header);

  // 1. Nothing with text sits before the header in document order (scripts and styles aside).
  const before = [...d.body.querySelectorAll("*")].filter(el => header && (header.compareDocumentPosition(el) & 2) && !(header.compareDocumentPosition(el) & 8)
    && !/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(el.tagName) && !el.closest("a.skip, #wiz") && text(el));  // the off-screen skip link is for keyboards, not a notice
  ok("nothing visible comes before the app header", before.length === 0, before.slice(0, 3).map(x => x.id || x.className || x.tagName).join(","));

  // 2. At most one notice before the daily three.
  const box = d.getElementById("sections");
  const d3 = box.querySelector(".gm-d3");
  ok("the daily three are on Today", !!d3);
  const notices = [...box.querySelectorAll(".gm-notice")];
  const above = notices.filter(n => d3 && (d3.compareDocumentPosition(n) & 2) && !n.closest("details"));
  ok("at most one notice precedes the daily three", above.length === 1, above.length + " notices");
  ok("that one notice is the example line, with one button", above.length === 1 && /Example numbers for now\. Enter yours in two minutes/.test(text(above[0]))
    && above[0].querySelectorAll("button").length === 1 && /Enter my details/.test(above[0].textContent));

  // 3. The example message is said once on the whole page.
  const pageText = () => { const c = d.body.cloneNode(true); c.querySelectorAll("script,style,template,noscript,#wiz").forEach(x => x.remove()); return text(c); };
  const body = pageText();
  const hits = (body.match(/Example (data|numbers)/g) || []).length;
  ok("the example message appears exactly once", hits === 1, hits + " times");
  ok("the second example warning (fields still hold example numbers) is gone", !/still hold example numbers/.test(body));

  // 4. The help line and the decade card sit in one closed Later (n).
  const folds = [...box.querySelectorAll("details")].filter(x => { const s = x.querySelector("summary"); return s && /^Later \(\d+\)$/.test(text(s)); });
  ok("exactly one Later (n) fold", folds.length === 1, folds.length + " folds");
  const f = folds[0];
  ok("the fold is closed", !!f && !f.open);
  ok("the fold sits after the daily three", !!f && !!d3 && (d3.compareDocumentPosition(f) & 4) !== 0);
  ok("the help line is inside the fold", !!f && /Lost\?/.test(text(f)));
  ok("the decade card is inside the fold", !!f && /The Acceleration Decade/.test(text(f)));
  ok("n counts what is folded", !!f && +text(f.querySelector("summary")).match(/\d+/)[0] === f.querySelectorAll(":scope > .gm-notice").length);
  ok("the help line and the decade card are not on the page twice", (body.match(/Lost\?/g) || []).length === 1 && (body.match(/The Acceleration Decade/g) || []).length === 1);

  // 5. A real profile with no other notice: no fold, nothing to fold.
  w.localStorage.setItem("gm_example_fields", "{}");
  w.localStorage.setItem("gm_last_export", JSON.stringify(dayAgo(1)));
  w.localStorage.setItem("sovP", JSON.stringify(real)); w.P = real;
  show();
  const later = [...d.getElementById("sections").querySelectorAll("details")].filter(x => /^Later \(/.test(text(x.querySelector("summary") || x)));
  ok("a real profile with nothing to say shows no Later fold", later.length === 0, later.length + " folds");
  ok("and no notice before the daily three", d.getElementById("sections").querySelectorAll(".gm-notice").length === 0);
  ok("and no help line", !/Lost\?/.test(pageText()));

  console.log("x3_14: PASS " + P + " FAIL " + F);
  if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); }
  process.exit(0);
}, 800);
