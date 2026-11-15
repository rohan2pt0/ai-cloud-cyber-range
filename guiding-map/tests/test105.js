// v105: the boot veil (owner 2026-11-15: the app froze on the old legacy screen before the lock showed). Nothing of the
// page shows until the Life OS has drawn its own first screen; a locked app is locked from the first frame; the veil
// always lifts (on the first draw, or after 4 s at the latest) so an error can never leave a blank page.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const head = html.slice(0, html.indexOf('</head>'));
ok("the veil is set in the head, before any app code", /classList\.add\("gm-boot"\)/.test(head) && head.indexOf('gm-boot') < head.indexOf('<script src') + 1e9);
ok("a stored lock locks the page from the first frame", /getItem\("gm_lock"\)\)d\.classList\.add\("gm-locked"\)/.test(head));
ok("there is a time-out release", /setTimeout\(function\(\)\{d\.classList\.remove\("gm-boot"\);\},4000\)/.test(head));
ok("the veil hides everything but the lock", /html\.gm-boot body>\*:not\(#gmLock\)/.test(head));
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
// a damaged lock record ({} with no credential) must never leave the veil's locked guess in place: a blank page is a lock-out
const dmg = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("gm_lock", "{}"); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const dd = dmg.window.document;
  ok("a damaged lock record leaves no hidden page (the locked guess is cleared)", !dd.documentElement.classList.contains("gm-locked") && !dd.getElementById("gmLock"),
    dd.documentElement.className);
  const d = dom.window.document;
  ok("the veil lifts once the Life OS has drawn its first screen", !d.documentElement.classList.contains("gm-boot"));
  ok("…and the app is there", !!d.querySelector("#sections .section"));
  console.log("test105 boot veil: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
