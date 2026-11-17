// v124: the renewals desk on the Risk tab (queue renewals-desk, slice 1). Pick a template that expires, type its date
// once, and see the one to act on first; Renewed rolls it forward (or closes a once-only item).
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
const day = (n) => new Date(Date.now() + n * 864e5).toISOString().slice(0, 10);
const addM = (s, n) => { const t = new Date(Date.parse(s)); t.setUTCMonth(t.getUTCMonth() + n); return t.toISOString().slice(0, 10); };
setTimeout(() => {
  const w = dom.window, d = w.document;
  const risk = () => { w.goTab("risk"); return d.querySelector('.gm-renewals'); };
  const saved = () => { try { const a = JSON.parse(w.localStorage.getItem("gm_renewals") || "[]"); return Array.isArray(a) ? a : []; } catch (x) { return []; } };
  let card = risk();

  ok("the Risk tab shows the renewals desk", !!card, card ? "no .gm-renewals card" : "no card");
  ok("every template travelled with the app", !!w.GM_RENEWALS && Array.isArray(w.GM_RENEWALS.renewals) && w.GM_RENEWALS.renewals.length === 12,
    w.GM_RENEWALS ? String((w.GM_RENEWALS.renewals || []).length) : "no GM_RENEWALS");
  ok("with nothing added, an example line invites the first one", !!card && /first one/i.test(card.textContent),
    card ? card.textContent.slice(0, 160) : "no card");

  if (card) {
    const pick = d.getElementById("gmRenewPick"), date = d.getElementById("gmRenewDate"), add = d.querySelector('[data-renew-add]');
    ok("the desk offers a template picker and its date", !!(pick && date && add), "missing picker, date or add");
    const amfDate = day(20);
    if (pick && date && add) { pick.value = "isc2-amf"; date.value = amfDate; add.click(); }
    const a = saved();
    ok("adding a template stores it in gm_renewals", a.length === 1 && a[0].id === "isc2-amf" && a[0].date === amfDate, JSON.stringify(a));
    card = risk();
    const openOne = card && card.querySelector('[data-renew-open="isc2-amf"]');
    ok("the added renewal shows its name, cost and check line", !!openOne
      && /ISC2 annual fee/.test(openOne.textContent) && /US\$135 a year/.test(openOne.textContent) && /amount on your dashboard/.test(openOne.textContent),
      openOne ? openOne.textContent.slice(0, 200) : "not shown");
  }

  // Two items inside their lead days: the higher lapse (ISC2, 3) is the one action, the other folds under Later.
  const amfDate = day(20), pucDate = day(5);
  w.localStorage.setItem("gm_renewals", JSON.stringify([{ id: "isc2-amf", date: amfDate }, { id: "puc", date: pucDate }]));
  card = risk();
  const openOne = card && card.querySelector('[data-renew-open]');
  const later = card && card.querySelector('.gm-renew-later summary');
  ok("the open item is the one inside its lead days with the highest lapse", !!openOne && openOne.getAttribute("data-renew-open") === "isc2-amf",
    openOne ? openOne.getAttribute("data-renew-open") : "no open item");
  ok("the rest fold under Later (n)", !!later && /Later \(1\)/.test(later.textContent) && /Pollution under control/.test(later.parentNode.textContent),
    later ? later.textContent : "no Later fold");

  const renewBtn = card && card.querySelector('[data-renew-done="isc2-amf"]');
  ok("the open renewal offers Renewed", !!renewBtn, "no Renewed button");
  if (renewBtn) renewBtn.click();
  const after = saved().filter((x) => x.id === "isc2-amf")[0];
  ok("Renewed moves the date forward by its every-months", !!after && after.date === addM(amfDate, 12) && !after.done,
    JSON.stringify(saved()));

  // A once-only item (every 0) is not rolled forward: it is marked done.
  w.localStorage.setItem("gm_renewals", JSON.stringify([{ id: "passport", date: day(200) }]));
  card = risk();
  const onceBtn = card && card.querySelector('[data-renew-done="passport"]');
  ok("a once-only item can be renewed too", !!onceBtn, "no Renewed button for passport");
  if (onceBtn) onceBtn.click();
  const p = saved().filter((x) => x.id === "passport")[0];
  ok("a once-only item is marked done, not rolled forward", !!p && p.done === true, JSON.stringify(saved()));

  // Several of one kind: two vehicles' PUC are two items, each with its own label and Renewed button.
  w.localStorage.setItem("gm_renewals", JSON.stringify([]));
  card = risk();
  ["Car", "Bike"].forEach((lab) => {
    const pick = d.getElementById("gmRenewPick"), date = d.getElementById("gmRenewDate"), label = d.getElementById("gmRenewLabel"), add = d.querySelector('[data-renew-add]');
    if (pick && date && label && add) { pick.value = "puc"; label.value = lab; date.value = day(5); add.click(); }
  });
  const two = saved();
  ok("two of one kind are kept apart by their label", two.length === 2 && two.every(x => x.id === "puc") && new Set(two.map(x => x.uid)).size === 2, JSON.stringify(two));
  card = risk();
  ok("each shows its label", !!card && /Car/.test(card.textContent) && /Bike/.test(card.textContent), card ? card.textContent.slice(0, 200) : "no card");
  // Nothing inside its warning days: no early Renewed action, one calm line naming the next.
  w.localStorage.setItem("gm_renewals", JSON.stringify([{ uid: "health-insurance", id: "health-insurance", date: day(200) }]));
  card = risk();
  ok("when nothing is due there is no Renewed action, only a calm line", !!card && !card.querySelector('.gm-renew-open') && /All current/.test(card.textContent),
    card ? card.textContent.slice(0, 200) : "no card");
  // A synced or restored file can plant an id that is not a template: it is ignored, never rendered.
  w.localStorage.setItem("gm_renewals", JSON.stringify([{ id: "x');window.__pwned=1;('", date: day(10) }]));
  card = risk();
  ok("a planted renewal id never reaches the card", !!card && !/pwned/.test(card.innerHTML), card ? card.innerHTML.slice(0, 200) : "no card");
  console.log("test124 renewals desk: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
