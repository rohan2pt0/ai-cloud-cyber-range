// test75: no sliders left on the Life OS. A checklist KPI counts itself; another KPI is a number box with
// 44px - and + buttons; an OKR key result is five plain chips. Fake data only.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000,
  exp: 90000, sav: 400000, nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000,
  parents: false, kids: [], loans: [], ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
    w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  try {
    const w = dom.window, d = w.document;

    w.S.okrs = [{ o: "Fake objective", krs: [{ t: "Fake key result", v: 0, at: Date.now() }], at: Date.now() }];
    w.goTab("okr");
    ok(d.querySelectorAll("#sections input[type=range]").length === 0, "the OKR tab has no range input");
    const chips = [...d.querySelectorAll("#sections .chip")];
    ok(chips.map((c) => c.textContent).join("|") === "Not started|Started|Halfway|Nearly|Done", "five plain chips: " + chips.map((c) => c.textContent).join("|"));
    const half = chips.find((c) => c.textContent === "Halfway");
    ok(half, "the Halfway chip is there");
    half.click();
    ok(w.S.okrs[0].krs[0].v === 0.5, "Halfway stores 0.5, got " + w.S.okrs[0].krs[0].v);
    const halfAfter = [...d.querySelectorAll("#sections .chip")].find((c) => c.textContent === "Halfway");
    ok(halfAfter && halfAfter.classList.contains("on") && halfAfter.getAttribute("aria-pressed") === "true", "the chosen chip shows as on");

    const counts = (k) => !!(k.steps && k.steps.length && k.base === 0 && k.goal === k.steps.length);
    const idxCheck = w.KPIs.findIndex((k) => !k.auto && counts(k));
    ok(idxCheck >= 0, "a checklist KPI exists");
    const check = w.KPIs[idxCheck], checkId = check.id;
    w.openK(idxCheck);
    ok(d.querySelectorAll("#mo input[type=range]").length === 0, "the checklist KPI modal has no range input");
    ok(/Counts itself from the boxes below/.test(d.getElementById("m_slider").textContent), "it says the boxes count it");
    ok(d.getElementById("mv").textContent === w.checkedArr("k", checkId).length + check.unit, "the checklist KPI reads its ticked steps, got " + d.getElementById("mv").textContent);
    w.tg("k", idxCheck, 0);
    ok(w.S.vals[checkId] === 1, "ticking a step saves the count in S.vals, got " + w.S.vals[checkId]);
    ok(d.getElementById("mv").textContent === "1" + check.unit, "the value follows the tick, got " + d.getElementById("mv").textContent);
    ok(w.kVal(w.KPIs.find((k) => k.id === checkId)) === 1, "kVal counts the ticked steps");
    ok(d.querySelectorAll("#mo input[type=range]").length === 0, "the checklist modal still has no range after a tick");

    const idxNum = w.KPIs.findIndex((k) => !k.auto && !counts(k));
    ok(idxNum >= 0, "a numeric KPI exists");
    const numItem = w.KPIs[idxNum], numId = numItem.id, before = w.kVal(numItem);
    w.openK(idxNum);
    ok(d.querySelectorAll("#mo input[type=range]").length === 0, "the numeric KPI modal has no range input");
    const num = d.querySelector('#mo input[type="number"]');
    ok(num && num.getAttribute("inputmode") === "decimal" && num.min === String(numItem.base) && num.max === String(numItem.goal), "the number box has decimal input and the boundaries");
    const plus = [...d.querySelectorAll("#mo button")].find((b) => b.textContent === "+");
    ok(plus && plus.getAttribute("aria-label") === "Increase", "the + button is there and labelled");
    plus.click();
    const step = (numItem.goal - numItem.base) > 20 ? 1 : 0.5;
    ok(w.S.vals[numId] === before + step, "the + button raises the value by one step to " + (before + step) + ", got " + w.S.vals[numId]);
    ok(w.S.valsAt[numId] > 0, "slide stores when the value last changed");
    ok(/Updated 0 days ago/.test(d.getElementById("m_slider").textContent), "the modal says when it was updated");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test75 no sliders; count, number box and chips: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
