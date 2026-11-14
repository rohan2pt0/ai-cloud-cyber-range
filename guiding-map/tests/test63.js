// v63: one consistent line-icon set in the More sheet. Every tab has a hand-drawn 24x24 stroke icon,
// the More sheet shows it above the plain label, and no tile falls back to an emoji.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const d = new JSDOM(html, {
  runScripts: "dangerously", url: "https://hub.securax.localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.confirm = () => false; w.alert = () => {}; w.fetch = () => Promise.reject(new Error("offline")); },
});
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) pass++; else { fail++; console.log("FAIL", m + (d ? " :: " + d : "")); } };
setTimeout(() => {
  const w = d.window, doc = w.document;
  const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
  const ids = w.TABS.map((t) => t[0]);
  ok(ids.length >= 23, "every tab is declared", String(ids.length));
  ids.forEach((id) => {
    const svg = w.gmIcon(id);
    ok(/^<svg /.test(svg) && /viewBox="0 0 24 24"/.test(svg) && /width="18"/.test(svg) && /height="18"/.test(svg)
      && /fill="none"/.test(svg) && /stroke="currentColor"/.test(svg) && /stroke-width="1.8"/.test(svg)
      && /stroke-linecap="round"/.test(svg) && /aria-hidden="true"/.test(svg) && /<\/svg>$/.test(svg),
      "gmIcon(" + id + ") is one line icon", svg.slice(0, 80));
  });
  ok(w.gmIcon("not-a-tab") === "", "an unknown id gives no icon");
  ok(/width="20"/.test(w.gmIcon("today", 20)) && /height="20"/.test(w.gmIcon("today", 20)), "the size is honoured");

  // Start simple (owner, 2026-11-14) shows three doors; every tab's icon is checked on the full menu (Show everything).
  w.gmNavMore(true);
  const simple = doc.getElementById("gmMoreSheet");
  ok([...simple.querySelectorAll(".sh button[role=menuitem]")].filter((b) => !/Show everything/.test(b.textContent)).every((b) => b.querySelector(".gi svg")), "the three simple doors carry their icons");
  w.gmSimple(false); w.gmNavMore(true);
  const sheet = doc.getElementById("gmMoreSheet");
  ok(sheet && sheet.classList.contains("on"), "the More sheet opens");
  const main = ["today", "inbox", "okr", "ask"];
  const tiles = w.TABS.filter((t) => main.indexOf(t[0]) < 0);
  const buttons = Array.from(sheet.querySelectorAll(".sh button"));
  ok(buttons.length === tiles.length + 2, "one tile per other tab, plus All apps and Back to simple");
  tiles.forEach((t, i) => {
    const b = buttons.find((x) => (x.getAttribute("onclick") || "").indexOf("'" + t[0] + "'") >= 0), gi = b && b.firstElementChild;
    ok(!!b && !!gi && gi.classList.contains("gi") && gi.querySelectorAll("svg").length === 1, t[0] + ": one icon above the label");
    ok(!EMOJI.test(b ? b.textContent : ""), t[0] + ": the tile text has no emoji", b && b.textContent);
    ok(!!b && b.textContent.indexOf(t[1]) >= 0, t[0] + ": the plain label stays");
  });
  const css = (doc.getElementById("gmNavCss") || {}).textContent || "";
  ok(/#gmMoreSheet \.sh button \.gi\{[^}]*color:var\(--text\)/.test(css), "the icon is the text colour on light");
  ok(/html\[data-theme=dark\] #gmMoreSheet \.sh button \.gi\{color:var\(--gold\)\}/.test(css), "the icon is gold on dark");
  const barText = Array.from(doc.querySelectorAll("#tabBar .tab")).map((x) => x.textContent).join(" ");
  ok(!EMOJI.test(barText), "the wide tab bar labels stay plain words", barText.slice(0, 120));

  console.log("test63 line icons in the More sheet: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1200);
