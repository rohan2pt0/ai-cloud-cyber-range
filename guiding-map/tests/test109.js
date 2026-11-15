// v109: Career step 4 was a wall of twelve fields (owner, 2026-11-15: the biggest card on each tab must be the
// best). Filled fields fold into one closed <details>; the first three empty fields stay open for a newcomer and
// the rest wait under "Add more"; the spouse field disappears when the person said they have no partner. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("gm_simple", "false");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  const openInputs = () => [...sec().querySelectorAll("input")].filter(i => !i.closest("details"));
  const show = (c) => { w.localStorage.setItem("gm_career", JSON.stringify(c)); w.goTab("career"); };

  w.localStorage.removeItem("gm_career");
  w.goTab("career");
  ok("an empty career file shows three open input fields", openInputs().length === 3, openInputs().length + " open");
  const more = sec().querySelector("details.car-more summary");
  ok("…and the rest wait under Add more", !!more && /Add more \(\d+\)/.test(more.textContent), more && more.textContent);
  ok("…with nothing folded as filled yet", !sec().querySelector("details.car-filled"), "a filled card exists");

  show({ cur: { gross: 100000 }, house: { exp: 50000 } });
  const filled = sec().querySelector("details.car-filled");
  const summary = filled && filled.querySelector("summary");
  ok("fields with a value fold into one closed details", !!filled && filled.open === false && !!summary && /Your figures \(2 filled\) · tap to change/.test(summary.textContent), summary && summary.textContent);
  const vals = filled ? [...filled.querySelectorAll("input")].map(i => i.value) : [];
  ok("…holding exactly the two filled fields", vals.includes("100000") && vals.includes("50000"), vals.join(","));

  w.localStorage.setItem("gm_facts", JSON.stringify({ partner: false }));
  w.goTab("career");
  ok("no partner leaves the spouse field out", !sec().querySelector('input[onchange*="house.wife"]'), "spouse input present");
  w.localStorage.setItem("gm_facts", JSON.stringify({ partner: true }));
  w.goTab("career");
  ok("a partner keeps the spouse field", !!sec().querySelector('input[onchange*="house.wife"]'), "spouse input missing");

  console.log("test109 career step 4 folded: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
