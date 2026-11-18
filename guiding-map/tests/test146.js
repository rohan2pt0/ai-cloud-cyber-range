// v146: exercise figures, Watch (owner 2026-11-18): one quiet button plays the movement from joint ANGLES at a real tempo
// with a rep count. gmFigureFrame(id, t) is pure, so no timers are needed here. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const boot = reduced => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: !!reduced && /prefers-reduced-motion/.test(q), media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const dom = boot(false), domR = boot(true);
const show = (w, h) => { const box = w.document.createElement("div"); box.innerHTML = h; return box; };
const num = (el, a) => parseFloat(el.getAttribute(a));
const len = l => Math.hypot(num(l, "x2") - num(l, "x1"), num(l, "y2") - num(l, "y1"));
const part = (fr, n) => fr.querySelector("[data-part='" + n + "']");
const pt = (l, k) => [num(l, "x" + k), num(l, "y" + k)];
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const strengthCard = w => [...w.document.querySelectorAll(".guide-card")].find(c => /30-min strength/.test(c.textContent));
setTimeout(() => {
  const w = dom.window, IDS = ["pushup", "row", "squat", "press", "plank"];
  const C = { torso: 30, neck: 4, uarm: 14, farm: 13, thigh: 18, shin: 18 };
  w.goTab("guide");
  const card = strengthCard(w); ok("strength guide present", !!card);
  const cards = card ? [...card.querySelectorAll(".gs-card")] : [];
  ok("five cards", cards.length === 5, cards.length);
  cards.forEach((c, i) => {
    const b = c.querySelectorAll("button.gm-watch");
    ok("card " + (i + 1) + ": one Watch button, aria-pressed false", b.length === 1 && b[0].type === "button" && b[0].getAttribute("aria-pressed") === "false" && /▶ Watch/.test(b[0].textContent), b.length);
  });
  ok("gmFigureFrame is a function", typeof w.gmFigureFrame === "function");
  ok("tempo table exposed", !!w.gmTempo && IDS.every(id => w.gmTempo[id] && w.gmTempo[id].down > 0));
  if (typeof w.gmFigureFrame !== "function" || !w.gmTempo) { done(); return; }
  const T = id => w.gmTempo[id], period = id => T(id).down + T(id).up + 2 * T(id).hold;
  const tempo = { pushup: [2, 1], row: [1, 2], squat: [2, 1], press: [1, 2] };
  Object.keys(tempo).forEach(id => ok(id + ": tempo " + tempo[id].join("/"), T(id).down === tempo[id][0] && T(id).up === tempo[id][1], JSON.stringify(T(id))));
  const frame = (id, t) => { const box = show(w, w.gmFigureFrame(id, t)); return { box, f: box.querySelector("g.gm-fig-frame") }; };
  const J = (f) => ({ hip: pt(part(f, "torso"), 1), sho: pt(part(f, "torso"), 2), knee: pt(part(f, "thigh"), 2), ank: pt(part(f, "shin"), 2), hand: pt(part(f, "farm"), 2), elbow: pt(part(f, "farm"), 1) });
  IDS.forEach(id => {
    const p = period(id);
    [0, .25, .5, .75].forEach(q => {
      const { box, f } = frame(id, q * p), tag = id + " @" + q;
      ok(tag + ": one svg, one figure, no pair", box.querySelectorAll("svg").length === 1 && box.querySelectorAll("g.gm-fig-frame").length === 1 && !box.querySelector(".gm-arrow"));
      Object.keys(C).forEach(k => { const l = f && part(f, k); ok(tag + ": " + k + " length", !!l && Math.abs(len(l) - C[k]) <= 1, l && len(l)); });
    });
    const svg = frame(id, 0).box.querySelector("svg"), pair = show(w, w.gmFigure(id)).querySelector("svg");
    ok(id + ": same box as the pair", svg.getAttribute("viewBox") === pair.getAttribute("viewBox") && svg.getAttribute("style") === pair.getAttribute("style"));
  });
  const joints = (id, which) => { const q = w.gmPoses[id][which], j = w.gmPoseJoints(q); return { hip: j.hip, sho: j.shoulder, knee: j.knee, ank: j.ankle, hand: j.hand, elbow: j.elbow }; };
  ["pushup", "row", "squat", "press"].forEach(id => {
    const a = J(frame(id, 0).f), s = joints(id, "start"), b = J(frame(id, T(id).down).f), n = joints(id, "end");
    ["hip", "sho", "knee", "ank", "hand", "elbow"].forEach(k => {
      ok(id + ": t=0 " + k + " = Start", dist(a[k], s[k]) <= 1, dist(a[k], s[k]));
      ok(id + ": end of down " + k + " = End", dist(b[k], n[k]) <= 1, dist(b[k], n[k]));
    });
    // progress of the hands along the Start-to-End direction never goes backwards (an arc may bow sideways, it may not stutter; 0.25 unit is under half a pixel)
    const dir = [b.hand[0] - a.hand[0], b.hand[1] - a.hand[1]], dl = Math.hypot(dir[0], dir[1]);
    let prev = -1, mono = dl > 1;
    for (let i = 0; i <= 20; i++) { const h = J(frame(id, T(id).down * i / 20).f).hand, dd = ((h[0] - a.hand[0]) * dir[0] + (h[1] - a.hand[1]) * dir[1]) / dl; if (dd < prev - 0.25) mono = false; prev = dd; }
    ok(id + ": hands move monotonically during the down phase", mono);
    const band = frame(id, T(id).down / 2).f.querySelector(".gm-band");
    if (band) ok(id + ": band follows the hands", dist(pt(band, 2), J(frame(id, T(id).down / 2).f).hand) < 1);
  });
  // counter
  const txt = (id, t) => (frame(id, t).box.querySelector(".gm-count") || {}).textContent;
  ok("pushup t=2.5 reps reads rep 3 / 12", txt("pushup", 2.5 * period("pushup")) === "rep 3 / 12", txt("pushup", 2.5 * period("pushup")));
  ok("pushup t=0 reads rep 1 / 12", txt("pushup", 0) === "rep 1 / 12");
  ok("squat counts to 15", txt("squat", 0.1) === "rep 1 / 15");
  // plank
  for (let t = 0; t <= 8; t += 0.5) {
    const { f } = frame("plank", t), j = J(f), dx = j.sho[0] - j.ank[0], dy = j.sho[1] - j.ank[1], n = Math.hypot(dx, dy);
    const dev = p => Math.abs((p[0] - j.ank[0]) * dy - (p[1] - j.ank[1]) * dx) / n;
    ok("plank t=" + t + ": straight line", dev(j.hip) <= 4 && dev(j.sho) <= 4);
    ok("plank t=" + t + ": counter in seconds", /^\d+ s$/.test(txt("plank", t) || ""), txt("plank", t));
  }
  ok("plank breathes (moves 1-2 units)", Math.abs(J(frame("plank", 0).f).hip[1] - J(frame("plank", 1).f).hip[1]) > 0.2);
  ok("plank counts down", parseInt(txt("plank", 0)) === 45 && parseInt(txt("plank", 10)) === 35, txt("plank", 10));
  // click behaviour
  const c0 = cards[0], c1 = cards[1], b0 = c0.querySelector(".gm-watch"), b1 = c1.querySelector(".gm-watch");
  const stage = c => c.querySelector(".gs-fig");
  ok("before: the pair", stage(c0).querySelectorAll("g.gm-fig-frame").length === 2);
  b0.click();
  ok("click: aria-pressed true and Stop label", b0.getAttribute("aria-pressed") === "true" && /■ Stop/.test(b0.textContent));
  ok("click: single figure in place of the pair", stage(c0).querySelectorAll("g.gm-fig-frame").length === 1 && stage(c0).querySelectorAll("svg").length === 1);
  b1.click();
  ok("second card plays", b1.getAttribute("aria-pressed") === "true" && stage(c1).querySelectorAll("g.gm-fig-frame").length === 1);
  ok("first card stopped, pair restored", b0.getAttribute("aria-pressed") === "false" && stage(c0).querySelectorAll("g.gm-fig-frame").length === 2);
  b1.click();
  ok("click again restores the pair", b1.getAttribute("aria-pressed") === "false" && stage(c1).querySelectorAll("g.gm-fig-frame").length === 2 && /▶ Watch/.test(b1.textContent));
  // reduced motion
  domR.window.goTab("guide");
  const cr = strengthCard(domR.window);
  ok("reduced motion: card renders, no Watch button", !!cr && cr.querySelectorAll(".gs-card").length === 5 && cr.querySelectorAll(".gm-watch").length === 0);
  done();
}, 1500);
function done() {
  console.log("test146 exercise figures Watch: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}
