// Rebuilds the self-contained index.html after editing ops.js.
// Usage: node build.js
//
// Inlines ops.js between the marker's <script> and the Failsafe <script>, using plain
// string slicing (NOT String.replace with the ops as the replacement) — replacement
// strings interpret $-sequences ($&, $', $1, $$), and ops.js contains regex literals with
// `$`, which previously caused the ops block to be duplicated and leak as raw page text.
// This version is $-safe and self-heals a previously corrupted index.html.
const fs = require("fs");
const html = fs.readFileSync("index.html", "utf8");
const ops = fs.readFileSync("ops.js", "utf8");

const MARK = "<!-- ops.js INLINED below by build.js";
const OPEN = "<script>\n";
const FAILSAFE = "<script>\n/* Failsafe";

const markAt = html.indexOf(MARK);
if (markAt < 0) { console.error("Marker not found — aborting, nothing changed."); process.exit(1); }
const openAt = html.indexOf(OPEN, markAt);
if (openAt < 0) { console.error("Opening <script> after marker not found — aborting."); process.exit(1); }
// Use the LAST Failsafe block as the clean tail, so any prior duplication/corruption
// between the ops script and the final Failsafe is discarded.
const failsafeAt = html.lastIndexOf(FAILSAFE);
if (failsafeAt < 0 || failsafeAt < openAt) { console.error("Failsafe block not found — aborting."); process.exit(1); }

const before = html.slice(0, openAt + OPEN.length);   // …marker + "<script>\n"
const tail = html.slice(failsafeAt);                  // "<script>\n/* Failsafe … </script>" + rest
const out = before + ops + "\n</script>\n" + tail;

fs.writeFileSync("index.html", out);
console.log("index.html rebuilt with current ops.js (" + ops.length + " chars).");
