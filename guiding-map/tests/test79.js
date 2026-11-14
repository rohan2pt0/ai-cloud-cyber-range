// test79: every property number carries a verdict (owner, 2026-11-12), and gold is metallic.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_intro_seen", "true");
    w.localStorage.setItem("gm_props", JSON.stringify([{ n: "Flat", use: "letout", val: "100", rent: "24000", loan: "43", rate: "8.5", emi: "38000", out: "30000", vac: "1" }])); } }).window;
setTimeout(() => {
  try {
    w.goTab("prop");
    const d = w.document;
    d.querySelectorAll("#sections details").forEach((x) => (x.open = true));
    const nums = Array.from(d.querySelectorAll(".gm-metric .gm-num"));
    ok(nums.length >= 10, "the property numbers render");
    const judged = nums.filter((n) => /gm-v-[gar]/.test(n.className));
    ok(judged.length >= 7, "the decision numbers each carry a verdict colour (" + judged.length + ")");
    ok(Array.from(d.querySelectorAll(".gm-metric .gm-vw")).every((x) => /^(Strong|Watch|Weak)$/.test(x.textContent)), "each verdict also has a word, never colour alone");
    ok(!/₹-/.test(d.getElementById("sections").textContent), "losses read with a real minus sign, not '₹-'");
    const css = Array.from(d.querySelectorAll("style")).map((s) => s.textContent).join("\n");
    var gm = (css.match(/--gold-metal:var\(--sx-gold-edge,(linear-gradient\(135deg,[^)]*\))\)/) || [])[1] || "";
    // Shared real gold (lux.css --sx-gold-edge), with a metallic fallback: many stops, deep shadows as well as highlights.
    ok(gm && gm.split("%").length > 7 && /#6b4a12|#8f6619/.test(gm) && /#fff6dc/.test(gm), "gold is a metallic gradient, not a flat yellow");
    ok(/\.gm-hero \.gm-hero-n\{background:var\(--gold-metal\)/.test(css), "hero numbers are set in metallic gold");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test79 verdicts and metallic gold: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
