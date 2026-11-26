// test185: Money health, published figures (queue published-figures, slice 1; owner 2026-11-26). The RBI repo rate and
// CPI inflation fill in by themselves from the latest published figures, with their date and source, and stay editable;
// nobody types a public number. With nothing typed the card shows the published figures and works the debt-duration line
// from them; a typed value wins and reads "your figure"; a "Use the published figure" link clears the typed one.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: iso(-Math.round(38.5 * 365.25)), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 50000, sav: 300000, pname: "Fake Partner",
  kids: [{ name: "Kid A", dob: "2018-01-01" }], ret: 60, tsav: 20, example: false, earners: 1, mine: { mf: 1400000, epf: 600000 },
  loans: [{ type: "Personal loan", remaining: 200000, emi: 10000, rate: 14, tenure: 20 }] };
const mh = { policies: [{ type: "health", who: "family", sa: 500000, prem: 18000, start: iso(-355) }],
  funds: [{ name: "Example Index Fund", value: 600000, plan: "direct" }],
  macro: {}, alloc: {}, bench: {} };
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.S = w.S || { okrs: [] }; w.S.okrs = [];
  w.goTab("money"); w.renderAll();
  let card = d.querySelector(".gm-mh");
  const txt = () => card ? card.textContent : "";

  // 1. with nothing typed, the published figures fill in, with their date and source
  ok("the repo rate fills in as 5.5 with its source and date", txt().indexOf("5.5 · RBI, 7 Oct 2026") >= 0, txt().slice(0, 200));
  ok("the CPI fills in as 6.09 with its source and date", txt().indexOf("6.09 · MoSPI, Oct 2026 (released 12 Nov 2026)") >= 0);
  ok("the debt-duration line is worked out from the published figures", txt().indexOf("Real rate = repo 5.5%") >= 0 && txt().indexOf("Debt duration") >= 0 && txt().indexOf("short (under 3 years)") >= 0);
  const change = card && [...card.querySelectorAll("a")].find(a => (a.textContent || "") === "change");
  ok("a change link is there, and no typed value yet", !!change && txt().indexOf("your figure") < 0);
  if (change) { change.click(); const allocBox = d.querySelector(".gm-mh-alloc"); ok("the change link opens the committee box", !!(allocBox && allocBox.open)); }
  if (d.activeElement && d.activeElement.blur) d.activeElement.blur(); // the change link focuses the field; renderAll waits for the blur, as a person's typing would

  // 2. a typed value wins and shows "your figure"
  w.gmMhMacroSet("repo", "4");
  card = d.querySelector(".gm-mh");
  ok("a typed value wins", txt().indexOf("your figure") >= 0 && txt().indexOf("Real rate = repo 4%") >= 0, txt().slice(0, 200));
  ok("the published CPI is still used alongside it", txt().indexOf("CPI 6.09%") >= 0);

  // 3. the "Use the published figure" link clears the typed one
  const use = card && [...card.querySelectorAll("a")].find(a => (a.textContent || "").indexOf("Use the published figure") >= 0);
  ok("a Use the published figure link is there", !!use);
  if (use) use.click();
  card = d.querySelector(".gm-mh");
  ok("it clears the typed figure and goes back to the published one", txt().indexOf("your figure") < 0 && txt().indexOf("5.5 · RBI, 7 Oct 2026") >= 0 && txt().indexOf("Real rate = repo 5.5%") >= 0);

  console.log("test185 published figures: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
