// v66: Life systems — the recipes run from a few facts asked once. With no facts answered only the systems that need
// nothing run; the hero counts them; a farmland fact reveals its card and its three lists; the region switch marks
// India-only steps; the one open action advances when ticked, and nothing unescaped or undefined reaches the page.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "", pdob: "", psal: 0, parents: false, kids: [], loans: [], ret: 50, tsav: 20,
  dream: "A calm life", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  const S = w.GM_SYSTEMS;
  ok("GM_SYSTEMS is present", !!S && Array.isArray(S.systems), S && Object.keys(S));
  ok("GM_SYSTEMS has at least 10 systems", !!S && S.systems.length >= 10, S && S.systems.length);
  if (!S) { console.log("test66 life systems: " + P + " passed, " + F + " failed"); process.exit(1); }
  const runsWithNothing = S.systems.filter(s => !(s.when && s.when.length));
  w.goTab("systems");
  let h = sec();
  const count = +(h.querySelector(".gm-hero-n") || {}).textContent;
  ok("hero counts the systems that run with no facts", count === runsWithNothing.length, count + " vs " + runsWithNothing.length);
  ok("hero says systems running", /systems running/i.test(h.textContent));
  ok("hero says it does the remembering", /remembering/i.test(h.textContent));
  const cards = [...h.querySelectorAll('details[id^="gmsys-"]')].map(x => x.id.replace("gmsys-", ""));
  const needsFact = cards.filter(id => { const s = S.systems.find(x => x.id === id); return s && s.when && s.when.length; });
  ok("only systems with an empty when run at first", needsFact.length === 0, needsFact.join(","));
  ok("the facts card names the questions", /A few questions, once/.test(h.textContent) && /own farmland/i.test(h.textContent));
  ok("the facts card has the region switch", /Local: India/.test(h.textContent) && /Global/.test(h.textContent));
  const nextBefore = (h.querySelector("#gmSysNext") || {}).textContent || "";
  const done = h.querySelector('#gmSysNext [data-haptic="success"]');
  ok("one open action offers Done", /buy-once test/i.test(nextBefore) && !!done, nextBefore.slice(0, 80));
  if (done) done.click();
  ok("Done stores the id with today's date", Object.keys(JSON.parse(w.localStorage.getItem("gm_sys_done") || "{}")).length > 0);
  const nextAfter = (sec().querySelector("#gmSysNext") || {}).textContent || "";
  ok("the open action moves on after Done", nextAfter !== nextBefore, nextBefore.slice(0, 60) + " -> " + nextAfter.slice(0, 60));
  ok("no NaN on the systems screen", !/NaN/.test(sec().textContent));
  ok("no undefined on the systems screen", !/undefined/.test(sec().textContent));
  ok("no raw script from content", !/<script/i.test(sec().innerHTML));

  w.localStorage.setItem("gm_facts", JSON.stringify({ farmland: true }));
  w.renderAll(); w.goTab("systems");
  h = sec();
  const farm = h.querySelector("#gmsys-farmland");
  ok("setting farmland true runs its system", !!farm);
  ok("farmland shows Make it earn", !!farm && /Make it earn/.test(farm.textContent));
  ok("farmland shows If the land is acquired", !!farm && /If the land is acquired/.test(farm.textContent));
  ok("farmland shows Buying land later", !!farm && /Buying land later/.test(farm.textContent));
  ok("farmland names a source with its checked date", !!farm && /Source: .+, checked \d{4}-\d{2}-\d{2}/.test(farm.textContent));
  ok("the hero count rises with the new system", +(h.querySelector(".gm-hero-n") || {}).textContent === count + 1);

  w.localStorage.setItem("gm_region", JSON.stringify("global"));
  w.renderAll(); w.goTab("systems");
  h = sec();
  const farmG = h.querySelector("#gmsys-farmland");
  ok("Global hides or marks the India-only farmland card", !farmG || /India only/.test(farmG.textContent), farmG ? farmG.textContent.slice(0, 80) : "hidden");
  ok("no undefined after the region switch", !/undefined/.test(sec().textContent));
  console.log("test66 life systems: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
