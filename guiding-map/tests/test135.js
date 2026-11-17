// test135: the Goals tab asks nothing that changes nothing (owner 2026-11-17; queue owner-frictions-goals-ask, slice 2).
// An objective keeps its strength but shows it as plain words instead of a select that changes no useful thing; the
// pre-mortem is one visible line with one tap that adds three short risk notes, and never adds them twice.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const state = { strengths: ["Discipline", "Curiosity", "Patience"],
  okrs: [{ o: "Make my money unshakeable", s: "Discipline", at: Date.now(),
    krs: [{ t: "Emergency fund from 2 to 4 months by 31 Mar", v: 0, at: Date.now() }] }] };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("sovS", JSON.stringify(state));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("okr");
  const card = () => { const t = d.querySelector('.okr-o'); return t ? t.closest('.okr-card') : null; };
  let c = card();
  ok("the Goals tab shows the objective", !!c, "no objective card");
  ok("no select asks which strength it builds on", d.querySelectorAll('select[aria-label*="Strength"], select[aria-label*="strength"]').length === 0,
    d.querySelectorAll('select').length + " select(s) on the tab");
  ok("the strength is kept", !!w.S && w.S.okrs[0] && w.S.okrs[0].s === "Discipline", w.S && w.S.okrs[0] ? w.S.okrs[0].s : "no state");
  ok("and shown as plain words", !!c && /Builds on/.test(c.textContent) && /Discipline/.test(c.textContent), c ? c.textContent.slice(0, 160) : "no card");
  const det = c && c.querySelector('details');
  ok("the pre-mortem is folded under a details element", !!det && /Pre-mortem/i.test(det.textContent), det ? det.textContent.slice(0, 80) : "no details");
  ok("no pre-mortem paragraph sits unfolded on the page", [...d.querySelectorAll('.info')].filter(x => /Pre-mortem/i.test(x.textContent) && !x.closest('details')).length === 0,
    "an unfolded pre-mortem paragraph is showing");
  const sum = det && det.querySelector('summary');
  ok("one visible line asks what could stop it", !!sum && /What could stop this\?/.test(sum.textContent), sum ? sum.textContent : "no summary");
  const btn = c && c.querySelector('[data-premortem]');
  ok("one button adds the risks", !!btn, btn ? btn.textContent : "no button");
  ok("there is one pre-mortem button per objective", d.querySelectorAll('[data-premortem]').length === 1, d.querySelectorAll('[data-premortem]').length + " buttons");
  if (btn) btn.click();
  c = card();
  const risks = (w.S.okrs[0] && w.S.okrs[0].risks) || [];
  ok("one tap adds three short risk notes", risks.length === 3, JSON.stringify(risks));
  const joined = risks.join(" | ");
  ok("they name timebox slipping, no weekly review and an unclear first step",
    /timebox slipping/i.test(joined) && /weekly review/i.test(joined) && /unclear first step/i.test(joined), joined);
  ok("they are shown on the objective", !!c && (c.textContent.match(/timebox slipping/gi) || []).length === 1, c ? c.textContent.slice(0, 240) : "no card");
  const again = c && c.querySelector('[data-premortem]');
  if (again) again.click();
  c = card();
  ok("a second tap does not add them twice", ((w.S.okrs[0] && w.S.okrs[0].risks) || []).length === 3 && (c ? (c.textContent.match(/timebox slipping/gi) || []).length : 0) === 1,
    JSON.stringify((w.S.okrs[0] && w.S.okrs[0].risks) || []));
  ok("the notes are saved for the next visit", /timebox slipping/i.test(w.localStorage.getItem("sovS") || ""), "not saved");
  console.log("test135 goals ask: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
