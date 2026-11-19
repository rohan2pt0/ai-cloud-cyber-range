// v148: whose name a property is in (two-earners-2): owner, share, borrower, papers, rent split. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Asha Fake", pname: "Ravi Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const done = () => { console.log("test148: PASS " + P + " FAIL " + F); e.forEach(x => console.log("  FAIL " + x)); process.exit(F ? 1 : 0); };
const setProps = (w, arr) => { w.localStorage.setItem("gm_props", JSON.stringify(arr)); };
const text = w => { w.goTab("prop"); const c = w.document.querySelector(".gm-papers"); const s = c ? c.closest(".section") : null; return (s || w.document.body).textContent.replace(/\s+/g, " "); };
setTimeout(() => {
  const w = dom.window;
  ok("gmRentByPerson exported", typeof w.gmRentByPerson === "function");
  setProps(w, [{ n: "Old flat", use: "letout", val: "75", rent: "18000", loan: "32", rate: "7.25", emi: "26000", out: "48000", vac: "1" }]);
  let t = text(w);
  ok("old property renders", /Old flat/.test(t) && /On whose name is it\?/.test(t));
  let r = w.gmRentByPerson();
  ok("old property defaults to me", r.me === 18000 && r.partner === 0, JSON.stringify(r));
  ok("loan question shown with a loan", /Who pays the home loan\?/.test(t));
  setProps(w, [{ n: "Joint flat", use: "letout", val: "75", rent: "20000", owner: "joint", share: "60", loan: "", vac: "1" }]);
  t = text(w); r = w.gmRentByPerson();
  ok("joint 60/40 splits rent", r.me === 12000 && r.partner === 8000, JSON.stringify(r));
  ok("no loan question without loan", !/Who pays the home loan\?/.test(t));
  ok("agreement line names both people", /every owner on the title \(Asha and Ravi\)/.test(t));
  ok("partner share shown", /Ravi: 40%/.test(t));
  setProps(w, [{ n: "P flat", use: "letout", rent: "10000", owner: "partner" }, { n: "Home", use: "self", rent: "99999", owner: "joint" }]);
  r = w.gmRentByPerson();
  ok("partner-owned rent is the partner's; self-use excluded", r.me === 0 && r.partner === 10000, JSON.stringify(r));
  setProps(w, [{ n: "Low", use: "letout", rent: "50000", owner: "joint", share: "50" }]);
  t = text(w); ok("no TDS line at 50,000", !/deduct TDS/.test(t));
  setProps(w, [{ n: "High", use: "letout", rent: "60000", owner: "joint", share: "50" }]);
  t = text(w); ok("TDS line above 50,000", /deduct TDS \(2%\)/.test(t));
  ok("TDS names the PAN of each owner", /each owner’s PAN/.test(t));
  setProps(w, [{ n: "High", use: "letout", rent: "60000", owner: "joint", share: "50", loan: "30", borrower: "joint" }]);
  t = text(w);
  const papers = w.document.querySelector(".gm-papers"); const pt = papers ? papers.textContent : "";
  ok("papers card present, later folded", !!papers && /Later \(\d\)/.test(pt) && !!papers.querySelector("details"));
  ok("no section number", !/\b194\b|24\(b\)|\b80C\b|section \d/i.test(pt));
  ok("no wife or husband", !/\b(wife|husband)\b/i.test(t));
  ok("CA tag present", /confirm with your CA/.test(pt));
  ok("no broken possessive such as You\u2019s", !/You[\u2019']s\b/.test(t));
  w.close();
  done();
}, 1500);
