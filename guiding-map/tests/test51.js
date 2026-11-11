// v51: explain every short code (human-first, plain words). The Optionality tags say "Now", "1-2 years",
// "3-5 years" instead of H1/H2/H3, and the GLOSSARY carries a plain entry for every code a person meets.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, parents: false, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("stack");
  const text = sec().textContent;
  ok("the Stack tab has no standalone H1, H2 or H3 tag", !/\bH[123]\b/.test(text), text.slice(0, 300));
  ok("the Optionality tags say 1-2 years in plain words", text.includes("1-2 years"), text.slice(-300));
  // every short code a person sees has a plain entry (the k match words are one per term)
  const src = fs.readFileSync(path.join(__dirname, '..', 'ops.js'), 'utf8');
  const block = (/var GLOSSARY = \[([\s\S]*?)\n  \];/.exec(src) || [])[1] || "";
  const kwords = new Set();
  for (const m of block.matchAll(/k:\s*\[([^\]]*)\]/g)) for (const q of m[1].matchAll(/"([^"]+)"/g)) kwords.add(q[1].toLowerCase());
  ["nps", "ppf", "epf", "emi", "ctc", "pan", "cas", "cdsl", "nsdl", "psu", "ciso", "bfsi", "opsec", "q1", "l0", "s1", "json", "url"]
    .forEach(word => ok("the GLOSSARY explains " + word.toUpperCase(), kwords.has(word), [...kwords].filter(x => x.includes(word)).join(",")));
  console.log("test51 explain the codes: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
