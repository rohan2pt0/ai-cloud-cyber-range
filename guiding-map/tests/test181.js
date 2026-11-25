// test181: an overdue paper is shown once, inside "Next for this home" (principle plain-first-everywhere, owner 2026-11-25).
// One let-out home whose agreement started 60 days ago has the tenant details for the police overdue. The paper's title must
// appear exactly once on the Property tab, inside "Next for this home"; the top strip names the next non-paper step (or says
// nothing is due, when the papers are the only thing left); and the separate "papers-open" problem card is gone while the
// engine still returns its fixes. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(); const iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: "1988-03-10", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 200000, kids: [], ret: 60, tsav: 20, example: false, earners: 1, loans: [] };
const flat = { n: "Test flat A", use: "letout", val: "90", rent: "26000", loan: "55.82", rate: "7.75", emi: "50000", out: "0", vac: "0", owner: "me", start: iso(-60), months: "11" };
const PAPER = "Tenant details to the police", count = (s, n) => s.split(n).length - 1;
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const boot = (f, cb) => {
  const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
      w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_props", JSON.stringify([f])); w.localStorage.setItem("gm_facts", JSON.stringify({ state: "MH" }));
      w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
  setTimeout(() => { dom.window.goTab("prop"); dom.window.renderAll(); cb(dom.window, dom.window.document); }, 400);
};
const parts = (d) => {
  const sec = d.getElementById("sections"), ll = [...sec.querySelectorAll(".gm-ll")].filter(b => /Next for this home/.test(b.textContent))[0] || null;
  return { sec, ll, sum: sec.querySelector(".gm-ll-sum") };
};

boot(flat, (w, d) => {
  const { sec, ll, sum } = parts(d);
  ok("fixture: the tenant-details paper is overdue", !!w.gmRemedyCtx(0).policeOpen, w.gmRemedyCtx(0).policeOpen);
  ok("the overdue paper's title appears exactly once on the Property tab", count(sec.innerHTML, PAPER) === 1, count(sec.innerHTML, PAPER));
  ok("that one showing is inside the 'Next for this home' block", !!ll && count(ll.innerHTML, PAPER) === 1, ll ? count(ll.innerHTML, PAPER) : "no block");
  ok("with papers as the only step left, the top strip says nothing is due", !!sum && count(sum.innerHTML, PAPER) === 0 && /nothing due/.test(sum.textContent), sum ? sum.textContent : "no strip");
  ok("the papers-open problem card no longer renders on the Property tab", !sec.querySelector('.gm-pf[data-issue="papers-open"]') && !sec.querySelector('.gm-issue[data-issue="papers-open"]'));
  const rem = w.gmRemedies("papers-open", w.gmRemedyCtx(0));
  ok("gmRemedies('papers-open') still returns its fixes", rem.fixes.length > 0 && rem.fixes.some(f => f.id === "police"), rem.fixes.map(f => f.id).join());

  // a rent row is not a paper: the top strip should name it, never the overdue paper
  boot(Object.assign({}, flat, { rentDay: "1" }), (w2, d2) => {
    const p2 = parts(d2);
    ok("with a rent due, the top strip names the rent, not the paper", !!p2.sum && /Rent for/.test(p2.sum.textContent) && count(p2.sum.innerHTML, PAPER) === 0, p2.sum ? p2.sum.textContent : "no strip");
    ok("the paper is still shown exactly once, inside 'Next for this home'", count(p2.sec.innerHTML, PAPER) === 1 && !!p2.ll && count(p2.ll.innerHTML, PAPER) === 1, count(p2.sec.innerHTML, PAPER));
    console.log("test181 overdue paper shown once: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
  });
});
