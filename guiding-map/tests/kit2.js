// kit2: VISUALIZATION HONESTY. The class of bug that passed thousands of green checks — a chart that renders, has contrast,
// throws no error, yet LIES to the eye (the money Sankey that drew nothing; a wheel that drew "not scored yet" as a near-zero
// catastrophe; a sparkline that made a 0.1 wiggle look like a cliff). A visualization must distinguish "no data" from a real
// low value, and must not exaggerate the effect it shows (Tufte's lie factor ~ 1). This renders the kit's charts with the
// degenerate-data family (nothing / partial / all-equal / full) and asserts each one stays honest.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const PFX = "osk:vantage:";
const html = fs.readFileSync(path.join(__dirname, '..', 'vantage', 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/vantage/",
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; w.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) }); } });
const w = dom.window, d = w.document;
const K = () => w.OSK;
const main = () => d.getElementById("oskMain").innerHTML;
const seed = (k, v) => w.localStorage.setItem(PFX + k, JSON.stringify(v));
const dims = () => K().cfg("wheel").dims.map(function (x) { return x.id; });

setTimeout(() => {
  ok("the app started", !!K(), d.title);
  const D = dims(), N = D.length;

  // 1. A wheel with NOTHING scored must NOT draw a filled shape (the old bug plotted every axis at 0.3 — a crumpled near-zero
  //    polygon that reads as "my whole life is a catastrophe" when the truth is "not scored yet").
  seed("wheel", { s: {}, at: null, hist: [] });
  K().go("wheel");
  ok("empty wheel draws NO filled shape (no false catastrophe)", main().indexOf('class="shape"') < 0, main().slice(0, 160));
  ok("empty wheel says it is not scored yet, plainly", /not scored yet/i.test(main()));
  ok("empty wheel draws no value dots either", main().indexOf('class="dot"') < 0);

  // 2. A PARTIALLY scored wheel shows a dot per scored area but still no closed shape (a closed shape implies a full picture).
  const partial = {}; D.slice(0, 3).forEach(function (id) { partial[id] = 7; });
  seed("wheel", { s: partial, at: "2026-10-01", hist: [] });
  K().go("wheel");
  ok("partial wheel still draws no filled shape", main().indexOf('class="shape"') < 0);
  ok("partial wheel marks each scored area with a dot", (main().match(/class="dot"/g) || []).length === 3, String((main().match(/class="dot"/g) || []).length));

  // 3. A FULLY scored wheel draws the shape — the honest, complete picture.
  const full = {}; D.forEach(function (id) { full[id] = 6; });
  seed("wheel", { s: full, at: "2026-10-01", hist: [] });
  K().go("wheel");
  ok("fully scored wheel draws the filled shape", main().indexOf('class="shape"') >= 0);

  // 4. A sparkline auto-scales to fit, so a tiny change would look dramatic. A visible lo-hi range must ride with it so the
  //    reader knows the real scale (kills the lie factor). Two near-equal values:
  const m = K().cfg("scorecard").metrics[0].id;
  seed("score", (function () { var o = {}; o[m] = [{ v: 40, d: "2026-10-01" }, { v: 41, d: "2026-10-10" }]; return o; })());
  K().go("scorecard");
  ok("a sparkline shows its real lo-hi range (not a bare auto-scaled line)", /spark-range/.test(main()) && main().indexOf("40") >= 0 && main().indexOf("41") >= 0, (main().match(/spark-range[^<]*<[^>]*>[^<]*/) || [""])[0]);

  // 5. When nothing moved, say "flat" — never draw a line that implies a trend that is not there.
  seed("score", (function () { var o = {}; o[m] = [{ v: 50, d: "2026-10-01" }, { v: 50, d: "2026-10-10" }]; return o; })());
  K().go("scorecard");
  ok("a flat metric says 'flat', it does not fake a trend", /flat at 50/.test(main()));

  console.log("kit2 visualization honesty: " + P + " passed, " + F + " failed");
  if (F) { console.log(e.join("\n")); process.exit(1); } process.exit(0);
}, 400);
