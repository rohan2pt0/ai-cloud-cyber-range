// v45: Today is calm and one-open-action. Each habit is a compact row with its floor on one muted line and the
// IF-THEN anchor folded under "How"; the streak appears only once it is above zero. Insights are one closed panel,
// not a wall of cards, and the destructive reset lives in Ops with the other health actions, not in the footer.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_calm", "false");
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("today");
  const today = sec(), t = today.textContent;
  ok("Today has no 'Floor today' pill", !/Floor today/i.test(t) && !today.querySelector(".hab-floor"));
  ok("a zero streak shows no flame", !t.includes("0\uD83D\uDD25"));
  const dets = [...today.querySelectorAll(".hab details")];
  ok("each habit's anchor sits in a closed How details", dets.length === 5 && dets.every(x => !x.open && /How/.test(x.querySelector("summary").textContent)), dets.length + " details");
  ok("every anchor is inside a details", [...today.querySelectorAll(".hab-anchor")].length === 5 && [...today.querySelectorAll(".hab-anchor")].every(a => a.closest("details")));
  ok("the science is folded, not shown", !/The science:/.test(t));

  const ins = d.getElementById("insights"), box = ins.querySelector("details.gm-insights");
  const n = ins.querySelectorAll(".insight").length;
  ok("insights are one closed details with the card count", !!box && !box.open && box.querySelector("summary").textContent.trim() === "Insights (" + n + ")" && n > 0,
    box ? box.querySelector("summary").textContent + " / " + n : "no details");
  const it = ins.textContent;
  ok("insights do not cite StickK", !/StickK/i.test(it));
  ok("insights have no 'No OKRs set'", !/No OKRs set/.test(it));
  ok("insights invite one goal", /Set one goal for this quarter \(optional\)/.test(it));
  ok("insights invite a stake", /A stake for a goal you keep missing \(optional\)/.test(it));
  ok("the points and level card is gone", !/next level at/.test(it));

  const foot = d.querySelector("footer");
  ok("footer has no reset button", !foot.querySelector("button") && !/Reset all data/.test(foot.textContent), foot.textContent);

  w.goTab("ops");
  ok("Ops has the erase-all-data button", /Erase all data on this device/.test(sec().textContent));
  console.log("test45 calm Today: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
