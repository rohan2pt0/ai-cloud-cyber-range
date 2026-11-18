// v3 fix 19: the More sheet is a dialog (owner, 2026-11-18). Opening More announces a dialog with a name, puts focus on
// its first button, and closing it hands focus back to the More button in the bottom bar. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    Object.defineProperty(w, "innerWidth", { configurable: true, value: 390 });
    Object.defineProperty(w, "innerHeight", { configurable: true, value: 844 });
    w.matchMedia = (q) => ({ matches: /max-width:\s*700px/.test(q), media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  // jsdom does not apply the phone-only @media rule, so make the sheet visible the way a phone would.
  const vis = d.createElement("style"); vis.textContent = "#gmMoreSheet.on{display:block!important}#gmNav{display:flex!important}"; d.head.appendChild(vis);
  const sheet = () => d.getElementById("gmMoreSheet");
  const moreBtn = () => Array.from(d.querySelectorAll("#gmNav button")).find(b => (b.textContent || "").trim() === "More");

  w.gmNavMore(true);
  const sh = sheet();
  ok("opening More shows the sheet", !!sh && sh.className.indexOf("on") > -1);
  ok("the sheet is a dialog", !!sh && sh.getAttribute("role") === "dialog", sh ? sh.getAttribute("role") : "no sheet");
  ok("the dialog says it is modal", !!sh && sh.getAttribute("aria-modal") === "true", sh ? sh.getAttribute("aria-modal") : "no sheet");
  ok("the dialog has a name", !!sh && !!(sh.getAttribute("aria-label") || "").trim(), sh ? sh.getAttribute("aria-label") : "no sheet");
  const first = sh && sh.querySelector(".sh button");
  ok("focus sits on the sheet's first button", !!first && d.activeElement === first,
    sh ? (d.activeElement ? d.activeElement.tagName + "." + d.activeElement.className : "nothing focused") : "no sheet");

  w.gmNavMore(false);
  ok("closing More closes the sheet", !sheet() || sheet().className.indexOf("on") < 0);
  ok("closing More returns focus to the More button in the bar", d.activeElement === moreBtn(),
    d.activeElement ? d.activeElement.tagName + "." + d.activeElement.className : "nothing focused");

  console.log("x3_19 More as a dialog: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
