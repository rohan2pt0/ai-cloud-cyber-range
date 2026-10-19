// Phone navigation: four fixed bottom tabs + More (no tab hidden off-screen), Today shows the Daily Three and the one open
// action first with the rest folded, the vitals sit at the top of Today, and the header shrinks once you scroll.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const d = new JSDOM(html, {
  runScripts: "dangerously", url: "https://hub.securax.localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; },
});
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
setTimeout(() => {
  const w = d.window, doc = w.document;
  w.goTab("today");
  const nav = doc.getElementById("gmNav");
  ok(nav && nav.querySelectorAll("button").length === 5, "five bottom buttons");
  ok(["Today", "Goals", "Ask", "Ops", "More"].every((t) => nav.textContent.indexOf(t) >= 0), "Today, Goals, Ask, Ops, More");
  ok(/#tabBar\{display:none!important\}/.test(doc.getElementById("gmNavCss").textContent), "the sideways strip is hidden on a phone");
  const sheet = doc.getElementById("gmMoreSheet");
  const others = w.TABS.filter((t) => ["today", "okr", "ask", "ops"].indexOf(t[0]) < 0).length;
  ok(sheet.querySelectorAll("button").length === others + 1, "More lists every other tab, plus All apps");
  ok(doc.querySelector("#sections #gmVitals.gm-inline"), "vitals at the top of Today, not a second bottom bar");
  const sec = doc.getElementById("sections").innerHTML;
  const more = doc.querySelector(".gm-more-today");
  ok(more && !more.open, "the rest of Today is folded behind More today");
  ok(sec.indexOf("gm-more-today") > sec.indexOf("DAILY") || sec.toUpperCase().indexOf("DAILY THREE") < sec.indexOf("gm-more-today"), "the Daily Three comes before the fold");
  w.gmNavMore(true);
  ok(doc.getElementById("gmMoreSheet").classList.contains("on"), "More opens the sheet");
  w.gmNavGo("okr");
  ok(w.curTab === "okr" && !doc.getElementById("gmMoreSheet").classList.contains("on"), "choosing a tab closes the sheet");
  ok(doc.querySelector("#gmNav button.on").textContent.indexOf("Goals") >= 0, "the current tab is lit");
  w.gmNavGo("kids");
  ok(doc.querySelector("#gmNav button.on").textContent.indexOf("More") >= 0, "a tab inside More lights More");
  Object.defineProperty(w, "scrollY", { value: 200, configurable: true });
  w.dispatchEvent(new w.Event("scroll"));
  setTimeout(() => {
    ok(doc.body.classList.contains("gm-compact"), "the header shrinks to one line after scrolling");
    console.log("test24 phone navigation: " + pass + " passed, " + fail + " failed");
    process.exit(fail ? 1 : 0);
  }, 100);
}, 800);
