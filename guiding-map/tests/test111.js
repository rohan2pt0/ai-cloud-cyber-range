// v111: colour means what the words mean (owner, 2026-11-15: "after Done, 1.0/1.0, why is it red?"). An OKR grade is
// green from 0.7 (a success by the method's own measure) up to 1.0, amber while in progress, muted at 0; never red or
// amber for a finished key result. The "too safe" advice stays in the quarterly review, where it is explained.
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
  const grade = (v) => { w.eval("S.okrs=[{o:'Fake objective',krs:[{k:'Fake key result',v:" + v + ",at:Date.now()}],at:Date.now()}];store('sovS',S);");
    w.goTab("okr"); const g = d.getElementById("og0"); return g ? g.getAttribute("style") + " | " + g.textContent : "none"; };
  let s = grade(1);
  ok("a finished key result (1.00) is green", /var\(--green\)/.test(s) && /1\.00/.test(s), s);
  s = grade(0.7);
  ok("0.70 is green: a success by the method's own measure", /var\(--green\)/.test(s), s);
  s = grade(0.3);
  ok("0.30 in the middle of a quarter is in progress (amber), never red", /var\(--amber\)/.test(s) && !/var\(--red\)/.test(s), s);
  s = grade(0);
  ok("0.00 is quiet, not a warning", /var\(--muted\)/.test(s), s);
  console.log("test111 colour means what the words mean: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
