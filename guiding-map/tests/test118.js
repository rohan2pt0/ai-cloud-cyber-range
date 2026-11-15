// v118: the expert council, item 2: pre-flight checklists before big moments (a pilot's and a surgeon's habit, for anyone):
// signing an agreement, a job offer, buying a home, a planned hospital admission, a big purchase, travel abroad. Pick the
// moment, tick the checks, see "N of M checked" as a gemstone, start again next time. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify({ name: "Fake", dob: "1988-02-02", gross: 200000, net: 150000, exp: 70000, kids: [], loans: [], example: false }));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  let html = ""; try { html = w.gmPreflightHTML(); } catch (x) { html = "ERR " + x.message; }
  ok("the card renders without an error", html.indexOf("ERR") !== 0 && /Before a big moment/.test(html), html.slice(0, 80));
  ok("six moments travel with the app", (w.GM_COUNCIL.checklists || []).length === 6);
  w.goTab("risk");
  ok("the Risk tab offers the moments, none open yet", d.querySelectorAll(".gm-pf .chip").length === 6 && !d.querySelector(".gm-pf-open"));
  w.gmPfOpen("hospital");
  const open = () => d.querySelector(".gm-pf-open");
  ok("choosing a moment opens its checklist", !!open() && open().getAttribute("data-pf") === "hospital" && /room-rent limit/.test(open().textContent));
  ok("it starts at 0 checked as a ruby stone", /0 of 5 checked/.test(open().textContent) && !!open().querySelector(".sx-state-low"));
  w.gmPfTick("hospital", 0); w.gmPfTick("hospital", 1);
  ok("ticks count, amber while partly done", /2 of 5 checked/.test(open().textContent) && !!open().querySelector(".sx-state-watch"));
  [2, 3, 4].forEach(i => w.gmPfTick("hospital", i));
  ok("every check done is an emerald", /5 of 5 checked/.test(open().textContent) && !!open().querySelector(".sx-state-good"));
  w.gmPfReset("hospital");
  ok("Start again clears it for the next admission", /0 of 5 checked/.test(open().textContent));
  w.gmPfOpen("hospital");
  ok("tapping the moment again closes it", !d.querySelector(".gm-pf-open"));
  console.log("test118 before a big moment: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
