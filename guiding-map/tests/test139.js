// v139: the strength guide reads like a one-page workout card (queue visual-guides, slice 3 of 3). Five exercise cards
// in order, each with a number badge, a gold dose chip, its moving figure, 2-4 "How to do" bullets and one "Easier:"
// line; one glance line above and one flow strip below; the cards stack on a phone and sit in a wrapping row from
// 900 px. Fake data only.
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
  const w = dom.window, d = w.document, css = () => [...d.querySelectorAll("style")].map(x => x.textContent || "").join("\n");
  w.goTab("guide");
  const card = [...d.querySelectorAll(".guide-card")].find(c => /30-min strength/.test(c.textContent));
  ok("the strength guide is on the Guides tab", !!card);
  if (card) {
    const glance = [...card.querySelectorAll(".gs-meta")].map(x => x.textContent.trim());
    ok("one glance line sits above the cards",
      glance.length === 1 && glance[0] === "5 exercises \u00b7 3 rounds \u00b7 rest 45\u201360 s \u00b7 about 25 min",
      JSON.stringify(glance));
    const cards = [...card.querySelectorAll(".gs-card")];
    ok("the guide shows five exercise cards", cards.length === 5, cards.length + " cards");
    const names = cards.map(c => { const x = c.querySelector(".gs-name"); return x ? x.textContent.replace(/\?$/, "").trim() : ""; });
    ok("the cards are in order: Push-ups, Band rows, Squats, Band press, Plank",
      names.join("|") === "Push-ups|Band rows|Squats|Band press|Plank", names.join("|"));
    const want = ["3 sets \u00d7 12", "3 sets \u00d7 12", "3 sets \u00d7 15", "3 sets \u00d7 12", "3 \u00d7 45 s"];
    cards.forEach((c, i) => {
      const n = c.querySelector(".gs-num"), dose = c.querySelector(".gs-dose");
      ok("card " + (i + 1) + " has its number badge", !!n && n.textContent.trim() === String(i + 1), n && n.textContent.trim());
      ok("card " + (i + 1) + " has its dose chip", !!dose && dose.textContent.trim() === want[i], dose && dose.textContent.trim());
      ok("card " + (i + 1) + " shows its figure", c.querySelectorAll("svg[role='img']").length === 1, c.querySelectorAll("svg[role='img']").length + " figures");
      const how = [...c.querySelectorAll(".gs-how li")];
      ok("card " + (i + 1) + " has 2 to 4 How to do bullets", how.length >= 2 && how.length <= 4 && how.every(x => x.textContent.trim().length > 3), how.length + " bullets");
      const easy = [...c.querySelectorAll(".gs-easier")];
      ok("card " + (i + 1) + " has one Easier line", easy.length === 1 && /^Easier:/.test(easy[0].textContent.trim()), easy.length + " lines");
    });
    const flow = [...card.querySelectorAll(".gs-flow")].map(x => x.textContent.replace(/\s+/g, " ").trim());
    ok("one flow strip runs 1 to 5 and says Repeat x3",
      flow.length === 1 && /1 \u2192 2 \u2192 3 \u2192 4 \u2192 5/.test(flow[0]) && /Repeat \u00d73/.test(flow[0]), JSON.stringify(flow));
  }
  ok("the cards stack on a narrow screen", /\.gs-cards\{[^}]*grid-template-columns:1fr/.test(css()));
  ok("from 900 px the cards sit in a row that wraps", /@media \(min-width:900px\)\{\.gs-cards\{[^}]*grid-template-columns:repeat\(auto-fit,minmax/.test(css()));
  ok("the number badge is gold", /\.gs-num\{[^}]*var\(--gold\)/.test(css()));
  console.log("test139 strength workout cards: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
