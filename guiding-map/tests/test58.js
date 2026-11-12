// v58: Life OS visual standard, slice 2. Life Map, Money and Career open with one calm hero tile,
// the explanation is folded under "How this works", and no status is shouted in capitals.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  const checkTab = (id, label) => {
    w.goTab(id);
    const s = sec().querySelector(".section.active");
    const hero = s.querySelector(".gm-hero");
    ok(label + ": exactly one hero tile", s.querySelectorAll(".gm-hero").length === 1);
    ok(label + ": the hero opens the tab, before its first card", !!hero && s.firstElementChild === hero, s.firstElementChild && s.firstElementChild.className);
    const how = s.querySelector("details.gm-how");
    ok(label + ": the explanation is folded, closed, under How this works", !!how && !how.open && /How this works/.test(how.querySelector("summary").textContent));
    ok(label + ": no 'most-validated' credential pill", !/most-validated/i.test(s.textContent));
    ok(label + ": no status is shouted in capitals", !/\b(CATCHING UP|AHEAD)\b/.test(s.textContent), s.textContent.slice(0, 200));
  };
  checkTab("life", "Life Map");
  checkTab("money", "Money");
  checkTab("career", "Career");

  w.goTab("life");
  const life = sec().querySelector(".section.active");
  ok("Life Map: the hero means the age benchmark", /Of the net-worth benchmark for your age/.test(life.textContent));
  ok("Life Map: the hero shows a percent", /%/.test((life.querySelector(".gm-hero-u") || {}).textContent || ""));

  w.goTab("money");
  const money = sec().querySelector(".section.active");
  ok("Money: the hero means the person's step", /Your step in the money sequence/.test(money.textContent));
  ok("Money: the hero counts the steps", /of 7/.test((money.querySelector(".gm-hero-u") || {}).textContent || ""), (money.querySelector(".gm-hero-u") || {}).textContent);
  ok("Money: a button leads to the current step", !!money.querySelector(".gm-hero-b button"));

  w.goTab("career");
  const career = sec().querySelector(".section.active");
  ok("Career: the hero means the honest monthly package", /Your honest monthly package/.test(career.textContent));

  console.log("test58 calm life map, money and career: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
