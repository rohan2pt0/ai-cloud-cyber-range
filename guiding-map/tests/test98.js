// v98: calm and real, slice 2b (owner, 2026-11-14: "too heavy"; queue calm-and-real part 3). The Menu keeps five items
// in view (All apps, Edit profile, the theme, Install, Report) and folds the three switches under Settings (3); in start
// simple, Today shows one card and the check-in: the five numbers wait inside "More for today", on a phone and on a
// wider screen (no bar along the bottom). Show everything brings both back as they were.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
function boot(phone, simple) {
  return new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.localStorage.setItem("sovP", JSON.stringify(prof));
      if (simple === false) w.localStorage.setItem("gm_simple", "false");
      w.matchMedia = (q) => ({ matches: phone && /max-width/.test(q), media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
}
const doms = [boot(true, true), boot(false, true), boot(true, false), boot(false, false)];
setTimeout(() => {
  const [ps, ws, pf, wf] = doms.map(x => { x.window.goTab("today"); return x.window; });
  // The Menu: five in view and Close; the switches folded.
  ps.gmMenu();
  const dlg = [...ps.document.querySelectorAll("button")].filter(b => /Edit profile/.test(b.textContent))[0];
  const box = dlg && dlg.closest("div[style*='grid']");
  const shown = box ? [...box.children].filter(x => x.tagName === "BUTTON").map(b => b.textContent) : [];
  ok("the Menu shows five items", shown.length === 5 && /All apps/.test(shown[0]) && /Report/.test(shown[4]), shown.join(" | "));
  const more = box && box.querySelector("details.gm-menu-more");
  ok("the three switches are folded under a closed Settings (3)", more && !more.open && /Settings \(3\)/.test(more.querySelector("summary").textContent)
    && more.querySelectorAll("button[role=switch]").length === 3);
  ok("…with their own handlers", more && /gmToggleStill/.test(more.innerHTML) && /gmToggleSmart/.test(more.innerHTML) && /gmToggleFocusShow/.test(more.innerHTML));
  // Simple Today on a phone: no numbers above the check-in; they are inside More for today, and counted.
  function check(w, label) {
    const d = w.document, sec = d.querySelector("#sections .section.active"), v = d.getElementById("gmVitals");
    const d3 = sec && sec.querySelector(".gm-d3"), fold = sec && sec.querySelector("details.gm-simple-more");
    ok(label + ": the numbers are inside More for today", v && fold && fold.contains(v), v ? (v.parentNode.className || v.parentNode.id) : "no vitals");
    ok(label + ": nothing numeric sits before the check-in", d3 && !(v && (v.compareDocumentPosition(d3) & 4) && !fold.contains(v)));
    ok(label + ": no bar along the bottom", !d.querySelector("body > #gmVitals"));
    const n = fold ? +((fold.querySelector("summary").textContent.match(/\((\d+)\)/) || [])[1] || 0) : -1;
    ok(label + ": More for today counts what it holds", fold && n === [...fold.children].filter(x => x.tagName !== "SUMMARY").length, String(n));
  }
  check(ps, "phone");
  check(ws, "wide screen");
  // Show everything: as before.
  const vp = pf.document.getElementById("gmVitals"), d3p = pf.document.querySelector("#sections .gm-d3");
  ok("everything, phone: the numbers are back at the top of Today", vp && !vp.closest(".gm-simple-more") && d3p && (vp.compareDocumentPosition(d3p) & 4));
  ok("everything, wide screen: the bar is back along the bottom", !!wf.document.querySelector("body > #gmVitals"));
  console.log("test98 calm and real slice 2b: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
