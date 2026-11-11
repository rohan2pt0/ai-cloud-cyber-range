// v42: ask once (owner, 2026-11-11). The profile from Setup is the one source for facts other screens used to ask again:
// Career and the Life Map read it when their own field is empty and write a change back; editing the profile keeps the
// children and loans it already holds (it used to erase them); the Kids tab's add form is folded, not an empty form.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, G = k => JSON.parse(w.localStorage.getItem(k) || "null"), sec = () => d.getElementById("sections");
  // Career reads the profile
  w.goTab("career");
  const vals = [...sec().querySelectorAll("input")].map(i => i.value);
  ok("Career shows the profile's take-home, gross, spending and investments", ["200000", "300000", "90000", "2500000"].every(v => vals.includes(v)), vals.slice(0, 20).join(","));
  ok("Career shows the birth month and retirement age from the profile", vals.includes("1990-05") && vals.includes("50"));
  // a change in Career goes back to the profile
  w.gmCarSet("cur.inhand", "210000");
  ok("a Career edit updates the profile", G("sovP").net === 210000 && w.eval("P").net === 210000);
  ok("…and keeps the profile's children and loans", G("sovP").kids.length === 1 && G("sovP").loans.length === 1);
  // the Life Map reads the profile too
  w.goTab("life");
  const L = (k) => { const i = [...sec().querySelectorAll("input")].find(x => (x.getAttribute("onchange") || "").includes("gmLifeSet('" + k + "'")); return i ? i.value : "(none)"; };
  ok("Life Map: ages come from the birth dates, child included", (() => { const t = sec().textContent, n = (re) => +((t.match(re) || [])[1] || 0); return n(/Your age: (\d+)/) >= 36 && n(/Spouse age: (\d+)/) >= 34 && n(/First child: (\d+)/) >= 4; })(), sec().textContent.slice(0, 300));
  ok("Life Map: income, net worth and emergency fund in lakh from the profile", L("inc") === "31.2" && L("nw") === "25" && L("ef") === "4", [L("inc"), L("nw"), L("ef")].join(","));
  w.gmLifeSet("nw", "30");
  ok("a Life Map net worth edit updates the profile in rupees", G("sovP").nw === 3000000);
  w.goTab("life"); ok("a typed Life Map value wins over the profile", L("nw") === "30" && G("gm_life").nw === "30");
  // editing the profile keeps the children and loans (it used to erase them)
  w.editProfile();
  ok("Setup edit shows the child and the loan already there", d.querySelectorAll("#kidList input")[0].value === "FakeKid" && d.querySelectorAll("#loanList input")[0].value === "1000000");
  w.buildDash();
  ok("saving the profile again keeps them", G("sovP").kids.length === 1 && G("sovP").kids[0].name === "FakeKid" && G("sovP").loans.length === 1);
  // the Kids tab: the add form is folded, so nothing looks like it is asking again
  w.goTab("kids");
  const add = sec().querySelector("details.gm-kid-add");
  ok("Kids: the add form is folded and closed", add && !add.open && /Add another child/.test(add.querySelector("summary").textContent));
  // an example profile is never copied into the person's screens
  w.eval("P.example = true"); w.localStorage.removeItem("gm_life"); w.goTab("life");
  ok("an example profile does not fill the Life Map", L("age") === "");
  console.log("test42 ask once: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
