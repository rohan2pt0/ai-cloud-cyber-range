// v14 render-correctness (user-perspective Kaizen): catch the class of bug that
// shipped the "● etc rather than colored icons" the user saw — a region of ops.js
// got DOUBLE-escaped (`\\u25cf`, `\\u20b9`), so every System-Health status dot and
// every ₹ money-unit label rendered as the LITERAL TEXT `●` / `₹` instead
// of ● / ₹. jsdom renders every tab; we assert no literal \uXXXX / \u{...} escape
// text, and no stray "\\u", leaks into what the user actually sees.
const fs = require('fs'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = [];
const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };

const dom = new JSDOM(fs.readFileSync('index.html', 'utf8'),
  { runScripts: "dangerously", pretendToBeVisual: true, url: "https://guiding-map.example.org/" });
const w = dom.window, d = w.document;
setTimeout(() => {
  const ids = w.TABS.map(t => t[0]);
  // A literal JS unicode escape that leaked into rendered text: \uXXXX or \u{...}.
  const LEAK = /\\u[0-9a-fA-F]{4}|\\u\{[0-9a-fA-F]+\}/;

  ids.forEach(t => {
    w.swT(ids.indexOf(t));
    const html = d.getElementById('sections').innerHTML;
    const text = d.getElementById('sections').textContent || "";
    const m = text.match(LEAK) || html.match(LEAK);
    ok("tab '" + t + "' has no literal \\uXXXX escape leaking to the user", !m, m && m[0]);
  });

  // System health specifically: the status dots must be real ● glyphs in a status
  // colour, and must NOT be the literal text that shipped before.
  w.swT(ids.indexOf('ops'));
  const ops = d.getElementById('sections').innerHTML;
  ok("System health renders real ● status dots (not literal \\u25cf)",
    ops.indexOf('\\u25cf') === -1 && ops.indexOf('●') > -1);
  ok("status dots carry a status colour (green/red/amber)",
    /var\(--green\)|var\(--red\)|var\(--amber\)/.test(ops));

  // Money-unit labels must render the ₹ GLYPH (U+20B9), not literal escape text.
  // NOTE: scan rendered #sections only — document.body.textContent also contains the
  // inlined <script> SOURCE (legit single-backslash ₹), which is not what the user sees.
  ok("₹ glyph renders in money context (System health shows real ₹)",
    (d.getElementById('sections').textContent || "").indexOf('₹') > -1 ||
    (function () { w.swT(ids.indexOf('book')); return (d.getElementById('sections').textContent || "").indexOf('₹') > -1; })());

  // Step markers are the new coloured ▸, not literal □ escape text.
  w.swT(ids.indexOf('book'));
  const book = d.getElementById('sections').innerHTML;
  ok("playbook step markers don't leak literal \\u25a1 escape text", book.indexOf('\\u25a1') === -1);

  // Frictionless launch: the Ask tab must surface a plain-language readiness status
  // so an early-opened page is never a silent dead end.
  w.swT(ids.indexOf('ask'));
  ok("Ask tab has a readiness status indicator", !!d.getElementById('askStatus'));
  ok("readiness pinger is defined", typeof w.gmAskPing === 'function');

  console.log("PASS " + P + "   FAIL " + F); e.forEach(x => console.log("  ✗ " + x));
  if (F > 0) process.exit(1);
}, 1500);
