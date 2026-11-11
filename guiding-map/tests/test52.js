// v52: the Pillars cards tell the truth (calm, human-first). A card the person never filled shows a dash and
// "Tap to add yours", never an invented number; units are plain words; labels no longer collide; the legend says
// "the vital few". The seed is fake and S.vals is empty.
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
  const card = (label) => [...d.querySelectorAll(".kc")].find(c => { const l = c.querySelector(".kl"); return l && l.textContent === label; });
  w.goTab("all");
  ok("S.vals starts empty (the person entered nothing)", w.eval("Object.keys(S.vals).length") === 0, JSON.stringify(w.eval("S.vals")));
  ok("no card shows the old pill words", !/Start Here|START HERE/.test(sec().textContent));
  const sleep = card("Sleep Quality");
  ok("the sleep card exists", !!sleep);
  ok("an unfilled card shows a dash, not an invented number", sleep && sleep.querySelector(".kv").textContent.indexOf("\u2014") >= 0 && !/\b6\b/.test(sleep.querySelector(".kv").textContent), sleep && sleep.querySelector(".kv").textContent);
  ok("an unfilled card invites the person to add their own", sleep && /Tap to add yours/.test(sleep.textContent));
  ok("an unfilled card carries no red status class", sleep && !/\bbehind\b/.test(sleep.className), sleep && sleep.className);
  const pill = sleep && sleep.querySelector(".ptrack .pfill");
  ok("an unfilled card has an empty progress bar", pill && /width:\s*0%/.test(pill.getAttribute("style")), pill && pill.getAttribute("style"));
  w.eval("S.vals.sleep=7; store('sovS',S); renderAll();");
  const sleep2 = card("Sleep Quality");
  ok("once the person adds 7, the card shows 7", sleep2 && /(^|\D)7(\D|$)/.test(sleep2.querySelector(".kv").textContent), sleep2 && sleep2.querySelector(".kv").textContent);
  const units = [...d.querySelectorAll(".ku")].map(u => u.textContent);
  ok("units are plain words, not codes", !units.includes("ppl") && !units.includes("str"), units.join(","));
  ok("the two networks have their own names", /Contacts abroad/.test(sec().textContent) && /Professional network/.test(sec().textContent));
  ok("no card is still called Global Network", !/Global Network/.test(sec().textContent));
  ok("the plan line replaces the old System line", !/System:/.test(sec().textContent) && /Plan steps: \d+% ticked/.test(sec().textContent));
  ok("the legend speaks plainly", /the vital few/.test(sec().textContent));
  console.log("test52 honest pillars: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
