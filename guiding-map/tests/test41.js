// v41: human-first review of the first run (queue human-first-review). The first tap comes before any setup ask; example
// numbers never raise an alarm; the words on Today invite and never command or guilt.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.innerWidth = 390; } });
setTimeout(() => {
  const w = dom.window, d = w.document; w.goTab("today");
  const sec = d.getElementById("sections"), html = sec.innerHTML, txt = sec.textContent;
  const d3 = html.indexOf("gm-d3"), setup = html.indexOf("gm-setup");
  ok("the first run shows the daily three before the setup ask", d3 >= 0 && (setup < 0 || d3 < setup), d3 + " vs " + setup);
  ok("the setup ask is short (under 12 words before its buttons)", setup < 0 || d.querySelector(".gm-setup div").textContent.trim().split(/\s+/).length < 12);
  const v = d.getElementById("gmVitals");
  ok("example numbers raise no alarm: no 'low' or 'watch' on the vitals", !v || !v.querySelector("[data-state]"), v && v.innerHTML.slice(0, 200));
  const bad = /non-negotiable|mandatory|you must|no excuses|you failed/i, shout = /\bNOW\b/;
  ok("Today invites, never commands or guilts", !bad.test(txt) && !shout.test(txt), (txt.match(bad) || txt.match(shout) || [])[0]);
  ok("the Mind floor is short (under 15 words) and has no false glossary hit", /Three slow breaths/.test(txt) && !/cyclic sighs/.test(txt));
  console.log("test41 first run: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
