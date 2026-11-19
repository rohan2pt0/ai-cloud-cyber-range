// test149: numbers asked once (owner 2026-11-19, screenshots: "the buffer won't show, it still says never updated, I am
// filling numbers again and again"). Buffer uses the profile's spending + EMIs when no fixed cost was typed; a number typed
// in any card stamps the date and the take-home flows back to the profile. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000, sav: 500000,
  nw: 1500000, kids: [], loans: [{ name: "Fake loan", remaining: 1000000, emi: 56000 }], ret: 50, tsav: 20, example: false };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false");
    w.localStorage.setItem("gm_mine_done", "true"); w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
    w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("today"); w.renderAll();
  const tile = [...d.querySelectorAll("#gmVitals > div")].find(t => /Buffer|Runway/.test(t.textContent));
  // 5,00,000 / (80,000 + 56,000) = 3.7 months
  ok("Buffer shows months from the profile's spending + EMIs, not a dash", !!tile && /3\.7m/.test(tile.textContent), tile && tile.textContent);
  ok("the card says not updated before anything is typed", /not updated since set-up/.test(w.gmNumbersCard()));
  w.gmLifeSet("minc", "160000");
  const sp = JSON.parse(w.localStorage.getItem("sovP"));
  ok("take-home typed in the plan becomes the profile's take-home", sp.net === 160000, sp.net);
  ok("typing it in another card stamps the date", /updated today/.test(w.gmNumbersCard()), w.gmNumbersCard().slice(0, 200));
  w.gmNumSet("net", "170000");
  const l = JSON.parse(w.localStorage.getItem("gm_life") || "{}");
  ok("changing take-home in My numbers clears the plan's older copy", l.minc === undefined || l.minc === "170000", l.minc);
  // asked once (owner 2026-11-19: "remove the repeated fields, this is really confusing")
  w.localStorage.setItem("gm_life", JSON.stringify({ fFixed: "100000", minc: "90000", nw: "3", ef: "1", inc: "9", age: "20" }));   // old typed copies
  w.renderAll();
  const t2 = [...d.querySelectorAll("#gmVitals > div")].find(t => /Buffer|Runway/.test(t.textContent));
  ok("an old typed fixed cost no longer competes with the profile", !!t2 && /3\.7m/.test(t2.textContent), t2 && t2.textContent);
  w.goTab("life"); w.renderAll();
  const sec = d.querySelector("#sections .section.active") || d.body;
  const inputs = [...sec.querySelectorAll("input")].filter(i => /gmLifeSet\('(minc|fFixed|nw|ef|inc|age|sage|k1)'/.test(i.getAttribute("onchange") || ""));
  ok("Your numbers and Edit the numbers ask none of the profile's facts again", inputs.length === 0, inputs.map(i => i.getAttribute("onchange")).join(" | "));
  ok("each shows as one line with a change link to My numbers", sec.querySelectorAll(".gm-fromp [onclick*=gmOpenNums]").length >= 3, sec.querySelectorAll(".gm-fromp").length);
  ok("My numbers is the one card with inputs for them", !!sec.querySelector("details.gm-nums input"));
  ok("no Spouse wording", !/Spouse age/.test(sec.textContent));
  console.log("test149 numbers once: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x));
  process.exit(F ? 1 : 0);
}, 1500);
