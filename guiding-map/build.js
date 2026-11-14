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
// Life OS languages: every guiding-map/i18n/lifeos.<lang>.json is inlined as window.GM_I18N, so they work offline and from file://.
const I18N_DIR = require("path").join(__dirname, "i18n"), CATS = {};
if (fs.existsSync(I18N_DIR)) fs.readdirSync(I18N_DIR).filter(f => /^lifeos\.[a-z]{2}\.json$/.test(f)).sort().forEach(f => { CATS[f.split(".")[1]] = JSON.parse(fs.readFileSync(require("path").join(I18N_DIR, f), "utf8")); });
const I18N_JS = "window.GM_I18N = " + JSON.stringify(CATS).replace(/<\/(script)/gi, "<\\/$1") + ";\n";
// Life systems: the recipes (facts, systems, projects, sources) travel with the app as window.GM_SYSTEMS, so they work offline.
const SYS_FILE = require("path").join(__dirname, "systems", "systems.json");
const SYSTEMS = fs.existsSync(SYS_FILE) ? JSON.parse(fs.readFileSync(SYS_FILE, "utf8")) : { systems: [], events: [], facts: [], sources: {} };
const SYS_JS = "window.GM_SYSTEMS = " + JSON.stringify(SYSTEMS).replace(/<\/(script)/gi, "<\\/$1") + ";\n";
// Threats in the news: the curated drills travel with the app (offline); the hosted intel.json adds live headlines and ranking.
const INTEL_FILE = require("path").join(__dirname, "..", "intel", "threat-patterns.json");
const INTEL_LIB = fs.existsSync(INTEL_FILE) ? JSON.parse(fs.readFileSync(INTEL_FILE, "utf8")) : { patterns: [] };
const INTEL = { version: INTEL_LIB.version || 1, generated: "", heat_days: 30, patterns: INTEL_LIB.patterns.map(p => ({ id: p.id, name: p.name, where: p.where, severity: p.severity, story: p.story, signs: p.signs, drills: p.drills, heat: 0, news: [] })) };
const INTEL_JS = "window.GM_INTEL = " + JSON.stringify(INTEL).replace(/<\/(script)/gi, "<\\/$1") + ";\n";
// The SecuRAX shared look (guiding-map/shared/lux.css): ONE source every app builds in (reuse-first). It loads before the
// app's own styles, so an app adds context on top and never keeps a private copy of a shared primitive.
const SX_FILE = require("path").join(__dirname, "shared", "lux.css");
// The shared sans (Jost, SIL OFL, guiding-map/fonts) rides with the shared look as a data URI, so it works offline.
const SX_FONT = "/* Jost, SIL Open Font License 1.1: guiding-map/fonts/Jost-OFL.txt */@font-face{font-family:'Jost';font-style:normal;font-weight:100 900;font-display:swap;src:url(data:font/woff2;base64," + fs.readFileSync(require("path").join(__dirname, "fonts", "Jost-Variable.woff2")).toString("base64") + ") format('woff2')}\n";
const SX_JS = fs.existsSync(SX_FILE) ? "(function(){try{var s=document.createElement('style');s.id='sxLux';s.textContent=" + JSON.stringify(SX_FONT + fs.readFileSync(SX_FILE, "utf8")).replace(/<\/(style|script)/gi, "<\\/$1") + ";document.head.appendChild(s);}catch(e){}})();\n" : "";
// The SecuRAX shared scripts (shared/*.js: the night sky, touch and light): the same engines every app builds in (reuse-first).
const SHARED_DIR = require("path").join(__dirname, "shared");
const SKY_JS = fs.readdirSync(SHARED_DIR).filter(f => f.endsWith(".js")).sort()
  .map(f => fs.readFileSync(require("path").join(SHARED_DIR, f), "utf8").replace(/<\/(script)/gi, "<\\/$1")).join("\n") + "\n";
const built = before + SX_JS + SKY_JS + I18N_JS + SYS_JS + INTEL_JS + ops + "\n</script>\n" + tail;

// Stamp the visible version badge from the repo's single source of truth (../VERSION) so the app can
// never show a version the product doesn't have. (It once said "v13.0.2" — a hardcoded legacy string.)
const VERSION_FILE = require("path").join(__dirname, "..", "VERSION");
if (!fs.existsSync(VERSION_FILE)) { console.error("VERSION file not found at " + VERSION_FILE + " — aborting."); process.exit(1); }
const VERSION = fs.readFileSync(VERSION_FILE, "utf8").trim();
const BADGE = /(id="app_ver"[^>]*>)v[^<]*(<\/span>)/;
if (!BADGE.test(built)) { console.error('Version badge (id="app_ver") not found in index.html — aborting.'); process.exit(1); }
const out = built.replace(BADGE, (_m, open, close) => open + "v" + VERSION + close);   // fn replacer: $-safe

fs.writeFileSync("index.html", out);
console.log("index.html rebuilt with current ops.js (" + ops.length + " chars).");
