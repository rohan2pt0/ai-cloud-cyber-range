// test150: real monthly spend without tracking (owner 2026-11-19). Fixed bills listed once, variable spend derived from one balance per
// earner each month, a runway against a dynamic target, and the Buffer tile reading the real figure. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", pname: "Sam", pdob: "1990-02-01", country: "India", cur: "INR", gross: 300000, net: 150000, exp: 60000, sav: 600000,
  nw: 1500000, kids: [], loans: [{ name: "Fake loan", remaining: 1000000, emi: 20000 }], ret: 50, tsav: 20, example: false,
  earners: 2, psal: 100000, mine: { fd: 200000 }, partner: { net: 100000, fd: 100000 }, rent1: 10000, rent2: 0 };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const mk = (p, life) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(p)); w.localStorage.setItem("gm_simple", "false");
    w.localStorage.setItem("gm_mine_done", "true"); if (life) w.localStorage.setItem("gm_life", JSON.stringify(life));
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const ym = (back) => { const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() - back); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2); };
const dom = mk(prof, { fSip: "30000", fEF: "10000" });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage;
  const add = (i, amt, k, v) => { w.gmFixedAdd(i); const l = JSON.parse(ls.getItem("gm_fixed")); const x = l[l.length - 1]; w.gmFixedSet(x.id, "amt", String(amt)); if (k) w.gmFixedSet(x.id, k, v); return x.id; };
  // suggestions: 0 Rent, 6 OTT (want), 9 Term insurance (yearly)
  add(0, 40000);
  add(9, 24000);
  const club = add(6, 12000, "kind", "want");
  const fx = JSON.parse(ls.getItem("gm_fixed"));
  ok("fixed bills are stored as id, name, amt, every, who, kind", fx.length === 3 && ["id", "name", "amt", "every", "who", "kind"].every(k => k in fx[0]));
  ok("a yearly item is a twelfth a month", fx[1].every === "year" && fx[1].amt === 24000);
  // fixed = 40000 + 2000 + 12000 + EMI 20000
  const card0 = w.gmSpendCard();
  ok("the fixed total is 74,000 a month (yearly spread, EMI read from loans)", /Fixed bills[^<]*74,000 a month, ₹8,88,000 a year/.test(card0), card0.slice(card0.indexOf("Fixed bills"), card0.indexOf("Fixed bills") + 160));
  ok("the EMI is a read-only line, never a stored or asked item", /Fake loan EMI <span[^>]*>\(already known\)/.test(card0) && !fx.some(x => /EMI/.test(x.name)));
  ok("before a second check-in the variable part is an estimate", /estimate/.test(card0) && /After next month/.test(card0));
  ok("one check-in is not enough for real spend", w.gmRealSpend().est === true);
  // check-in form: two inputs for two earners, one for one
  ok("two earners get two balance inputs", /id="gmCkMe"/.test(card0) && /id="gmCkPt"/.test(card0));
  // two check-ins (last month, this month)
  ls.setItem("gm_spendcheck", JSON.stringify({ [ym(1)]: { me: 300000, partner: 100000, at: ym(1) + "-01" }, [ym(0)]: { me: 320000, partner: 110000, at: ym(0) + "-01" } }));
  const r = w.gmRealSpend();
  // 2,60,000 in - 40,000 saved - 74,000 fixed - 30,000 rise = 1,16,000 variable
  ok("two check-ins give the right variable spend", r && !r.est && r.variable === 116000 && r.fixed === 74000 && r.total === 190000, JSON.stringify(r));
  w.goTab("money"); w.renderAll();
  const sec = d.querySelector("#sections") || d.body, txt = sec.textContent;
  ok("the card says the real spend plainly", /Your real monthly spend: ₹1,90,000/.test(txt) && /fixed ₹74,000 \+ variable ₹1,16,000/.test(txt), txt.slice(txt.indexOf("Your real"), txt.indexOf("Your real") + 120));
  ok("the fixed vs variable bar is a true share (39% / 61%)", /aria-label="Fixed 39 percent, variable 61 percent"/.test(sec.innerHTML));
  ok("last months and their average are shown", /Average variable/.test(txt) && /Last 1 month/.test(txt));
  // runway: 9,00,000 / 1,90,000 = 4.7 months
  let rw = w.gmRunway();
  ok("runway uses savings plus both FDs over real spend", rw && Math.abs(rw.months - 900000 / 190000) < 1e-9, rw && rw.months);
  ok("salaried target is 6 months, amber at 4.7", rw.target === 6 && rw.state === "watch" && !!sec.querySelector(".gm-rag-watch"), rw.state);
  w.gmWorkSet("me", "contract"); w.renderAll();
  rw = w.gmRunway();
  const sec2 = d.querySelector("#sections") || d.body;
  ok("contract target is 12 months, red at 4.7", rw.target === 12 && rw.state === "low" && !!sec2.querySelector(".gm-rag-low") && /aim 12\+ months/.test(sec2.textContent), rw.state);
  ok("the work choice is stored as kind and from", JSON.parse(ls.getItem("sovP")).work.kind === "contract" && JSON.parse(ls.getItem("sovP")).work.from === "2027-01-01");
  w.gmWorkSet("me", "salaried"); w.gmWorkSet("partner", "contract");
  ok("either earner on contract makes the target 12", w.gmRunway().target === 12);
  w.gmWorkSet("partner", "salaried");
  ok("back to salaried: 6", w.gmRunway().target === 6);
  // owner 2026-11-19: "what is Need; I don't know whether what I enter is saved; the buttons don't look proper"
  { let said = ""; w.gmToast = (t) => { said = t; };
    const fx = JSON.parse(w.localStorage.getItem("gm_fixed") || "[]")[0];
    if (fx) { w.gmFixedSet(fx.id, "kind", "want");
      ok("a change says it was saved, with the monthly amount", /^Saved: /.test(said) && /could pause/.test(said), said); }
    w.goTab("money"); w.renderAll();
    const row = w.document.querySelector(".gm-fx");
    ok("each bill offers Must pay or Could pause, the chosen one marked", !!row && /Must pay/.test(row.textContent) && /Could pause/.test(row.textContent) && !!row.querySelector('.gm-seg [aria-pressed="true"]'));
    ok("each bill shows what it costs a month", !!row && /\/month|add amount/.test(row.textContent));
    ok("the list says that changes save at once", /saves on this device at once/.test(w.document.body.textContent));
    if (fx) w.gmFixedSet(fx.id, "kind", fx.kind || "need"); }
  // owner 2026-11-19: "only my work will be contract; the partner's is permanent (government); after clicking nothing much happens; placement is wrong"
  w.gmWorkSet("me", "contract"); w.gmWorkSet("partner", "permanent"); w.goTab("money"); w.renderAll();
  const rp = w.gmRunway();
  ok("a permanent (govt / PSU) partner's pay is counted as secure: savings cover only the rest", rp.secure > 0 && Math.abs(rp.gapM - Math.max(0, rp.real.total - rp.secure)) < 1, JSON.stringify({ s: rp.secure, g: rp.gapM }));
  ok("contract still sets the aim to 12 months", rp.target === 12);
  const card = w.document.querySelector(".gm-rs"), work = card && card.querySelector(".gm-work");
  ok("the work choice sits with the cover it changes (inside the card, after the aim)", !!work && card.innerHTML.indexOf("is the aim") < card.innerHTML.indexOf("gm-work"));
  ok("once both are chosen it folds to one line naming both", !!work && work.tagName === "DETAILS" && /Contract/.test(work.querySelector("summary").textContent) && /Permanent \(govt \/ PSU\)/.test(work.querySelector("summary").textContent), work && work.outerHTML.slice(0, 200));
  const pressed = work ? [...work.querySelectorAll('button[aria-pressed="true"]')].map(b => b.textContent) : [];
  ok("the chosen option is marked, so a tap visibly lands", pressed.includes("Contract") && pressed.includes("Permanent (govt / PSU)"), pressed.join("|"));
  w.gmWorkSet("me", "salaried"); w.gmWorkSet("partner", "salaried");
  // insight names the biggest want and what pausing it adds: 9,00,000/1,78,000 - 4.74 = 0.3
  w.gmWorkSet("me", "contract"); rw = w.gmRunway();
  ok("the insight names the biggest want and its gain, a small one in days (never 0.0 months)", /Pausing OTT and app subscriptions adds 10 days/.test(rw.insight) && /10% cut in variable spend adds \d/.test(rw.insight) && !/0\.0 months/.test(rw.insight), rw.insight);
  // Buffer tile: 6,00,000 / 1,90,000 = 3.2m (not the profile's 60,000 + 20,000 EMI = 7.5m)
  w.goTab("today"); w.renderAll();
  const tile = [...d.querySelectorAll("#gmVitals > div")].find(t => /Buffer|Runway/.test(t.textContent));
  ok("the Buffer tile uses the real spend", !!tile && /3\.2m/.test(tile.textContent), tile && tile.textContent);
  // My numbers: spending becomes a derived line
  const nums = w.gmNumbersCard();
  ok("My numbers shows spending as a line from the check-ins, not an input", /Monthly spending: <b[^>]*>₹1,90,000<\/b>[^]*from your month-end check-ins/.test(nums) && !/gmNumSet\('exp'/.test(nums), nums.slice(0, 400));
  ok("the other numbers are still inputs", /gmNumSet\('net'/.test(nums) && /gmNumSet\('sav'/.test(nums));
  // calendar
  const reg = w.gmCalendarRegistry().filter(x => x.id === "spend-monthly")[0];
  ok("the calendar registry holds spend-monthly in group money", !!reg && reg.group === "money" && reg.v === 1);
  const ics = w.gmCalendarICS("money");
  ok("it repeats on the 1st of every month from 1 Dec 2026 at 09:00 for 10 minutes", /RRULE:FREQ=MONTHLY;BYMONTHDAY=1/.test(ics) && /DTSTART:20261201T090000/.test(ics) && /DTEND:20261201T091000/.test(ics) && /UID:securax-gm-spend-monthly@local/.test(ics), ics.slice(0, 500));
  ok("test38 lists the id as handed out", /"spend-monthly"/.test(fs.readFileSync(path.join(__dirname, "test38.js"), "utf8")));
  // due logic: 1st to 7th of the month, or until done; one open action
  ls.setItem("gm_spendcheck", JSON.stringify({ [ym(1)]: { me: 300000, partner: 100000, at: ym(1) + "-01" } }));
  const day = new Date().getDate();
  ok("the check-in is due now (90 in the first week, 45 after) until done", w.gmSpendDue() === (day <= 7 ? 90 : 45), w.gmSpendDue());
  ok("it is a candidate for Today's one open action", w.gmFocusCands().some(c => c.id === "spend-checkin"));
  // saving through the form: partner input, cap
  w.goTab("money"); w.renderAll();
  d.getElementById("gmCkMe").value = "330000"; d.getElementById("gmCkPt").value = "120000"; w.gmCheckinSaveForm();
  const sc = JSON.parse(ls.getItem("gm_spendcheck"));
  ok("saving stores me, partner and the date under the month", sc[ym(0)] && sc[ym(0)].me === 330000 && sc[ym(0)].partner === 120000 && !!sc[ym(0)].at, JSON.stringify(sc));
  ok("the profile follows once real spend exists (one source)", JSON.parse(ls.getItem("sovP")).exp > 0 && JSON.parse(ls.getItem("sovP")).expFrom === "checkin");
  ok("done: no longer due", w.gmSpendDue() === 0);
  ok("done: one quiet line instead of the form", /Next one on the 1st/.test((d.querySelector("#sections") || d.body).textContent) && !d.getElementById("gmCkMe"));
  const big = {}; for (let i = 1; i <= 40; i++) big[(2020 + Math.floor((i - 1) / 12)) + "-" + ("0" + (((i - 1) % 12) + 1)).slice(-2)] = { me: 1000 + i, partner: 0, at: "2020-01-01" };
  ls.setItem("gm_spendcheck", JSON.stringify(big)); w.renderAll();
  d.getElementById("gmCkMe") || w.goTab("money");
  // card is done-looking only when the month exists; add via save
  w.renderAll(); w.goTab("money");
  if (d.getElementById("gmCkMe")) { d.getElementById("gmCkMe").value = "5000"; w.gmCheckinSaveForm(); }
  ok("history is capped at 36 months", Object.keys(JSON.parse(ls.getItem("gm_spendcheck"))).length <= 36, Object.keys(JSON.parse(ls.getItem("gm_spendcheck"))).length);
  // wording
  const all = w.gmSpendCard() + w.gmNumbersCard();
  ok("no wife or husband wording", !/wife|husband/i.test(all) && !/wife|husband/i.test(fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8").slice(fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8").indexOf("Your real monthly spend") - 12000, fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8").indexOf("Your real monthly spend") + 12000)));
  // one earner
  const d2 = mk(Object.assign({}, prof, { earners: 1, psal: 0, partner: undefined, pname: "" }), { fSip: "30000", fEF: "10000" });
  setTimeout(() => {
    const w2 = d2.window, c2 = w2.gmSpendCard();
    ok("one earner gets one balance input and no partner wording", /id="gmCkMe"/.test(c2) && !/id="gmCkPt"/.test(c2) && !/Partner/.test(c2));
    console.log("test150 real spend: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x));
    process.exit(F ? 1 : 0);
  }, 1200);
}, 1500);
