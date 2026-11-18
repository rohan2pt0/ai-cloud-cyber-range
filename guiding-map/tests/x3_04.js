// x3_04: the habit check is a named button (experience-v3, fix 4 of 20). In the full Today view each check is a real
// <button type="button"> with a truthful aria-pressed and an aria-label that names the habit, and Enter or Space toggles
// it. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_calm", "false");
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("today");
  const rows = [...d.querySelectorAll("#sections .hab")];
  const checks = rows.map(r => r.querySelector(".hab-chk"));
  ok("the full Today shows a check for every habit", rows.length === w.HABITS.length && checks.every(Boolean),
    rows.length + " rows, " + checks.filter(Boolean).length + " checks");
  ok("every habit check is a button type=button", checks.length > 0 && checks.every(b => b && b.tagName === "BUTTON" && b.getAttribute("type") === "button"),
    checks.map(b => b && b.tagName).join(","));
  ok("every check carries aria-pressed true or false", checks.length > 0 && checks.every(b => b && (b.getAttribute("aria-pressed") === "true" || b.getAttribute("aria-pressed") === "false")),
    checks.map(b => b && b.getAttribute("aria-pressed")).join(","));
  const sorted = rows.every((r, i) => { const b = checks[i]; return b && (b.getAttribute("aria-label") || "").indexOf(w.HABITS[i].name) >= 0; });
  ok("every check's aria-label contains its habit name", rows.length > 0 && sorted,
    rows.map((r, i) => checks[i] && checks[i].getAttribute("aria-label")).join(" | "));

  const btn = () => d.querySelectorAll("#sections .hab-chk")[0];
  const press = (key) => btn().dispatchEvent(new w.KeyboardEvent("keydown", { key: key, bubbles: true, cancelable: true }));
  const first = btn() && btn().getAttribute("aria-pressed");
  press("Enter");
  ok("Enter toggles the check", btn() && btn().getAttribute("aria-pressed") !== first,
    first + " -> " + (btn() && btn().getAttribute("aria-pressed")));
  const afterEnter = btn() && btn().getAttribute("aria-pressed");
  press(" ");
  ok("Space toggles it back", btn() && btn().getAttribute("aria-pressed") !== afterEnter,
    afterEnter + " -> " + (btn() && btn().getAttribute("aria-pressed")));

  console.log("x3_04 habit check button: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
