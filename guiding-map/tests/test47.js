// v47: 360 audit round 1 (owner, 2026-11-11). (1) Stored XSS: a profile from a restored file or another device carried
// markup in the partner, child, loan and dream fields, and four screens ran it. The profile is cleaned at the one door every
// read and write passes; no tab may hold a planted element. (2) Every restore keeps an undo snapshot, and a backup's own old
// undo slot never overwrites it. (3) No terminal command on Inbox or Ask's first view; one gold action on Ops and Plan.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const X = '<img src=x onerror="window.__xss=1">';
const prof = { name: "Fake" + X, dob: "1990-05-15", country: "India", city: "Faketown" + X, cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000, nw: 2500000,
  pname: "Partner" + X, pdob: "1992-01-10", psal: 1, parents: true, kids: [{ name: "Kid" + X, dob: "2022-03-01" }],
  loans: [{ type: "Loan" + X, remaining: 100000, rate: 9, emi: 5000, tenure: 20 }], ret: 50, tsav: 20, dream: "UAE" + X, goal: "Goal" + X, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.confirm = () => true; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const p = w.eval("P");
  ok("the loaded profile holds no markup", [p.name, p.city, p.pname, p.dream, p.goal, p.kids[0].name, p.loans[0].type].every(v => !/[<>"`]/.test(v)), JSON.stringify(p.pname));
  const bad = [];
  w.eval("TABS").map(t => t[0]).forEach(t => { try { w.goTab(t); } catch (x) {} d.querySelectorAll('#sections details').forEach(x => x.open = true);
    if (d.querySelector('img[onerror], [onerror]')) bad.push(t); });
  try { w.editProfile(); } catch (x) {}
  if (d.querySelector('img[onerror]')) bad.push("setup");
  ok("no tab holds a planted element", bad.length === 0, bad.join(","));
  w.eval('store("sovP", Object.assign({}, P, { pname: "A<b>B" }))');
  ok("a write is cleaned too", JSON.parse(w.localStorage.getItem("sovP")).pname === "AbB");
  // restore keeps an undo snapshot, and the file's own undo slot is ignored
  w.localStorage.setItem("gm_marker", JSON.stringify("before"));
  const src = fs.readFileSync(path.join(__dirname, '..', 'ops.js'), 'utf8');
  ok("every restore path takes an undo snapshot first", (src.match(/gmSnap\("before (moving data in|restoring)/g) || []).length >= 4);
  ok("a backup never carries or restores the undo slot", /k\.indexOf\("gm_undo"\) !== 0\) blob\[k\]/.test(src) && (src.match(/k\.indexOf\("gm_undo"\) !== 0/g) || []).length >= 4);
  // plain words: no terminal command in Inbox or Ask's first view
  ["inbox", "ask"].forEach(t => { w.goTab(t); const vis = [...d.querySelectorAll('#sections *')].filter(el => !el.closest('details:not([open])') || el.closest('summary')).map(el => el.childNodes.length && [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('')).join(' ');
    ok(t + ": no terminal command in view", !/\.\/securax/.test(vis), (vis.match(/.{30}\.\/securax.{20}/) || [""])[0]); });
  // one gold action on Ops and Plan
  ["ops", "plan"].forEach(t => { w.goTab(t);
    const g = [...d.querySelectorAll('#sections button')].filter(b => !b.closest('details:not([open])') && (/gold/.test(b.getAttribute('style') || '') || b.classList.contains('btn-p')));
    ok(t + ": at most one gold or primary button in view", g.length <= 1, g.map(b => b.textContent).join("|")); });
  console.log("test47 360 audit round 1: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
