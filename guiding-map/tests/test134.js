// v134: adding a key result is one tap on a suggestion, not typing "from X to Y by a date" (queue owner-frictions-goals-ask,
// friction okr-kr-typing). Tapping + Key result on an objective shows three chips from the quarterly suggestions that match
// its words; one tap adds the result with the quarter-end date. Write my own still opens the old prompt, and 4 stays the max.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const seed = { okrs: [{ o: "Make my money unshakeable", krs: [], at: Date.now() }], strengths: ["steady saver"] };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("sovS", JSON.stringify(seed));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const overlay = () => d.getElementById("gmOverlay");
  const chips = () => overlay() ? Array.from(overlay().querySelectorAll("button[data-kr]")) : [];
  const addBtn = () => d.querySelector('button[onclick="addKR(0)"]');
  const now = new Date();
  const qEnd = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3 + 3, 0);

  const sug = typeof w.gmKRSuggest === "function" ? w.gmKRSuggest("Make my money unshakeable") : [];
  ok("gmKRSuggest returns three suggestions", Array.isArray(sug) && sug.length === 3, JSON.stringify(sug));
  ok("the suggestions match the objective's words", sug.indexOf("Emergency fund up by one month of expenses") >= 0, JSON.stringify(sug));
  const gen = typeof w.gmKRSuggest === "function" ? w.gmKRSuggest("Underwater basket weaving zzz") : [];
  ok("an objective with no match gets a generic set of three", gen.length === 3 && gen.indexOf("Emergency fund up by one month of expenses") < 0, JSON.stringify(gen));

  w.goTab("okr");
  ok("the objective shows a + Key result button", !!addBtn(), "no addKR(0) button");
  if (addBtn()) addBtn().click();
  const c1 = chips();
  ok("tapping + Key result shows three suggestion chips", c1.length === 3, c1.length + " chips");
  ok("the chips are suggestions, not a typing prompt", c1.some(x => /Emergency fund up by one month/.test(x.textContent)) && !d.getElementById("gmPin"),
    c1.map(x => x.textContent).join(" | "));

  const pick = c1.filter(x => /Emergency fund up by one month/.test(x.textContent))[0];
  if (pick) pick.click();
  ok("the dialog closes after the tap", !overlay(), "dialog still open");
  const krs = w.S.okrs[0].krs;
  ok("one tap adds the key result with its text", krs.length === 1 && krs[0].t === "Emergency fund up by one month of expenses", JSON.stringify(krs));
  ok("and it carries the quarter-end date", !!krs[0].dueMs && new Date(krs[0].dueMs).toDateString() === qEnd.toDateString(),
    (krs[0] && (krs[0].due + " / " + krs[0].dueMs)) || "none");

  if (addBtn()) addBtn().click();
  const own = overlay() ? Array.from(overlay().querySelectorAll("a")).filter(a => /Write my own/i.test(a.textContent))[0] : null;
  ok("a Write my own link remains", !!own, overlay() ? overlay().textContent.slice(0, 120) : "no dialog");
  if (own) own.click();
  const inp = d.getElementById("gmPin");
  ok("Write my own opens the old prompt", !!inp && /New Key Result/.test(overlay() ? overlay().textContent : ""), inp ? "has input" : "no input");
  if (inp) { inp.value = "Emergency fund from 2 to 4 months by 31 Mar"; d.getElementById("gmOk").click(); }
  const krs2 = w.S.okrs[0].krs;
  ok("a typed key result is still parsed", krs2.length === 2 && krs2[1].b === 2 && krs2[1].g === 4, JSON.stringify(krs2));

  for (let i = 0; i < 2; i++) { if (addBtn()) addBtn().click(); const cs = chips(); if (cs.length) cs[0].click(); }
  ok("four key results can be added", w.S.okrs[0].krs.length === 4, w.S.okrs[0].krs.length + " results");
  if (addBtn()) addBtn().click();
  ok("a fifth is refused", w.S.okrs[0].krs.length === 4 && chips().length === 0, w.S.okrs[0].krs.length + " results");

  console.log("test134 okr one-tap key results: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
