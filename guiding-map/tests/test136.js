// v136: deciding the community-proven way starts from one question (queue owner-frictions-goals-ask, slice 3 of 3;
// friction ask-intel-paste). One box asks what to decide; with the estate AI off the question waits in the Inbox.
// The paste fields fold under "I have my own list" and still give the consensus.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const inbox = () => { try { return JSON.parse(w.localStorage.getItem("gm_inbox") || "[]") || []; } catch (x) { return []; } };
  w.goTab("ask");
  const card = d.getElementById("askIntelCard");
  ok("the Ask tab shows the Decide the community-proven way card", !!card, "no card");
  if (card) card.open = true;

  const q = d.getElementById("intelQuestion");
  const ask = card && card.querySelector('[data-intel-ask]');
  const own = card && card.querySelector('details.gm-intel-own');
  const beforeFold = card ? Array.from(card.querySelectorAll('button')).filter(function (b) { return !own || !own.contains(b); }) : [];

  ok("the card opens with one question box: What do you want to decide?", !!q && /What do you want to decide\?/i.test(q.getAttribute("placeholder") || ""),
    q ? q.getAttribute("placeholder") : "no question box");
  ok("with one action before the fold", !!ask && beforeFold.length === 1, beforeFold.length + " buttons");
  ok("the paste area and names field are folded under I have my own list",
    !!own && !own.open && /I have my own list/i.test(own.querySelector("summary").textContent),
    own ? (own.open ? "open" : own.querySelector("summary").textContent) : "no fold");
  ok("the paste area and names field still live in that fold", !!own && !!own.querySelector("#intelItems") && !!own.querySelector("#intelVocab"));

  if (q && ask) {
    q.value = "Which cloud certification should I do next?";
    ask.click();
  }
  const it = inbox()[0] || {};
  ok("with the estate AI off, the question waits in the Inbox as an action",
    it.t === "Which cloud certification should I do next?" && it.kind === "action", JSON.stringify(inbox()));
  const said = d.getElementById("intelAskOut");
  ok("and the card says where the question waits", !!said && /Saved in your Inbox/i.test(said.textContent),
    said ? said.textContent : "nothing said");

  if (own) {
    own.open = true;
    const items = d.getElementById("intelItems"), vocab = d.getElementById("intelVocab");
    if (items && vocab) {
      items.value = "Passed CCSP! Pete Zerger videos\nCCSP: Pete Zerger + Sybex";
      vocab.value = "Pete Zerger";
      const go = own.querySelector('[onclick="gmIntelGo()"]');
      if (go) go.click();
    }
    const out = d.getElementById("intelOut");
    ok("I have my own list still finds the consensus", !!out && /Pete Zerger/.test(out.textContent),
      out ? out.textContent.slice(0, 160) : "no output");
  }

  console.log("test136 Ask one question: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
