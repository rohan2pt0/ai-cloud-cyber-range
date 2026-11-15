// v106: "Make it yours" (owner, 2026-11-15). A new person answers five things once, then the Life OS hides the doors
// and partner-only cards that do not apply; what is hidden is never a safety item, and "Show me everything" hides
// nothing. The answers live in gm_facts, so Menu -> Your life can change them later.
const fs = require("fs"), path = require("path"), { JSDOM } = require("jsdom");
let P = 0, F = 0, e = [];
const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
function boot(seed) {
  return new JSDOM(fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8"), {
    runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.localStorage.setItem("sovP", JSON.stringify(prof));
      w.localStorage.setItem("gm_intro_seen", "true");
      w.localStorage.setItem("gm_simple", "false");
      Object.keys(seed || {}).forEach(k => w.localStorage.setItem(k, JSON.stringify(seed[k])));
      w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    }
  });
}
const tap = (w, q, v) => {
  const b = w.document.querySelector('#gmMineSheet [data-mine="' + q + '"] [data-v="' + v + '"]');
  if (!b) return false;
  b.click(); return true;
};
const facts = (w) => JSON.parse(w.localStorage.getItem("gm_facts") || "{}");
const A = boot(), B = boot(), C = boot(), D = boot({ gm_facts: { stage: "student" }, gm_mine_done: true });
setTimeout(() => {
  // A: a new person sees one sheet with all five questions, and finishes with Student + four No.
  const wa = A.window, da = wa.document, sheet = () => da.getElementById("gmMineSheet");
  ok("a new person sees Make it yours", !!sheet() && /Make it yours/.test(sheet().textContent) && /Five taps/.test(sheet().textContent), sheet() ? sheet().textContent.slice(0, 120) : "no sheet");
  ok("it asks all five things on one screen", !!sheet() && sheet().querySelectorAll("[data-mine]").length === 5);
  ok("tapping Student works", tap(wa, "stage", "student"));
  ["partner", "kids", "home", "parents"].forEach(k => ok("tapping No for " + k + " works", tap(wa, k, "no")));
  da.querySelector("#gmMineSheet .gm-mine-done").click();
  const fa = facts(wa);
  ok("finishing saves the stage and every answer", fa.stage === "student" && fa.salaried === false && fa.business === false
    && fa.partner === false && fa.kids === false && fa.home === false && fa.parents === false, JSON.stringify(fa));
  ok("finishing closes the sheet and marks it done", !sheet() && JSON.parse(wa.localStorage.getItem("gm_mine_done")) === true);
  ok("finishing shows the one next step", /Your Life OS now fits you/.test((da.getElementById("gmToast") || {}).textContent || ""), (da.getElementById("gmToast") || {}).textContent);
  wa.gmNavMore(true);
  const moreText = (da.getElementById("gmMoreSheet") || {}).textContent || "";
  ok("the More sheet no longer lists the Kids door", !/Kids/.test(moreText), moreText);
  ok("the More sheet no longer lists the Property door", !/Property/.test(moreText), moreText);
  wa.goTab("ops");
  const opsText = (da.getElementById("sections") || {}).textContent || "";
  ok("the partner-only Spouse emergency page is hidden", opsText.indexOf("Spouse emergency page") < 0);

  // B: Show me everything hides nothing and records only that the sheet was answered.
  const wb = B.window, db = wb.document;
  const skip = [...db.querySelectorAll("#gmMineSheet button")].find(b => /Show me everything/.test(b.textContent));
  ok("the skip link is on the sheet", !!skip);
  if (skip) skip.click();
  ok("skip records only the decision and never a fact", JSON.parse(wb.localStorage.getItem("gm_mine_done")) === true && !wb.localStorage.getItem("gm_facts"));
  wb.gmNavMore(true);
  const moreAll = (db.getElementById("gmMoreSheet") || {}).textContent || "";
  ok("skip keeps the Kids door", /Kids/.test(moreAll));
  ok("skip keeps the Property door", /Property/.test(moreAll));
  wb.goTab("ops");
  const opsAll = (db.getElementById("sections") || {}).textContent || "";
  ok("skip keeps the Spouse emergency page", opsAll.indexOf("Spouse emergency page") >= 0);

  // C: Menu -> Your life reopens the sheet with the answers already chosen.
  const wc = C.window, dc = wc.document;
  ok("a second new person sees the sheet", !!dc.getElementById("gmMineSheet"));
  tap(wc, "stage", "salaried"); tap(wc, "partner", "yes");
  dc.querySelector("#gmMineSheet .gm-mine-done").click();
  wc.gmMenu();
  const yourLife = [...dc.querySelectorAll("#gmOverlay button")].find(b => /Your life/.test(b.textContent));
  ok("the Menu offers Your life", !!yourLife);
  if (yourLife) yourLife.click();
  ok("Your life reopens the same sheet", !!dc.getElementById("gmMineSheet"));
  const st = dc.querySelector('#gmMineSheet [data-mine="stage"] [data-v="salaried"]');
  const pa = dc.querySelector('#gmMineSheet [data-mine="partner"] [data-v="yes"]');
  ok("it remembers the stage", st && st.getAttribute("aria-pressed") === "true");
  ok("it remembers the partner answer", pa && pa.getAttribute("aria-pressed") === "true");

  // D: someone already answered is not asked again on the next visit.
  ok("a returning person is not asked again", !D.window.document.getElementById("gmMineSheet"));

  console.log("test106 make it yours: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
