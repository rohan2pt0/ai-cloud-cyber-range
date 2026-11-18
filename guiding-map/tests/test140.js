// v140: exercise figures v2 (owner 2026-11-18): Start and End frames, bodies from joint angles. Fake data only.
// (v138 header follows)
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
const num = (el, a) => parseFloat(el.getAttribute(a));
const len = l => Math.hypot(num(l, "x2") - num(l, "x1"), num(l, "y2") - num(l, "y1"));
const part = (fr, n) => fr.querySelector("[data-part='" + n + "']");
const pt = (l, k) => [num(l, "x" + k), num(l, "y" + k)];
const frames = (w, id) => { const box = show(w, w.gmFigure(id)); return { box, start: box.querySelector("[data-frame='start']"), end: box.querySelector("[data-frame='end']") }; };
setTimeout(() => {
  const w = dom.window, IDS = ["pushup", "row", "squat", "press", "plank"];
  const C = { torso: 30, neck: 4, uarm: 14, farm: 13, thigh: 18, shin: 18 };
  ok("gmFigure('nope') is empty", w.gmFigure("nope") === "");
  IDS.forEach(id => {
    const { box, start, end } = frames(w, id), svg = box.querySelector("svg");
    ok(id + ": one svg role=img with a label", box.querySelectorAll("svg").length === 1 && svg.getAttribute("role") === "img" && (svg.getAttribute("aria-label") || "").length > 10);
    const fr = box.querySelectorAll("g.gm-fig-frame");
    ok(id + ": two frames", fr.length === 2, fr.length);
    ok(id + ": Start and End text", start && end && /Start/.test(start.textContent) && /End/.test(end.textContent));
    ok(id + ": an arrow between", box.querySelectorAll(".gm-arrow").length === 1);
    ok(id + ": a floor line in each frame", box.querySelectorAll("g.gm-fig-frame .gm-floor").length === 2);
    ok(id + ": no animation", box.querySelectorAll("animate, animateTransform, animateMotion, set").length === 0);
    const vw = parseFloat((svg.getAttribute("viewBox") || "").split(/\s+/)[2]), mw = parseFloat((svg.getAttribute("style") || "").replace(/.*max-width:\s*([\d.]+)px.*/, "$1"));
    ok(id + ": fits (viewBox and max-width <= 260)", vw > 0 && vw <= 260 && mw > 0 && mw <= 260, vw + "/" + mw);
    [start, end].forEach((f, i) => {
      if (!f) return;
      const tag = id + "/" + (i ? "end" : "start");
      Object.keys(C).forEach(k => { const l = part(f, k); ok(tag + ": " + k + " length " + C[k], !!l && Math.abs(len(l) - C[k]) <= 1, l && len(l)); });
      const hd = f.querySelector(".gm-head"); ok(tag + ": head radius 6", !!hd && Math.abs(num(hd, "r") - 6) <= 1);
      f.querySelectorAll(".gm-limb").forEach(l => ok(tag + ": limb " + l.getAttribute("data-part") + " thick and round", num(l, "stroke-width") >= 5 && l.getAttribute("stroke-linecap") === "round" && l.getAttribute("stroke") === "var(--text)"));
      if (hd) ok(tag + ": head uses var(--text)", hd.getAttribute("fill") === "var(--text)");
      f.querySelectorAll(".gm-band, .gm-loop").forEach(b => ok(tag + ": band is gold width 4", b.getAttribute("stroke") === "var(--gold)" && num(b, "stroke-width") === 4));
    });
    const P = w.gmPoses && w.gmPoses[id];
    ok(id + ": poses are joint angles, not points", !!P && ["start", "end"].every(k => ["torso", "head", "uA", "fA", "th", "sh"].every(a => typeof P[k][a] === "number") && !("knee" in P[k]) && !("hand" in P[k]) && !("elbow" in P[k])));
  });
  ok("one forward-kinematics function", typeof w.gmPoseJoints === "function");
  const J = (id, k) => { const f = frames(w, id)[k]; return { hip: pt(part(f, "torso"), 1), sho: pt(part(f, "torso"), 2), knee: pt(part(f, "thigh"), 2), ank: pt(part(f, "shin"), 2), hand: pt(part(f, "farm"), 2), elbow: pt(part(f, "farm"), 1), f }; };
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  // row
  ["start", "end"].forEach(k => { const j = J("row", k); ok("row " + k + ": seated, legs straight along the floor", Math.abs(j.hip[1] - j.ank[1]) <= 1 && Math.abs(j.knee[1] - j.hip[1]) <= 1 && j.ank[0] - j.hip[0] > 30 && j.hip[1] >= 84);
    const b = j.f.querySelector(".gm-band"); ok("row " + k + ": band feet to hands", !!b && dist(pt(b, 1), j.ank) < 1 && dist(pt(b, 2), j.hand) < 1); });
  { const s = J("row", "start"), e = J("row", "end"); ok("row end: hands at the waist", dist(e.hand, e.hip) <= 22 && dist(e.hand, e.hip) < dist(s.hand, s.hip)); }
  // squat
  { const s = J("squat", "start"), e = J("squat", "end");
    ok("squat start standing", Math.abs(s.sho[0] - s.hip[0]) < 2 && s.sho[1] < s.hip[1] - 25 && Math.abs(s.ank[0] - s.hip[0]) < 2);
    ok("squat end hips lowered >= 12", e.hip[1] - s.hip[1] >= 12, e.hip[1] - s.hip[1]);
    ok("squat end knees bent", Math.abs(e.knee[1] - e.hip[1]) < 10 && e.knee[0] - e.hip[0] > 10);
    [s, e].forEach((j, i) => { const l = j.f.querySelector(".gm-loop"); ok("squat " + i + ": gold loop just above the knee", !!l && len(l) <= 14 && dist([(num(l, "x1") + num(l, "x2")) / 2, (num(l, "y1") + num(l, "y2")) / 2], j.knee) <= 8); }); }
  // press
  { const s = J("press", "start"), e = J("press", "end");
    [s, e].forEach((j, i) => { const b = j.f.querySelector(".gm-band"), a = pt(b, 1);
      ok("press " + i + ": standing", Math.abs(j.sho[0] - j.hip[0]) < 2 && Math.abs(j.ank[0] - j.hip[0]) < 2 && j.sho[1] < j.hip[1] - 25);
      ok("press " + i + ": band from behind the back at chest height to the hands", a[0] < j.hip[0] - 15 && Math.abs(a[1] - j.sho[1]) <= 12 && dist(pt(b, 2), j.hand) < 1); });
    ok("press end: arms straight forward", Math.abs(e.hand[1] - e.sho[1]) <= 2 && e.hand[0] - e.sho[0] >= 26 && e.hand[0] - e.sho[0] > s.hand[0] - s.sho[0] + 10); }
  // pushup
  { const s = J("pushup", "start"), e = J("pushup", "end"), lineDev = j => { const dx = j.sho[0] - j.ank[0], dy = j.sho[1] - j.ank[1], n = Math.hypot(dx, dy); return Math.abs((j.hip[0] - j.ank[0]) * dy - (j.hip[1] - j.ank[1]) * dx) / n; };
    ok("pushup start: arms straight, hand under shoulder", Math.abs(s.hand[0] - s.sho[0]) < 2 && Math.abs(s.hand[1] - s.sho[1] - 27) < 2);
    ok("pushup end: chest near the floor", 91 - e.sho[1] <= 20 && 91 - e.sho[1] < 91 - s.sho[1] - 8, 91 - e.sho[1]);
    ok("pushup: body straight in both", lineDev(s) <= 2 && lineDev(e) <= 2, lineDev(s) + "/" + lineDev(e)); }
  // plank
  ["start", "end"].forEach(k => { const j = J("plank", k), dx = j.sho[0] - j.ank[0], dy = j.sho[1] - j.ank[1], n = Math.hypot(dx, dy);
    const dev = p => Math.abs((p[0] - j.ank[0]) * dy - (p[1] - j.ank[1]) * dx) / n;
    ok("plank " + k + ": shoulders, hips, ankles in one line", dev(j.hip) <= 4 && dev(j.sho) <= 4);
    ok("plank " + k + ": forearms on the floor", Math.abs(j.elbow[1] - j.hand[1]) <= 2 && 91 - j.hand[1] <= 5); });
  console.log("test140 exercise figures v2: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
