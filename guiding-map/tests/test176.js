// test176: the jargon ratchet (principle plain-first, owner 2026-11-25). What a person sees by default is everyday language:
// ratios, formulas and theory sit one tap away, under "How we worked this out" or in the glossary. This test renders every
// top-level tab with a fake profile, collects the text that is visible by default (not inside a closed <details>, not in
// "How we worked this out", not in the glossary) and counts jargon terms. The count per tab may only go down:
// tests/jargon-baseline.json holds each tab's ceiling, and the Property tab's is 0. UPDATE_BASELINE=1 lowers a ceiling
// after a tab has been made plain (it never raises one). Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(process.env.INDEX_HTML || path.join(__dirname, '..', 'index.html'), 'utf8');   // INDEX_HTML: measure another build (for a before count)
const BASE = path.join(__dirname, 'jargon-baseline.json');
const t = new Date(); const iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: "1988-03-10", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 200000,
  pname: "Fake Partner", kids: [{ name: "Kid A", dob: "2018-01-01" }], ret: 60, tsav: 20, example: false, earners: 1, loans: [] };
const flat = { n: "Test flat A", use: "letout", val: "90", rent: "26000", loan: "55.82", rate: "7.75", emi: "50000", out: "0", vac: "0",
  owner: "me", start: iso(-200), months: "11" };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_props", JSON.stringify([flat])); w.localStorage.setItem("gm_facts", JSON.stringify({ state: "MH" }));
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
    w.fetch = () => Promise.reject(new Error("offline")); } });
// the jargon: a word a common person does not use. Matched as whole words, any case; "×" is the multiplication sign of a bare ratio.
const TERMS = [["DSCR", /\bDSCR\b/gi], ["KPI", /\bKPIs?\b/gi], ["KRI", /\bKRIs?\b/gi], ["IRR", /\bX?IRR\b/gi], ["CAGR", /\bCAGR\b/gi],
  ["amortisation", /\bamorti[sz]ation\b/gi], ["occupancy", /\boccupancy\b/gi], ["LTV", /\bLTV\b/gi], ["debt-to", /\bdebt-to\b/gi], ["ratio", /\bratios?\b/gi],
  ["×", /×/g], ["basis points", /\bbasis points?\b/gi], ["bps", /\bbps\b/gi], ["alpha", /\balpha\b/gi], ["beta", /\bbeta\b/gi],
  ["Sharpe", /\bSharpe\b/gi], ["drawdown", /\bdrawdowns?\b/gi], ["corpus", /\bcorpus\b/gi]];
// text visible by default: skip a closed <details> (keep its summary), a "How we worked this out" block, the glossary, scripts and styles
function visible(root) {
  const out = [];
  (function walk(n) {
    if (n.nodeType === 3) { out.push(n.textContent); return; }
    if (n.nodeType !== 1) return;
    const tag = n.tagName;
    if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT" || n.hidden || /display:\s*none/.test(n.getAttribute("style") || "")) return;
    if (/\bgm-gloss\b|\bgm-pf-how\b|\bgm-fix-how\b/.test(n.className || "") || n.getAttribute("data-glossary") !== null) return;
    if (tag === "DETAILS") {
      const s = n.querySelector(":scope > summary"); if (s && /How we worked this out/i.test(s.textContent)) return;
      if (!n.open) { if (s) out.push(s.textContent); return; }
    }
    if (tag === "INPUT" || tag === "TEXTAREA") { out.push(" " + (n.getAttribute("placeholder") || "") + " "); return; }
    n.childNodes.forEach(walk); out.push(" ");
  })(root);
  return out.join("");
}
const count = (txt) => { const by = {}; let n = 0; TERMS.forEach(([k, re]) => { const m = txt.match(re); if (m) { by[k] = m.length; n += m.length; } }); return { n, by }; };
setTimeout(() => {
  const w = dom.window, d = w.document;
  const tabs = w.eval("TABS.map(function (x) { return x[0]; })");
  const base = fs.existsSync(BASE) ? JSON.parse(fs.readFileSync(BASE, "utf8")) : { tabs: {} };
  const now = {}, raw = {}, rows = [];
  tabs.forEach((id) => {
    try { w.goTab(id); w.renderAll(); } catch (er) { ok("tab " + id + " renders", false, er.message); return; }
    const box = d.getElementById("sections") || d.body, c = count(visible(box));
    now[id] = c.n; raw[id] = count(box.textContent).n; rows.push(id.padEnd(10) + String(c.n).padStart(4) + " of " + String(raw[id]).padStart(3) + " total, " + String(box.textContent.length).padStart(6) + " chars  " + JSON.stringify(c.by));
  });
  console.log("jargon terms visible by default, per tab (baseline in brackets):\n" + tabs.map((id, i) => "  " + rows[i] + "  [" + (base.tabs[id] === undefined ? "-" : base.tabs[id]) + "]").join("\n"));
  if (process.env.UPDATE_BASELINE) {   // lowers a ceiling, never raises one; a new tab starts at its own count
    const next = { about: "Jargon terms visible by default on each tab (tests/test176.js). A ceiling: it may only go down. Plain-first, owner 2026-11-25.", tabs: {} };
    tabs.forEach((id) => { next.tabs[id] = base.tabs[id] === undefined ? now[id] : Math.min(base.tabs[id], now[id]); });
    fs.writeFileSync(BASE, JSON.stringify(next, null, 1) + "\n");
  }
  const cur = fs.existsSync(BASE) ? JSON.parse(fs.readFileSync(BASE, "utf8")) : { tabs: {} };
  ok("the baseline lists every top-level tab", tabs.every((id) => cur.tabs[id] !== undefined), tabs.filter((id) => cur.tabs[id] === undefined).join());
  ok("the Property tab has no jargon by default (its ceiling is 0)", cur.tabs.prop === 0 && now.prop === 0, now.prop + " vs " + cur.tabs.prop);
  tabs.forEach((id) => { if (now[id] !== undefined && cur.tabs[id] !== undefined) ok("tab " + id + " keeps within its jargon ceiling", now[id] <= cur.tabs[id], now[id] + " > " + cur.tabs[id]); });
  const lower = tabs.filter((id) => now[id] < cur.tabs[id]);
  if (lower.length) console.log("  note: " + lower.join(", ") + " now sit under their ceiling: run UPDATE_BASELINE=1 node tests/test176.js to lock the gain in");
  console.log("test176 jargon ratchet: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 500);
