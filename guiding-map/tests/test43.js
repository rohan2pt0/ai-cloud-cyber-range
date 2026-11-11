// v43: ask by frequency (owner, 2026-11-11). Fixed facts fold under one line after the first set-up; the numbers that change
// sit in one small "My numbers" card (Money and Life Map) with when they were last updated; ages from birth dates are shown,
// not asked. First set-up is unchanged: everything open.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "Faketown", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [], ret: 50, tsav: 20, dream: "UAE", goal: "Fake goal", example: false };
const boot = (seed) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { Object.entries(seed).forEach(([k, v]) => w.localStorage.setItem(k, JSON.stringify(v)));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const A = boot({ sovP: prof, gm_career: { cur: { inhand: 111111 }, house: {}, cfg: {}, done: {}, gaps: {} } }), B = boot({});
setTimeout(() => {
  const w = A.window, d = w.document, G = k => JSON.parse(w.localStorage.getItem(k) || "null"), sec = () => d.getElementById("sections");
  // 1. editing the profile: fixed facts folded under one line that shows them; the money fields in view
  w.editProfile();
  const fa = d.getElementById("w_fixA"), fb = d.getElementById("w_fixB");
  ok("edit: About you is folded and its line shows the facts", !fa.open && /Fake/.test(fa.querySelector("summary").textContent) && /Faketown/.test(fa.querySelector("summary").textContent) && /1990/.test(fa.querySelector("summary").textContent), fa.querySelector("summary").textContent);
  ok("edit: Family and vision is folded and shows partner, children and retirement age", !fb.open && /FakePartner/.test(fb.querySelector("summary").textContent) && /1 child/.test(fb.querySelector("summary").textContent) && /retire by 50/.test(fb.querySelector("summary").textContent), fb.querySelector("summary").textContent);
  ok("edit: the money fields are not folded", !d.getElementById("w_nw").closest("details") && d.getElementById("w_nw").value === "2500000");
  ok("edit: the button says Save changes", /Save changes/.test(d.getElementById("w_go").textContent));
  d.getElementById("w_nw").value = "2600000"; w.buildDash();
  ok("saving keeps the folded facts", G("sovP").name === "Fake" && G("sovP").dob === "1990-05-15" && G("sovP").kids.length === 1 && G("sovP").nw === 2600000);
  // 2. first set-up: nothing folded
  const bd = B.window.document;
  ok("first set-up: everything open, as before", bd.getElementById("w_fixA").open && bd.getElementById("w_fixB").open && /Build My Command Center/.test(bd.getElementById("w_go").textContent));
  // 3. My numbers on Money: the changing facts only, saved to the profile, with when
  w.goTab("money");
  const card = sec().querySelector("details.gm-nums");
  ok("Money: a 'My numbers' card with the four changing numbers", card && card.querySelectorAll("input").length === 4 && /not updated since set-up/.test(card.textContent));
  w.gmNumSet("nw", "2700000");
  ok("a number saved there updates the profile and stamps the day", G("sovP").nw === 2700000 && G("sovP").numsAt === new Date().toISOString().slice(0, 10));
  w.goTab("money");
  ok("…and the card says updated today", /updated today/.test(sec().querySelector("details.gm-nums").textContent));
  w.gmNumSet("net", "222222");
  ok("…and Career follows instead of keeping its older copy", !(G("gm_career").cur || {}).inhand && G("sovP").net === 222222);
  // 4. Life Map: the card is there too, ages are shown not asked
  w.goTab("life");
  const s = sec();
  ok("Life Map: the same My numbers card", !!s.querySelector("details.gm-nums"));
  const ageInput = [...s.querySelectorAll("input")].some(i => (i.getAttribute("onchange") || "").includes("gmLifeSet('age'"));
  ok("Life Map: your age is shown from the birth date, not asked", !ageInput && /Your age: \d+/.test(s.textContent) && /from your profile/.test(s.textContent));
  ok("Life Map: net worth follows the number just saved (27 lakh)", [...s.querySelectorAll("input")].some(i => (i.getAttribute("onchange") || "").includes("gmLifeSet('nw'") && i.value === "27"));
  // 5. an example profile shows no card
  w.eval("P.example = true"); w.goTab("money");
  ok("an example profile shows no My numbers card", !sec().querySelector("details.gm-nums"));
  console.log("test43 ask by frequency: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
