// v59: the Scorecard, Plan and Growth tabs open with one calm hero and fold their explanation away, like the rest of
// the Life OS. Plan's suggestion pills no longer shout an abbreviation such as "OPT"; they say "Optional" calmly.
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
  const beforeFirstCard = (hero, firstCard) => hero && firstCard && !!(hero.compareDocumentPosition(firstCard) & w.Node.DOCUMENT_POSITION_FOLLOWING);
  const heroCheck = (tab, meaning) => {
    w.goTab(tab);
    const heroes = sec().querySelectorAll(".gm-hero");
    const hero = heroes[0];
    const first = sec().querySelector(".kc, .card, .okr-card");
    ok(tab + " opens with exactly one hero", heroes.length === 1, heroes.length);
    ok(tab + " hero comes before the first card", beforeFirstCard(hero, first));
    ok(tab + " hero says why it matters", hero && hero.textContent.includes(meaning), hero && hero.textContent);
    const hows = sec().querySelectorAll("details.gm-how");
    ok(tab + " folds its explanation under one closed How", hows.length === 1 && !hows[0].open, hows.length);
  };
  heroCheck("score", "Your overall score across the four perspectives");
  heroCheck("plan", "Goals for this quarter");
  heroCheck("growth", "Where you are heading in 12 months");
  // fewer than 3 goals: the hero carries one button to add a goal
  w.goTab("plan");
  const add = [...sec().querySelectorAll(".gm-hero button")];
  ok("Plan offers one button to add a goal when fewer than 3 are set", add.length === 1 && /add a goal/i.test(add[0].textContent), add.map(b => b.textContent).join("|"));
  // no shouted abbreviation such as OPT in a pill on Plan
  const pillText = [...sec().querySelectorAll(".pill, .cb, .badges")].map(x => x.textContent.trim());
  ok("Plan has no standalone OPT pill", !pillText.some(t => t === "OPT" || /\bOPT\b/.test(t)), pillText.join("|"));
  ok("Plan's suggestions say Optional calmly", [...sec().querySelectorAll(".gm-status")].some(x => /Optional/.test(x.textContent)));
  console.log("test59 calm heroes on score, plan and growth: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
