// v60: the Playbook, OKRs, Commit, Health Cal, Kids and Archive tabs open with one calm hero, fold their
// explanation away, and drop the credential pills that used to sit beside their headings.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dkey = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
const today = new Date(), yesterday = new Date(); yesterday.setDate(today.getDate() - 1);
const state = { okrs: [{ o: "Fake objective", at: Date.now(), krs: [{ t: "from 1 to 10 by 31 Dec", b: 1, g: 10, c: 8 }] }],
  commits: [], archived: ["k:checkups"], daily: { [dkey(today)]: ["ex"], [dkey(yesterday)]: ["ex"] } };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("sovS", JSON.stringify(state));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  const heroCheck = (tab, meaning) => {
    w.goTab(tab);
    const s = sec().querySelector(".section.active");
    const hero = s.querySelector(".gm-hero");
    ok(tab + ": exactly one hero tile", s.querySelectorAll(".gm-hero").length === 1);
    ok(tab + ": the hero opens the tab, before its first card", !!hero && s.firstElementChild === hero, s.firstElementChild && s.firstElementChild.className);
    ok(tab + ": the hero means why it matters", !!hero && hero.textContent.replace(/\?/g, "").includes(meaning), hero && hero.textContent);
    ok(tab + ": the hero never shows NaN or undefined", !!hero && !/NaN|undefined/.test(hero.textContent), hero && hero.textContent);
    const how = s.querySelector("details.gm-how");
    ok(tab + ": the explanation is folded, closed, under How this works", !!how && !how.open && /How this works/.test(how.querySelector("summary").textContent));
  };
  heroCheck("book", "Plays you have run");
  heroCheck("okr", "Key results on track this quarter");
  heroCheck("commit", "Days in a row you kept your word");
  heroCheck("cal", "Next check-up");
  heroCheck("kids", "Children with a plan");
  heroCheck("arch", "Items put away, one tap to bring back");

  w.goTab("book");
  const book = sec().querySelector(".section.active");
  ok("Playbook: the hero counts the stages cleared", book.querySelector(".gm-hero-n").textContent === "0" && /5/.test(book.querySelector(".gm-hero-u").textContent), book.querySelector(".gm-hero").textContent);
  ok("Playbook: the current stage bar is the calm gradient, not navy", /linear-gradient\(90deg,var\(--teal\)/.test(book.innerHTML));
  ok("Playbook: no credential pill beside the heading", !/dynamic/i.test([...book.querySelectorAll(".pill,.badges,.cb")].map(x => x.textContent).join("|")));

  w.goTab("okr");
  const okr = sec().querySelector(".section.active");
  ok("OKRs: the hero counts the results on track", okr.querySelector(".gm-hero-n").textContent === "1" && /1/.test(okr.querySelector(".gm-hero-u").textContent), okr.querySelector(".gm-hero").textContent);
  ok("OKRs: no method-credential pill", !/Doerr|Intel\/Google/.test([...okr.querySelectorAll(".pill,.badges,.cb")].map(x => x.textContent).join("|")));

  w.goTab("commit");
  const commit = sec().querySelector(".section.active");
  ok("Commit: the hero shows the streak in days", commit.querySelector(".gm-hero-n").textContent === "2" && /days/i.test(commit.querySelector(".gm-hero-u").textContent), commit.querySelector(".gm-hero").textContent);
  ok("Commit: no success-statistic pill", !/78%/.test([...commit.querySelectorAll(".pill,.badges,.cb")].map(x => x.textContent).join("|")));

  w.goTab("arch");
  ok("Archive: the hero counts the items put away", sec().querySelector(".section.active .gm-hero-n").textContent === "1");

  w.P.kids = [];
  w.goTab("kids");
  const kids = sec().querySelector(".section.active");
  ok("Kids: no children shows zero", kids.querySelector(".gm-hero-n").textContent === "0");
  const add = [...kids.querySelectorAll(".gm-hero button")];
  ok("Kids: one button opens the profile to add a child", add.length === 1 && /editProfile/.test(add[0].getAttribute("onclick")), add.map(b => b.getAttribute("onclick")).join("|"));

  console.log("test60 calm heroes on playbook, okrs, commit, cal, kids and archive: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
