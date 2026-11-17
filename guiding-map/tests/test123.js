// v123: a mission line above the quarter's objectives (queue why-chain, slice 1). Every goal is read against why it
// matters: a guest sees an example mission marked as one, Edit opens one input, saving keeps it, an empty save
// brings the example back.
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
  const okr = () => { w.goTab("okr"); return d.querySelector('.gm-mission'); };
  const stored = () => { try { return JSON.parse(w.localStorage.getItem("gm_mission") || '""'); } catch (x) { return ""; } };
  let card = okr();

  ok("the Goals tab opens with a mission line above the objectives", !!card, card ? "no .gm-mission line" : "no mission line");
  ok("as a guest it shows an example, marked as one", !!card && /example/i.test(card.textContent),
    card ? card.textContent.slice(0, 160) : "no mission line");
  ok("the example offers an Edit link", !!card && !!card.querySelector('a.gm-inl'), card ? card.innerHTML.slice(0, 200) : "no mission line");

  if (card) {
    const edit = card.querySelector('a.gm-inl');
    if (edit) edit.click();
    card = okr();
    const inputs = card ? card.querySelectorAll('input') : [];
    ok("Edit opens exactly one input", inputs.length === 1, inputs.length + " inputs");
    const inp = d.getElementById("gmMissionText"), save = card && card.querySelector('[data-mission-save]');
    if (inp && save) {
      inp.value = "Leave my family calmer, safer and with more choice";
      save.click();
    }
    card = okr();
    ok("saving stores the mission in gm_mission", stored() === "Leave my family calmer, safer and with more choice", JSON.stringify(stored()));
    ok("and shows it in place of the example", !!card && /calmer, safer/.test(card.textContent) && !/example/i.test(card.textContent),
      card ? card.textContent.slice(0, 160) : "no mission line");

    const edit2 = card && card.querySelector('a.gm-inl');
    if (edit2) edit2.click();
    card = okr();
    const inp2 = d.getElementById("gmMissionText"), save2 = card && card.querySelector('[data-mission-save]');
    ok("the saved mission is open to change", !!inp2 && inp2.value === "Leave my family calmer, safer and with more choice",
      inp2 ? inp2.value : "no input");
    if (inp2 && save2) { inp2.value = "   "; save2.click(); }
    card = okr();
    ok("an empty save brings the example back", !!card && /example/i.test(card.textContent) && !w.localStorage.getItem("gm_mission"),
      card ? card.textContent.slice(0, 160) : "no mission line");
  }
  console.log("test123 okr mission: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
