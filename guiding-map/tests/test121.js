// v121: Calls journal on the Plan tab (queue calls-journal, slice 1). Log a call ("I expect X by date") with a
// confidence, judge it in one tap when its date comes, and see how often you were right at each confidence.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const plan = () => { w.goTab("plan"); return d.querySelector('.gm-calls'); };
  const saved = () => { try { return JSON.parse(w.localStorage.getItem("gm_calls") || "[]") || []; } catch (x) { return []; } };
  let card = plan();

  ok("the Plan tab shows the calls journal", !!card, card ? "no .gm-calls card" : "no card");
  ok("with no calls, an example line invites the first one", !!card && /first one/i.test(card.textContent),
    card ? card.textContent.slice(0, 140) : "no card");

  if (card) {
    const text = d.getElementById("gmCallText"), date = d.getElementById("gmCallDate");
    const chip = d.querySelector('[data-call-conf="70"]'), add = d.querySelector('[data-call-add]');
    ok("the date defaults to 90 days ahead", !!date && Math.abs((Date.parse(date.value) - Date.now()) / 86400000 - 90) <= 2,
      date ? date.value : "no date field");
    if (text && date && chip && add) {
      text.value = "I expect the fund to cross 10 lakh";
      chip.click();
      date.value = "2020-01-01";
      add.click();
    }
    const a = saved();
    ok("adding a call stores it in gm_calls", a.length === 1 && a[0].text === "I expect the fund to cross 10 lakh" && +a[0].conf === 70 && a[0].date === "2020-01-01", JSON.stringify(a));
    card = plan();
    ok("the call shows on the Plan tab", !!card && /fund to cross 10 lakh/.test(card.textContent),
      card ? card.textContent.slice(0, 160) : "no card");
    const fold = card && card.querySelector('details.gm-call-new');
    ok("while a call is due, judging it is the one action and the new-call form is folded", !!fold && !fold.open
      && card.innerHTML.indexOf('data-call-yes') < card.innerHTML.indexOf('gm-call-new'), fold ? "form open or above" : "form not folded");
    const yes = card && card.querySelector('[data-call-yes]'), no = card && card.querySelector('[data-call-no]');
    ok("a call whose date has passed offers Yes and No", !!(yes && no), "missing");
    if (yes) yes.click();
    const a2 = saved();
    ok("a tap records the outcome", a2.length === 1 && a2[0].outcome === "yes", JSON.stringify(a2));
    card = plan();
    ok("the card shows the right-count per confidence level", !!card && /At 70% you were right 1 of 1/.test(card.textContent),
      card ? card.textContent.slice(0, 200) : "no card");
  }
  // A synced or restored file can plant an id that would break out of onclick='...': it is replaced, never rendered.
  w.localStorage.setItem("gm_calls", JSON.stringify([{ id: "x');window.__pwned=1;('", text: "Planted", conf: 80, date: "2020-01-01", outcome: null, ts: 1 }]));
  card = plan();
  const btn = card && card.querySelector('[data-call-yes]');
  ok("a planted id never reaches an onclick", !!btn && !/pwned/.test(card.innerHTML), card ? card.innerHTML.slice(0, 200) : "no card");
  if (btn) btn.click();
  ok("the planted call can still be judged, and no planted script ran", !w.__pwned && saved()[0] && saved()[0].outcome === "yes", JSON.stringify(saved()));
  console.log("test121 calls journal: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
