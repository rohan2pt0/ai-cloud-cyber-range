// v119: the expert council, item 3: early-warning signs (indicators and warnings, vital signs): runway, saving rate,
// spending against plan, energy and slipping habits, each with lines where amber and red begin. Risk shows all five;
// Today shows only the most urgent red one, in one calm line, and the link to the signs works. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
// runway: sav 150000 / (exp 60000 + emi 15000) = 2.0 months -> red; saving: (100000 - 60000 - 15000)/100000 = 25% -> green
const prof = { name: "Fake", dob: "1988-02-02", gross: 120000, net: 100000, exp: 60000, sav: 150000, kids: [], loans: [{ emi: 15000 }], example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  let sg = []; try { sg = w.gmSigns(); } catch (x) { sg = [{ id: "ERR " + x.message }]; }
  const by = (id) => sg.filter(x => x.id === id)[0] || {};
  ok("the signs compute without an error", sg.length >= 3 && !/^ERR/.test(sg[0].id), JSON.stringify(sg).slice(0, 120));
  ok("runway of 2.0 months is red", by("runway").st === "low" && by("runway").v === "2.0 months", JSON.stringify(by("runway")));
  ok("a 25% saving rate is green", by("saving").st === "good" && by("saving").v === "25%", JSON.stringify(by("saving")));
  w.goTab("risk");
  const card = d.querySelector(".gm-signs");
  ok("Risk shows the signs, red first, with its one action", !!card && card.querySelector(".gm-sign").getAttribute("data-sign") === "runway" && /Move a fixed amount into the emergency fund/.test(card.textContent));
  w.goTab("today");
  const line = d.querySelector(".gm-sign-today");
  ok("Today shows one calm line for the red sign, above the daily three", !!line && /Buffer: 2.0 months/.test(line.textContent) && d.querySelectorAll(".gm-sign-today").length === 1);
  let clicked = true; try { w.gmSignSeen("x:runway"); } catch (x) { clicked = false; }
  ok("the link works (it once called a function private to another part of the app)", clicked && w.curTab === "risk", String(w.curTab));
  const k = (typeof w.dKey === "function") ? w.dKey(new Date()) : "";
  w.gmSignSeen(k + ":runway"); w.goTab("today");
  ok("once seen today, the line rests until tomorrow", !d.querySelector(".gm-sign-today"));
  w.eval("P.sav=900000;store('sovP',P);"); w.goTab("risk");
  ok("a full fund turns runway green", (w.gmSigns().filter(x => x.id === "runway")[0] || {}).st === "good");
  console.log("test119 early warning signs: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
