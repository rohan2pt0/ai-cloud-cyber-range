// test180: Ready for the big waves (queue horizon-waves, slice 1; owner 2026-11-25). Under Money health, four world
// waves are checked against the person's own numbers: ready, partly ready or not ready yet, one plain line why, and only
// the fixes whose issue the Money health scan actually flags. Pure: no network, no AI, no storage write.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: iso(-Math.round(38.5 * 365.25)), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 50000, sav: 300000, pname: "Fake Partner",
  kids: [{ name: "Kid A", dob: "2018-01-01" }], ret: 60, tsav: 20, example: false, earners: 1, mine: { mf: 1400000, epf: 600000 },
  loans: [{ type: "Personal loan", remaining: 200000, emi: 10000, rate: 14, tenure: 20 }] };
const mh = { policies: [
  { type: "pli", who: "me", sa: 500000, prem: 24000, start: iso(-Math.round(7.5 * 365.25)), term: 20, ppt: 20, sv: 110000, pu: 180000 },
  { type: "health", who: "family", sa: 500000, prem: 18000, start: "2017-06-01" },
  { type: "health", who: "family", sa: 500000, prem: 21000, start: "2023-06-01" }],
  funds: [{ name: "Example Flexi Cap Fund", value: 800000, plan: "regular" }, { name: "Example Index Fund", value: 600000, plan: "direct" }],
  macro: { repo: 5.5, cpi: 3, at: iso(-20) }, alloc: {}, bench: {} };
let fetches = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => { fetches++; return Promise.reject(new Error("offline")); }; } });
setTimeout(() => {
  const w = dom.window, d = w.document, c = w.gmMhCtx();

  // 1. four waves, each with a plain status and one line why
  const W = w.gmWaves(c);
  ok("gmWaves gives the four waves in order", Array.isArray(W) && W.length === 4 && W.map(x => x.id).join() === "slowdown,prices-rates,trade-shocks,health-weather", W && W.map(x => x.id).join());
  ok("each wave has a name, a status and a plain line why", W.every(x => typeof x.name === "string" && x.name && ["ready", "partly", "not"].indexOf(x.status) > -1 && typeof x.why === "string" && x.why.length > 10));
  ok("the same numbers give the same answer twice", JSON.stringify(w.gmWaves(c)) === JSON.stringify(W));
  const f0 = fetches;
  w.gmWaves(c); w.gmWaves(Object.assign({}, c, { buffer: 2 }));
  ok("no network call", fetches === f0, String(fetches - f0));

  // 2. the slowdown follows the cash buffer: 6 months ready, 3 to 6 partly, under 3 or unknown not yet
  const sw = (b) => w.gmWaves(Object.assign({}, c, { buffer: b })).find(x => x.id === "slowdown").status;
  ok("a buffer of 6 months or more is ready", sw(6) === "ready" && sw(12) === "ready", sw(6) + "," + sw(12));
  ok("a buffer of 3 to under 6 months is partly ready", sw(3) === "partly" && sw(5.9) === "partly", sw(3) + "," + sw(5.9));
  ok("a buffer under 3 months or unknown is not ready yet", sw(2.9) === "not" && sw(0) === "not" && sw(null) === "not" && w.gmWaves(Object.assign({}, c, { buffer: undefined })).find(x => x.id === "slowdown").status === "not");

  // 3. health-weather follows the two cover gaps
  const hw = (hg, lg) => w.gmWaves(Object.assign({}, c, { hGap: hg, lifeGap: lg })).find(x => x.id === "health-weather").status;
  ok("a short health cover or a short life cover is not ready yet", hw(1, 0) === "not" && hw(0, 1) === "not" && hw(1, 1) === "not");
  ok("both covers at their floors is ready", hw(0, 0) === "ready");

  // 4. fixes are issue ids from REMEDIES, and only those the Money health scan flags
  const scan = w.gmMhScan(c).map(f => f.issue), keys = Object.keys(w.GM_REMEDIES);
  W.forEach(x => ok(x.id + ": every fix is an issue that exists in REMEDIES", x.fixes.every(id => keys.indexOf(id) > -1), x.fixes.join()));
  ok("only flagged issues are shown as fixes", W.find(x => x.id === "slowdown").fixes.join() === "debt-costly"
    && W.find(x => x.id === "prices-rates").fixes.join() === "alloc-drift,debt-costly,fund-regular"
    && W.find(x => x.id === "trade-shocks").fixes.join() === "alloc-drift"
    && W.find(x => x.id === "health-weather").fixes.join() === "health-below-floor,life-cover-gap", JSON.stringify(W.map(x => [x.id, x.fixes])));
  ok("a fix that is not flagged is hidden", !scan.includes("cash-idle") && w.gmWaves(Object.assign({}, c, { buffer: 1 })).find(x => x.id === "slowdown").fixes.join() === "debt-costly");

  // 5. the block under Money health: four waves, the reason folded, the source cited, no fear words
  w.goTab("money"); w.renderAll();
  const card = d.querySelector(".gm-mh");
  ok("the Money health card shows the big waves block", !!card && /Ready for the big waves/.test(card.textContent), card ? card.textContent.slice(0, 80) : "missing");
  ok("the four waves are named", !!card && ["A slowdown", "Prices and rates", "Trade shifts", "Health and weather"].every(n => card.textContent.includes(n)));
  ok("Why these waves holds the source line", !!card && /Why these waves/.test(card.textContent) && /World Economic Forum Global Risks Report 2026, paraphrased/.test(card.textContent));
  ok("the block stays calm: no fear words", !!card && !/crash|panic|collapse|catastroph|doom|devastat/i.test(card.textContent));
  ok("the screen shows no NaN, Infinity or a negative rupee", !!card && !/NaN|Infinity|-₹|−₹/.test(card.textContent));

  // 6. damaged storage never throws
  let threw = "";
  try {
    w.localStorage.setItem("gm_mhealth", "}{"); w.localStorage.setItem("sovP", "}{");
    const r = w.gmWaves(w.gmMhCtx());
    ok("damaged storage: still four waves, never NaN", Array.isArray(r) && r.length === 4 && !/NaN|Infinity|undefined/.test(JSON.stringify(r)));
  } catch (er) { threw = String(er); }
  ok("damaged storage: no crash", !threw, threw);

  console.log("test180 ready for the big waves: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
