// x3_01: unsaved days, said honestly on Today (owner 2026-11-18; experience-v3, fix 1 of 20). With real data and no
// backup for 8 days or more, Today shows one amber line ("N days of changes live only on this phone") and one button that
// calls the existing backup action. A backup under 8 days old, or example data, hides it; a dismiss hides it for 30 days.
// jsdom sees text, classes and attributes, not pixels: the real-browser audits hold the look. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = [];
const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
function dayAgo(n) {
  const d = new Date(); d.setDate(d.getDate() - n);
  return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
}
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_calm", "true");
    w.localStorage.setItem("gm_first_open", JSON.stringify(dayAgo(20)));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const line = () => d.querySelectorAll(".gm-unsaved");
  const show = () => { try { w.goTab("today"); } catch (x) {} w.renderAll(); };
  const realP = () => { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.P = prof; };

  // 1. Real data, never backed up: the 20 days since the first open are the honest count.
  w.localStorage.removeItem("gm_last_export");
  show();
  let L = line();
  ok("one line when real data has no backup", L.length === 1, L.length + " lines");
  ok("the line names the number of days", !!L[0] && /20 days of changes live only on this phone\./.test(L[0].textContent), L[0] && L[0].textContent);
  const btns = L[0] ? [...L[0].querySelectorAll("button")].filter(b => /Save a copy/.test(b.textContent)) : [];
  ok("one button calls the existing backup action", btns.length === 1 && /gmExportNow/.test(btns[0].getAttribute("onclick") || ""), btns.length && btns[0].getAttribute("onclick"));
  ok("attention is amber, never red", !!L[0] && /--amber/.test(L[0].getAttribute("style") || "") && !/--red/.test(L[0].getAttribute("style") || ""), L[0] && L[0].getAttribute("style"));

  // 2. A backup 9 days old: changes since then live only here.
  w.localStorage.setItem("gm_last_export", JSON.stringify(dayAgo(9)));
  show();
  L = line();
  ok("a backup 9 days old shows 9 days", L.length === 1 && /9 days of changes live only on this phone\./.test(L[0].textContent), L[0] && L[0].textContent);

  // 3. Under 8 days: quiet.
  w.localStorage.setItem("gm_last_export", JSON.stringify(dayAgo(7)));
  show();
  ok("a backup under 8 days old hides the line", line().length === 0, line().length + " lines");

  // 4. Example data is nobody's to lose: never the line, even with an old backup.
  w.localStorage.setItem("gm_last_export", JSON.stringify(dayAgo(9)));
  const ex = Object.assign({}, prof, { example: true });
  w.localStorage.setItem("sovP", JSON.stringify(ex)); w.P = ex;
  show();
  ok("example data never gets the line", line().length === 0, line().length + " lines");
  realP();

  // 5. Dismiss hides it for 30 days, then it comes back.
  show();
  ok("the line returns with real data", line().length === 1);
  w.gmUnsavedDismiss();
  show();
  ok("dismiss hides it", line().length === 0, line().length + " lines");
  w.localStorage.setItem("gm_unsaved_dismiss", JSON.stringify(dayAgo(29)));
  show();
  ok("still hidden on day 29", line().length === 0, line().length + " lines");
  w.localStorage.setItem("gm_unsaved_dismiss", JSON.stringify(dayAgo(30)));
  show();
  ok("shown again after 30 days", line().length === 1, line().length + " lines");

  // 6. The full Today view shows the same single line (never twice).
  w.localStorage.setItem("gm_calm", "false");
  show();
  ok("the full Today view shows it exactly once", line().length === 1, line().length + " lines");

  // 7. Simple mode (the default) keeps it in view instead of folding it away.
  w.localStorage.setItem("gm_calm", "true"); w.localStorage.setItem("gm_simple", "true");
  show();
  L = line();
  ok("simple mode keeps the line in view, not folded", L.length === 1 && !L[0].closest("details"), L.length + " lines");

  console.log("x3_01 unsaved days on Today: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
