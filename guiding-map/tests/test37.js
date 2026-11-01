// v37: "Welcome back" — returning after days away is met with a warm hello (never a guilt-wall of missed
// days) and one zero-input tap onto today's three. Shown only from the 4th day away, once per day. Daily
// and brand-new users never see it. The greeting + n/3 ring (test26's contract) stays intact beneath it.
const fs = require("fs"), path = require("path"), { JSDOM } = require("jsdom");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) pass++; else { fail++; console.log("FAIL", m, d || ""); } };
const ymd = (dt) => dt.getFullYear() + "-" + ("0" + (dt.getMonth() + 1)).slice(-2) + "-" + ("0" + dt.getDate()).slice(-2);
function boot(seedLastOpen) {
  return new JSDOM(html, {
    runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; w.confirm = () => false; w.alert = () => {};
      if (seedLastOpen) { try { w.localStorage.setItem("gm_lastOpen", JSON.stringify(seedLastOpen)); } catch (e) {} }
    }
  });
}
setTimeout(() => {
  // 1) Returning after 12 days: the welcome-back hero appears, above the greeting.
  const d1 = boot(ymd(new Date(Date.now() - 12 * 864e5)));
  const w1 = d1.window, doc1 = w1.document;
  w1.curTab = "today"; w1.renderAll();
  const wb = doc1.querySelector("#sections .gm-wb");
  ok(!!wb, "a returning user sees a Welcome back hero");
  ok(wb && /Welcome back/i.test(wb.textContent) && /Good to see you again/.test(wb.textContent), "it greets warmly", wb && wb.textContent.slice(0, 80));
  ok(wb && /12 days/.test(wb.textContent), "it names how long they were away, without shaming", wb && wb.textContent.slice(0, 140));
  ok(wb && wb.querySelector(".gm-wb-cta"), "it offers one zero-input tap to pick up");
  const g1 = doc1.querySelector("#sections .gm-greet");
  ok(g1 && /\d\/3/.test(g1.textContent), "the greeting and n/3 ring (test26's contract) still render");
  ok(wb && g1 && (wb.compareDocumentPosition(g1) & w1.Node.DOCUMENT_POSITION_FOLLOWING) !== 0, "the hero sits above the greeting");
  w1.gmWelcomeHide();
  ok(!doc1.querySelector("#sections .gm-wb"), "dismissing removes it");
  w1.renderAll();
  ok(!doc1.querySelector("#sections .gm-wb"), "and it stays gone for the rest of the day");

  // 2) A daily user (opened yesterday) never sees it.
  const d2 = boot(ymd(new Date(Date.now() - 1 * 864e5)));
  d2.window.curTab = "today"; d2.window.renderAll();
  ok(!d2.window.document.querySelector("#sections .gm-wb"), "a daily user is not shown the hero");

  // 3) A brand-new user (no history) never sees it.
  const d3 = boot(null);
  d3.window.curTab = "today"; d3.window.renderAll();
  ok(!d3.window.document.querySelector("#sections .gm-wb"), "a first-time user is not shown the hero");

  console.log("test37 welcome back: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 800);
