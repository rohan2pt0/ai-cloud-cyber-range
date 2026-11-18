// v138: every strength move shows how it is done (queue visual-guides, slice 2 of 3). Each of the five strength steps
// carries one small moving stick figure (start and end pose, about 3 s), the band is drawn from its anchor to the hand on
// the row and the press, the figure stays at most 140 px wide, and reduced motion rests on the end pose. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const show = (w, html) => { const box = w.document.createElement("div"); box.innerHTML = html; return box; };
setTimeout(() => {
  const w = dom.window, d = w.document;
  if (typeof w.gmFigure !== "function") { ok("gmFigure is available", false); }
  else {
    ["pushup", "row", "squat", "press", "plank"].forEach(id => {
      const box = show(w, w.gmFigure(id)), svgs = box.querySelectorAll("svg"), svg = svgs[0];
      ok(id + " is one svg", svgs.length === 1, svgs.length + " svg");
      if (!svg) return;
      ok(id + " is a picture for a screen reader", svg.getAttribute("role") === "img" && (svg.getAttribute("aria-label") || "").length > 3, svg.getAttribute("role") + " / " + svg.getAttribute("aria-label"));
      ok(id + " has a start and an end frame", svg.querySelectorAll("g.gm-fig-frame").length === 2, svg.querySelectorAll("g.gm-fig-frame").length + " frames");
      ok(id + " does not animate (v140)", svg.querySelectorAll("animate").length === 0);
      const width = parseFloat((svg.getAttribute("style") || "").replace(/.*max-width:(\d+)px.*/, "$1")) || parseFloat((svg.getAttribute("style") || "").replace(/.*max-width:(\d+)px.*/, "$1"));
      ok(id + " is at most 260 px wide", width > 0 && width <= 260, width + " px");
    });
    ["row", "press"].forEach(id => {
      const box = show(w, w.gmFigure(id));
      const band = box.querySelector(".gm-band, line[stroke='var(--gold)']");
      ok(id + " draws the band in gold from an anchor to a hand", !!band && /var\(--gold\)/.test(band.getAttribute("stroke") || "") && band.hasAttribute("x1") && band.hasAttribute("x2"), band && band.getAttribute("stroke"));
    });
    ok("an unknown move draws nothing", w.gmFigure("no-such-move") === "", JSON.stringify(w.gmFigure("no-such-move")));
  }
  w.goTab("guide");
  const card = [...d.querySelectorAll(".guide-card")].find(c => /30-min strength/.test(c.textContent));
  ok("the strength guide is on the Guides tab", !!card);
  if (card) {
    const list = card.querySelector(".gs-list");
    const steps = list ? [...list.querySelectorAll(".gs")] : [];
    ok("the strength guide has five steps", steps.length === 5, steps.length + " steps");
    steps.forEach((st, i) => {
      const figs = st.querySelectorAll("svg[role='img']");
      ok("step " + (i + 1) + " shows exactly one figure beside its text", figs.length === 1 && !!st.querySelector(".gs-v"), figs.length + " figures");
    });
  }
  console.log("test138 strength figures: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
