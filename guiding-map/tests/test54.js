// v54: the Wheel of Life never invents a score. An unscored area is null (drawn as a gap with a dotted centre
// mark, never 5 or 0), each area gets tap targets 1-10 that stamp S.wheelAt, and a measured chip from the
// numbers the app already holds. Fake data only; S.wheel starts empty.
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
  // an unscored area is null, never an invented 5
  ok("wheelVal returns null for an unscored area", w.eval("wheelVal(0)") === null, String(w.eval("wheelVal(0)")));
  w.goTab("wheel");
  ok("the Wheel tab shows Not scored yet when S.wheel is empty", /Not scored yet/.test(sec().textContent), sec().textContent.slice(0, 200));
  const vals = [...sec().querySelectorAll('span[id^="wsv"]')];
  ok("no area shows a score unless the person set one", vals.length === 8 && vals.every(s => s.textContent === "\u2014"), vals.map(s => s.textContent).join(","));
  const svg = d.getElementById("wheelSvg");
  ok("an empty wheel draws no filled shape and marks the gap with a dotted centre mark", svg && svg.innerHTML.indexOf("<polygon") < 0 && /stroke-dasharray/.test(svg.innerHTML), svg && svg.innerHTML.slice(0, 120));
  ok("an unscored area draws no point on its axis", (svg.innerHTML.match(/<line [^>]*stroke="#0f766e"/g) || []).length === 0, svg.innerHTML.slice(0, 400));
  // tapping 7 for Career saves the felt score and stamps the date
  const t7 = [...sec().querySelectorAll('#wrow0 button')].find(b => b.getAttribute("data-v") === "7");
  ok("Career offers ten tap targets", [...sec().querySelectorAll('#wrow0 button')].length === 10, String([...sec().querySelectorAll('#wrow0 button')].length));
  t7.click();
  ok("tapping 7 for Career saves S.wheel.career = 7", w.S.wheel.career === 7, JSON.stringify(w.S.wheel));
  ok("tapping stamps S.wheelAt with an ISO date", /^\d{4}-\d{2}-\d{2}$/.test(w.S.wheelAt || ""), String(w.S.wheelAt));
  ok("the chosen tap target is highlighted", t7.className.indexOf("on") >= 0, t7.className);
  // measured chips come from the numbers the app already holds
  w.eval("S.vals.invest=60; store('sovS',S);");
  w.goTab("wheel");
  ok("Finances shows a measured chip when a fin measure has a value", /Measured from your numbers/.test(sec().textContent) && /Finances \d+(\.\d+)?\/10/.test(sec().textContent), sec().textContent.slice(0, 300));
  ok("areas with no data show no measured chip", !/Love \d+(\.\d+)?\/10/.test(sec().textContent) && !/Fun \d+(\.\d+)?\/10/.test(sec().textContent), sec().textContent.slice(0, 300));
  // Use the measured scores fills ONLY the unscored areas
  const m = w.eval("wheelMeasured('money')");
  const useBtn = [...sec().querySelectorAll("button")].find(b => (b.getAttribute("onclick") || "").indexOf("whlMeasured") >= 0);
  ok("the Use the measured scores button is there", !!useBtn);
  useBtn.click();
  ok("Use the measured scores fills an unscored area with its measured value", w.S.wheel.money === w.eval("wheelMeasured('money')"), JSON.stringify(w.S.wheel));
  ok("…but keeps the area the person scored themselves", w.S.wheel.career === 7, JSON.stringify(w.S.wheel));
  // a felt/measured gap of 3 or more shows the plain line
  const m2 = w.eval("wheelMeasured('money')");
  w.eval("S.wheel.money = " + (m2 >= 5 ? 1 : 10) + "; store('sovS',S);");
  w.goTab("wheel");
  ok("a felt/measured gap of 3 or more shows the line", m2 >= 5 ? /Feels lower than your numbers/.test(sec().textContent) : /Feels higher than your numbers/.test(sec().textContent), sec().textContent.slice(0, 300));
  console.log("test54 wheel: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
