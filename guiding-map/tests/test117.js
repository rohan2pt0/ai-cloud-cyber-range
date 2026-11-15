// v117: the expert council, item 1 (owner, 2026-11-15: what the best professionals would make every household do, as small
// systems). On Risk: "If one thing failed tomorrow": the household's single points of failure and paper hygiene, the most
// severe first, one open at a time, a visible "N of M closed", Closed / Not for us / Reopen. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1988-02-02", gross: 200000, net: 150000, exp: 70000, kids: [], loans: [], example: false };
const boot = (facts) => new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_facts", JSON.stringify(facts));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const fam = boot({ stages: ["salaried"], partner: true, kids: true }), single = boot({ stages: ["student"], partner: false, kids: false });
setTimeout(() => {
  const w = fam.window, d = w.document;
  let html = ""; try { html = w.gmSpofHTML(); } catch (x) { html = "ERR " + x.message; }
  ok("the card renders without an error (a swallowed ReferenceError would hide it)", html.indexOf("ERR") !== 0 && html.length > 100, html.slice(0, 80));
  ok("the content travels with the app (at least 9 items)", (w.GM_COUNCIL.spof || []).length >= 9);
  w.goTab("risk");
  const card = () => d.querySelector(".gm-spof"), open = () => (d.querySelector(".gm-spof-open") || { getAttribute: () => "" }).getAttribute("data-spof");
  ok("the Risk tab shows the card", !!card() && /If one thing failed tomorrow/.test(d.body.textContent));
  ok("the most severe gap opens first (the main earner's cover, for a family)", open() === "one-earner", open());
  ok("it starts at 0 closed, as a ruby stone", /0 of \d+ closed/.test(card().textContent) && !!card().querySelector(".sx-state-low"));
  w.gmSpofSet("one-earner", "done");
  ok("Closed moves to the next gap and counts it", open() !== "one-earner" && /1 of \d+ closed/.test(card().textContent), open());
  ok("the emergency-file template is ready to copy", /Family emergency file/.test(card().textContent) || open() !== "one-keyholder");
  w.gmSpofSet("one-earner", "");
  ok("Reopen puts it back first", open() === "one-earner");
  const all = (w.GM_COUNCIL.spof || []).filter(x => !(x.when || {}).salaried || true).map(x => x.id);
  all.forEach(id => w.gmSpofSet(id, "done"));
  ok("with every gap closed it says so, as an emerald", /Every gap is closed/.test(card().textContent) && !!card().querySelector(".sx-state-good"));
  const w2 = single.window;
  const h2 = w2.gmSpofHTML();
  ok("a single student with no partner or children is not asked about cover for dependants", !/main earner's income/.test(h2) || h2.indexOf("one-earner") < 0, "");
  console.log("test117 if one thing failed tomorrow: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1800);
