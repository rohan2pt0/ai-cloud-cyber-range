// test182: the Money health fixes and the big-waves card use everyday words (queue horizon-waves and
// plain-first-everywhere; owner 2026-11-25). A debt fund is not a loan, "SIP" is jargon, and two policies due
// the same month must not read as one line. Pure: no network, no AI, no storage write.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: iso(-Math.round(38.5 * 365.25)), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 50000, sav: 300000, pname: "Fake Partner",
  kids: [{ name: "Kid A", dob: "2018-01-01" }], ret: 60, tsav: 20, example: false, earners: 1, mine: { mf: 1400000, epf: 600000 },
  loans: [{ type: "Personal loan", remaining: 200000, emi: 10000, rate: 14, tenure: 20 }] };
// Two policies in the Money health register, due the same month: a health cover and a top-up.
const mh = { policies: [
  { type: "health", who: "family", sa: 500000, prem: 18000, start: iso(-355) },
  { type: "topup", who: "family", sa: 1000000, prem: 6000, start: iso(-355) }],
  funds: [{ name: "Example Flexi Cap Fund", value: 800000, plan: "regular" }, { name: "Example Index Fund", value: 600000, plan: "direct" }],
  macro: { repo: 5.5, cpi: 3, at: iso(-20) }, alloc: {}, bench: {} };
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window;
  const jargon = /\bdebt\b|\bSIPs?\b/i;
  const al = (drift) => ({ drift: drift, months: 3, switchAmt: 5000, move: 100000, fromNew: 50000, total: 2000000, actual: drift > 0 ? 68 : 52, t: { target: 60 } });
  const base = { local: true, surplus: 50000, benchSet: { drag: 0.75 }, drag: 0.75 };

  // 1. no fix title says "debt" (a loan) or "SIP" (jargon), in either direction of drift
  [8, -8].forEach(dr => {
    const R = w.gmRemedies("alloc-drift", Object.assign({}, base, { al: al(dr) }));
    ok("alloc-drift drift " + dr + ": both fixes are offered", R.fixes.length === 2, R.fixes.map(x => x.id).join());
    R.fixes.forEach(x => ok("alloc-drift title uses plain words: " + x.title, !jargon.test(x.title), x.title));
  });
  const FR = w.gmRemedies("fund-regular", Object.assign({}, base, { regV: 800000 }));
  ok("fund-regular offers the direct-plan fix", FR.fixes.length === 1 && FR.fixes[0].id === "fund-direct", FR.fixes.map(x => x.id).join());
  FR.fixes.forEach(x => ok("fund-regular title uses plain words: " + x.title, !jargon.test(x.title), x.title));
  FR.fixes.forEach(x => ok("fund-regular time uses plain words: " + x.time, !jargon.test(x.time), x.time));

  // 2. the mix titles say "safer funds" for debt and "shares" for equity
  const up = w.gmRemedies("alloc-drift", Object.assign({}, base, { al: al(8) })).fixes.map(x => x.title).join(" | ");
  const down = w.gmRemedies("alloc-drift", Object.assign({}, base, { al: al(-8) })).fixes.map(x => x.title).join(" | ");
  ok("above target: new money and a switch go to safer funds", /safer funds/.test(up) && !/equity/i.test(up) && !/\bdebt\b/i.test(up), up);
  ok("below target: new money and a switch go to shares", /shares/.test(down) && !/equity/i.test(down) && !/\bdebt\b/i.test(down), down);

  // 3. two policies due the same month are two rows, each naming its own policy type
  const due = w.gmComingUp().filter(x => x.kind === "policy" && /^Premium due/.test(x.t));
  ok("two policies due the same month give two premium rows", due.length === 2, String(due.length));
  ok("the two premium rows say which policy each is", due.length === 2 && new Set(due.map(x => x.t)).size === 2, due.map(x => x.t).join(" | "));
  ok("each premium row carries its policy type", due.length === 2 && due.some(x => /Health/.test(x.t)) && due.some(x => /Top-up|Super top-up/.test(x.t)), due.map(x => x.t).join(" | "));

  console.log("test182 plain words in the fixes and the waves card: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
