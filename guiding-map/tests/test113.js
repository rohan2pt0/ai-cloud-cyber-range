// v113: one fact, one place (owner, 2026-11-15: the same value is asked on three or four screens). The profile is
// the one source: on the Life Map and Career a fact the profile already holds is shown as a line with "from your
// profile · change", never a second input, unless the person typed their own value on that screen. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1988-02-02", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 70000,
  sav: 900000, nw: 3000000, psal: 50000, ret: 55, kids: [], loans: [], tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const onchange = () => [...d.querySelectorAll("#sections input")].map(x => x.getAttribute("onchange") || "").join("\n");
  w.goTab("life");
  let s = onchange();
  ok("the Life Map asks no second time for household income", !s.includes("gmLifeSet('inc'"), s);
  ok("the Life Map asks no second time for net worth", !s.includes("gmLifeSet('nw'"), s);
  ok("the Life Map asks no second time for the emergency fund", !s.includes("gmLifeSet('ef'"), s);
  ok("Where the money goes asks no second time for take-home", !s.includes("gmLifeSet('minc'"), s);
  ok("Where the money goes asks no second time for fixed costs", !s.includes("gmLifeSet('fFixed'"), s);
  const text = d.getElementById("sections").innerHTML;
  const lines = (text.match(/from your profile/g) || []).length;
  ok("each profile fact is shown as a line, not an input (five on the Life Map)", lines >= 5, lines + " lines");
  const link = d.querySelector("#sections .gm-fromp a.gm-inl");
  ok("the change link opens the one profile form", !!link && /editProfile\(\)/.test(link.getAttribute("onclick") || ""),
    link ? link.outerHTML : "no link");

  w.goTab("career");
  s = onchange();
  ok("Career asks no second time for the in-hand salary", !s.includes("gmCarSet('cur.inhand'"), s);
  ok("Career asks no second time for household essentials", !s.includes("gmCarSet('house.exp'"), s);
  ok("Career asks no second time for the spouse's take-home", !s.includes("gmCarSet('house.partner'"), s);

  w.P.example = true;
  w.goTab("life");
  s = onchange();
  ok("with the example profile the Life Map still asks for net worth", s.includes("gmLifeSet('nw'"), s);
  ok("with the example profile the Life Map still asks for the emergency fund", s.includes("gmLifeSet('ef'"), s);

  console.log("test113 one fact, one place: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
