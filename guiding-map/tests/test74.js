// test74: tick a shared fact once and see it in the Stack, the Shield and the CSF.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = () => ({ matches: true, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }); w.scrollTo = () => {}; } });
const w = dom.window, doc = w.document;
function csfRow(code) {
  const heads = Array.from(doc.querySelectorAll("#sections .road-h"));
  const h = heads.find((el) => new RegExp("^\\s*" + code + "\\s*\u00b7").test(el.textContent));
  return h ? h.parentElement.textContent : "";
}
setTimeout(() => {
  try {
    w.gmNavGo("stack");
    const stackTexts = Array.from(doc.querySelectorAll("#sections .road-i")).map((el) => el.textContent);
    (w.GM_LINKS || []).forEach((f) => {
      const risk = f.shield ? w.RISKS.filter((r) => r.id === f.shield.risk)[0] : null;
      const shieldOK = !!(risk && risk.steps && risk.steps.some((s) => f.shield.rx.test(s)));
      const stackOK = f.stack ? stackTexts.some((t) => f.stack.test(t)) : false;
      ok(stackOK || shieldOK || !!f.csf, f.id + " has a linked place");
    });

    w.gmNavGo("ops");
    let pr = csfRow("PR");
    ok(/0\/5/.test(pr) && /Auto/.test(pr), "CSF Protect starts at Not yet, with Auto: " + pr.slice(0, 90));

    w.gmStackTg("L0", 4);
    let link = JSON.parse(w.localStorage.getItem("gm_links") || "{}");
    ok(link["password-manager"] && link["password-manager"].done === true && link["password-manager"].src === "Stack", "the Stack tick writes the shared fact, source Stack");
    ok(w.checkedArr("r", "r_cyber").indexOf(0) >= 0, "the linked Shield step reads ticked");
    w.gmNavGo("ops");
    pr = csfRow("PR");
    ok(/4\/5/.test(pr) && /Auto/.test(pr), "CSF Protect rises and still says Auto: " + pr.slice(0, 90));

    w.gmCsfSet("PR", "1");
    w.gmNavGo("ops");
    pr = csfRow("PR");
    ok(/1\/5/.test(pr), "a manual CSF choice wins over Auto: " + pr.slice(0, 90));
    const chip = Array.from(doc.querySelectorAll("#sections [role='button']")).filter((el) => /^Auto$/.test(el.textContent.trim()) && /gmCsfAuto/.test(el.getAttribute("onclick") || ""))[0];
    ok(!!chip, "the Auto chip is there to clear the manual choice");
    w.gmCsfAuto("PR");
    w.gmNavGo("ops");
    pr = csfRow("PR");
    ok(/4\/5/.test(pr) && /Auto/.test(pr), "the Auto chip restores the derived value: " + pr.slice(0, 90));

    const cy = w.RISKS.findIndex((r) => r.id === "r_cyber");
    w.tg("r", cy, 0);
    link = JSON.parse(w.localStorage.getItem("gm_links") || "{}");
    ok(link["password-manager"] && link["password-manager"].done === false, "unticking the Shield step unticks the fact");
    ok(w.checkedArr("r", "r_cyber").indexOf(0) < 0, "the Shield step reads unticked");
    const st = JSON.parse(w.localStorage.getItem("gm_stack") || "{}");
    ok(!(st["L0"] && st["L0"][4]), "the Stack item is unticked");
    w.gmNavGo("ops");
    pr = csfRow("PR");
    ok(/0\/5/.test(pr) && /Auto/.test(pr), "CSF Protect follows back down: " + pr.slice(0, 90));

    const beforeLinks = w.localStorage.getItem("gm_links");
    w.tg("r", cy, 2);
    ok(w.checkedArr("r", "r_cyber").indexOf(2) >= 0, "an unlinked Shield step still ticks itself");
    ok(w.localStorage.getItem("gm_links") === beforeLinks, "an unlinked Shield step writes no shared fact");
    ok(!w.checkedArr("r", "r_cyber").includes(0), "an unlinked step does not touch a linked step");
    w.gmStackTg("L0", 0);
    const st2 = JSON.parse(w.localStorage.getItem("gm_stack") || "{}");
    ok(!!(st2["L0"] && st2["L0"][0]), "an unlinked Stack item still ticks itself");
    ok(w.localStorage.getItem("gm_links") === beforeLinks, "an unlinked Stack item writes no shared fact");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test74 shared facts: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
