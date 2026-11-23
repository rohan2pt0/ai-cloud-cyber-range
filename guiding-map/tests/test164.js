// test164: Rent-to-EMI cover (owner 2026-11-23): the home loan entered once under Loans feeds the let-out flat's cover; a flat with no
// loan says "No loan", never 0.00x Weak; a flat's own EMI wins. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const flat = o => Object.assign({ n: "Flat", use: "letout", val: "90", rent: "26000", loan: "", rate: "", emi: "", out: "", vac: "1" }, o || {});
const boot = (loans, props) => {
  const prof = { name: "Fake", dob: "1989-05-05", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, ret: 60, tsav: 20, example: false, earners: 1, loans: loans };
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_props", JSON.stringify(props));
      w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true"); w.localStorage.setItem("gm_quick_done", "true");
      w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } }).window;
};
const tab = w => { w.goTab("prop"); w.renderAll(); const b = w.document.body.cloneNode(true); b.querySelectorAll("script,style").forEach(x => x.remove()); return b.textContent; };
setTimeout(() => {
  const home = [{ type: "Home loan", emi: 48000, remaining: 5400000 }];
  let w = boot(home, [flat()]);
  const r = w.gmPropCalc(flat());
  ok("EMI from Loans gives the cover", r.emiFrom === "loans" && Math.abs(r.dscr - 26000 * 11 / (48000 * 12)) < 1e-6, JSON.stringify([r.emiFrom, r.dscr]));
  ok("the loan amount comes from remaining", Math.abs(r.ltv - 60) < 1e-6, r.ltv);
  let t = tab(w);
  ok("the tab says where the EMI came from", /EMI taken from your Loans/.test(t));
  ok("no 0.00 cover", !/0\.00×/.test(t) && /0\.50×/.test(t));
  w = boot([], [flat()]);
  t = tab(w);
  ok("no loan anywhere says No loan", /No loan/.test(t) && /the rent is all yours/.test(t) && !/0\.00\u00d7/.test(t) && !/Rent does not cover the EMI/.test(t));
  w = boot(home, [flat({ emi: "30000" })]);
  const r3 = w.gmPropCalc(flat({ emi: "30000" }));
  ok("a flat's own EMI is used", r3.emiFrom === "" && Math.abs(r3.dscr - 26000 * 11 / 360000) < 1e-6, r3.dscr);
  t = tab(w);
  ok("own EMI shows no Loans note", !/EMI taken from your Loans/.test(t));
  console.log("test164 rent-to-EMI from loans: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
