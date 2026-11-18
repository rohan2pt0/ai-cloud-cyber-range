// x3_09: late is amber, never red (owner, 2026-11-18; experience-v3 fix 9). A career plan step
// dated last week is written "late" in amber, never "overdue" in red, so a mind that avoids what
// shames it stays. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const ymd = (d) => d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
const notice = new Date(); notice.setDate(notice.getDate() - 21);
const due = new Date(notice.getTime()); due.setDate(due.getDate() + 14);
const career = { cfg: { noticeStart: ymd(notice) } };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("gm_career", JSON.stringify(career));
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("career");
  const title = "Get every offer's CTC breakdown";
  const btn = [...sec().querySelectorAll("button.gm-chk")].find(b => (b.getAttribute("aria-label") || "").includes(title));
  const row = btn && btn.parentElement;
  ok("the late career plan step renders", !!row, "no row with the offer-paper step");
  if (row) {
    ok("it says late", /\blate\b/.test(row.textContent), row.textContent.slice(0, 160));
    ok("it never says overdue", !/overdue/.test(row.textContent), row.textContent.slice(0, 160));
    ok("its date is the one dated last week", row.textContent.includes(ymd(due)), row.textContent.slice(0, 160));
    ok("its date uses amber, not red", /var\(--amber\)/.test(row.innerHTML) && !/var\(--red\)/.test(row.innerHTML), row.innerHTML.slice(0, 200));
  }
  console.log("x3_09 late is amber: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
