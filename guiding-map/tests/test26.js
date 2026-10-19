// Design v2 and "Report a problem": one quiet header with a menu, a greeting that says what today needs, the daily three as
// big tiles, and a two-tap bug report whose details hold nothing personal and whose link comes only from the build file.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
const tick = () => new Promise((r) => setTimeout(r, 30));
setTimeout(async () => {
  const w = d.window, doc = w.document;
  w.curTab = "today"; w.renderAll();
  const hdr = doc.querySelector("#dash header");
  ok(hdr && hdr.querySelector(".gm-menu-btn"), "the header has one menu button");
  ok([...hdr.querySelectorAll(".hdr-btn")].filter((b) => !b.classList.contains("gm-hide-hdr")).length === 2, "only All Apps and the menu stay in the header");
  const g = doc.querySelector("#sections .gm-greet");
  ok(g && /Good (morning|afternoon|evening)|Still up/.test(g.textContent) && /\d\/3/.test(g.textContent), "Today opens with a greeting and the n/3 ring");
  const tiles = doc.querySelectorAll("#sections .gm-d3 .tile");
  ok(tiles.length === 3 && [...tiles].every((t) => t.getAttribute("role") === "button" && t.getAttribute("tabindex") === "0"), "the daily three are three keyboard-reachable tiles");
  const before = doc.querySelectorAll("#sections .gm-d3 .tile.on").length;
  tiles[0].dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  ok(doc.querySelectorAll("#sections .gm-d3 .tile.on").length === before + 1, "Enter on a tile ticks it");
  w.gmMenu();
  ok(/Report a problem/.test(doc.getElementById("gmOverlay").textContent), "the menu offers Report a problem");
  w.gmClose();
  // The report: no personal data, a link only when the build names the repo.
  w.P.name = "Example Person"; w.dispatchEvent(new w.ErrorEvent("error", { message: "boom in a test", lineno: 7 }));
  const diag = w.gmDiag({ label: "v9.9.9 · abc1234" });
  ok(/v9\.9\.9/.test(diag) && /boom in a test @7/.test(diag) && /\d+x\d+/.test(diag), "the details name the build, the screen and the last error");
  ok(!/Example Person/.test(diag), "the details hold no name");
  w.gmReport(null); await tick();
  ok(doc.getElementById("gmDiag") && !doc.querySelector("#gmOverlay a[href*='issues/new']"), "without a build file there is no guessed link");
  w.gmClose();
  w.gmReport({ label: "v9.9.9 · abc1234", repo: "example-owner/example-repo" }); await tick();
  const a = doc.querySelector("#gmOverlay a[href*='issues/new']");
  ok(a && /github\.com\/example-owner\/example-repo\/issues\/new\?template=bug_report\.yml/.test(a.href) && /version=v9\.9\.9/.test(a.href), "with one, the link opens the prefilled bug form");
  ok(a && !/Example/.test(decodeURIComponent(a.href)), "the link carries no name either");
  console.log("test26 design and report: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 800);
