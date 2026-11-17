// v125: a step that asks you to write names or note something gets its own place to do it, right under the step
// (queue step-doers, slice 1). Deep Friendships: 5 name inputs tick the step when full; the after-call step keeps
// dated notes and lists the last 3; a step with neither pattern gets no name or note inputs (a recurring one may still
// add its calendar, slice 3).
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const saved = () => { try { return JSON.parse(w.localStorage.getItem("gm_stepdo") || "{}") || {}; } catch (x) { return {}; } };
  const stepBy = (re) => Array.prototype.slice.call(d.querySelectorAll("#m_sys .step")).filter((s) => re.test(s.textContent))[0];
  const doerOf = (step) => (step && step.nextElementSibling && /(^|\s)step-do(\s|$)/.test(step.nextElementSibling.className)) ? step.nextElementSibling : null;
  const inputsOf = (step) => { const b = doerOf(step); return b ? Array.prototype.slice.call(b.querySelectorAll('input:not([type="checkbox"])')) : []; };
  const type = (inp, v) => { inp.value = v; inp.dispatchEvent(new w.Event("input", { bubbles: true })); };

  const fi = w.KPIs.findIndex((k) => k.id === "friends");
  ok("the Deep Friendships system exists", fi >= 0, "index " + fi);
  if (fi >= 0) w.openK(fi);

  const names = stepBy(/Write the 5 names/);
  ok("opening it shows the names step", !!names, "no step");
  const ni = inputsOf(names);
  ok("the write-the-5-names step shows 5 inputs under it", ni.length === 5, ni.length + " inputs");
  ni.forEach((inp, ix) => type(inp, "Friend " + (ix + 1)));
  const n0 = saved()["friends:0"];
  ok("the 5 names are saved under friends:0", Array.isArray(n0) && n0.length === 5 && n0[0] === "Friend 1" && n0[4] === "Friend 5", JSON.stringify(n0));
  const names2 = stepBy(/Write the 5 names/), cb = names2 && names2.querySelector('input[type="checkbox"]');
  ok("filling all 5 ticks the step", !!(cb && cb.checked), cb ? "still unchecked" : "no checkbox");

  const call = stepBy(/After each call/);
  const one = inputsOf(call);
  ok("the after-call step shows one note input", one.length === 1, one.length + " inputs");
  const addOf = (s) => { const b = doerOf(s); return b && b.querySelector('[data-stepdo-add]'); };
  ok("the note input has an add control", !!addOf(call), "no add control");
  ["Talked about his new job", "His mother is unwell", "Ran a half marathon", "Asked about the move"].forEach((txt) => {
    const s = stepBy(/After each call/), inp = inputsOf(s)[0], add = addOf(s);
    if (inp && add) { type(inp, txt); add.click(); }
  });
  const n2 = saved()["friends:2"];
  ok("the notes are saved with a date", Array.isArray(n2) && n2.length === 4
    && n2.every((n) => n && /^\d{4}-\d{2}-\d{2}$/.test(n.d) && n.t), JSON.stringify(n2));
  const call2 = stepBy(/After each call/), box = doerOf(call2);
  ok("only the last 3 notes are listed", !!box && /Asked about the move/.test(box.textContent)
    && /Ran a half marathon/.test(box.textContent) && /His mother is unwell/.test(box.textContent)
    && !/Talked about his new job/.test(box.textContent), box ? box.textContent.slice(0, 220) : "no doer");

  const wed = stepBy(/Every Wednesday/);
  ok("a step with neither pattern shows no name or note inputs", !!wed && inputsOf(wed).length === 0 && !addOf(wed),
    wed ? (inputsOf(wed).length + " inputs") : "no step");

  // A noun is not an instruction: "a 1-line personal note" in a LinkedIn step gets no note line.
  const li = w.KPIs.findIndex((k) => k.id === "network");
  if (li >= 0) { w.openK(li); const lstep = stepBy(/LinkedIn requests/);
    ok("a step that only mentions a note as a noun gets no note line", !!lstep && inputsOf(lstep).length === 0 && !addOf(lstep), lstep ? "has note inputs" : "step not found"); }
  console.log("test125 step doers: " + P + " passed, " + F + " failed");
  if (F) { e.forEach((x) => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
