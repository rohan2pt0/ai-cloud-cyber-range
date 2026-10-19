// Life OS habits from national strategies (docs 70-71): key results "from X to Y by a date", the 6-week drop / re-scope /
// recommit prompt, strengths first, and the "who touched my data" log.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/" });
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
setTimeout(() => {
  const w = d.window, S = w.S;
  // 1. A key result written as "from X to Y by a date" tracks the number.
  const kr = w.parseKR("Emergency fund from 2 to 4 months by 31 Mar");
  ok(kr && kr.b === 2 && kr.g === 4 && kr.c === 2 && kr.dueMs > Date.now() - 864e5 * 31, "from/to/by parsed, date in the future");
  ok(w.parseKR("Savings rate 12 -> 18% by 30 Jun").g === 18, "arrow form parsed");
  ok(w.parseKR("Read more books") === null, "free text stays a slider");
  ok(w.krFrac({ b: 2, g: 4, c: 3 }) === 0.5 && w.krFrac({ b: 2, g: 4, c: 9 }) === 1 && w.krFrac({ b: 10, g: 5, c: 7.5 }) === 0.5, "score from the number, clamped, works downwards too");
  // 2. Strengths first, and each objective names one.
  S.strengths = ["calm in a crisis", "steady saver"];
  S.okrs = [{ o: "Money unshakeable", s: "steady saver", at: Date.now(), krs: [Object.assign({ t: "fund from 2 to 4 by 31 Mar", v: 0, at: Date.now() }, kr)] }];
  let out = w.renderOKR();
  ok(out.indexOf("calm in a crisis") >= 0 && out.indexOf("Builds on") >= 0, "strengths shown, objective picks one");
  ok(out.indexOf("days left") >= 0 && out.indexOf("No movement") < 0, "fresh goal: countdown, no stale prompt");
  w.setKRNow(0, 0, 3);
  ok(S.okrs[0].krs[0].c === 3 && w.okrGrade(0) === 0.5, "typing today's number moves the grade");
  // 3. Six idle weeks: an explicit decision.
  S.okrs[0].at = Date.now() - 864e5 * 50; S.okrs[0].krs[0].at = Date.now() - 864e5 * 50;
  out = w.renderOKR();
  ok(out.indexOf("No movement for 7 weeks") >= 0 && out.indexOf("Recommit") >= 0 && out.indexOf("Re-scope") >= 0 && out.indexOf("Drop, keep the lesson") >= 0, "stale prompt offers all three");
  w.okrRecommit(0);
  ok(w.okrIdle(S.okrs[0]) === 0 && S.okrs[0].recommits === 1, "recommit resets the clock and is counted");
  w.okrDrop(0);
  d.window.document.getElementById("gmPin").value = "timing was wrong";
  d.window.document.getElementById("gmOk").click();
  ok(S.okrs.length === 0 && S.okrDropped.length === 1 && S.okrDropped[0].lesson === "timing was wrong", "drop keeps the lesson on record");
  ok(w.renderOKR().indexOf("Dropped on purpose") >= 0, "dropped goals stay visible");
  S.okrs = [{ o: "From an older version", krs: [{ t: "no timestamps", v: 0.3 }] }];
  ok(w.renderOKR().indexOf("No movement") < 0 && w.okrIdle(S.okrs[0]) === 0, "a goal with no timestamps starts its clock now, not in 1970");
  // 4. Who touched my data: logged, de-duplicated within the hour, merged across devices.
  w.gmTouch("Synced, encrypted", "your OneDrive");
  w.gmTouch("Synced, encrypted", "your OneDrive");
  w.localStorage.setItem("gm_access_otherdev", JSON.stringify([{ t: Date.now() - 1000, w: "A question went to AI", p: "your estate AI gateway", d: "Android phone" }]));
  const rows = w.gmTouchRows();
  ok(rows.filter((r) => r.w === "Synced, encrypted").length === 1, "a repeat within the hour is not logged again");
  ok(rows.some((r) => r.d === "Android phone"), "other devices' logs are shown too");
  w.document.body.insertAdjacentHTML("beforeend", "<div id=x></div>");
  w.URL.createObjectURL = () => "blob:x";
  w.HTMLAnchorElement.prototype.click = function () {};
  w.gmExportNow();
  ok(w.gmTouchRows().some((r) => /Exported/.test(r.w)), "an export is logged");
  console.log("test23 strategy habits: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 800);
