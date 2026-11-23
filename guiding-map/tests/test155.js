// test155: Coming up in your world (owner 2026-11-23): the next real events from facts already held, with nothing to type;
// three in view, the rest under Later; a waxing moon; late items say so. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(); const iso = (days, y) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return y + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake", dob: iso(40, 1989), pname: "Sam Example", pdob: iso(6, 1994), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000,
  kids: [{ name: "Kiddo", dob: iso(19, 2022) }], ret: 60, tsav: 20, example: false, earners: 2, partner: { net: 50000 },
  loans: [{ type: "Personal Loan", remaining: 84000, rate: 10, emi: 84000, tenure: 1 }, { type: "Home Loan", remaining: 5000000, emi: 40000, tenure: 300 }] };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const L = w.gmComingUp();
  ok("birthdays of the people at home come from the profile", L.some(x => /Sam turns 32/.test(x.t) && x.days === 6) && L.some(x => /Kiddo turns 4/.test(x.t)) && L.some(x => /Your birthday/.test(x.t)), JSON.stringify(L.map(x => [x.days, x.t])));
  ok("a loan's last EMI shows, with what it frees up", L.some(x => /Personal Loan: last EMI/.test(x.t) && /84,000 a month frees up/.test(x.s)));
  ok("a long loan does not", !L.some(x => /Home Loan/.test(x.t)));
  ok("the month-end check-in is always there", L.some(x => x.kind === "checkin"));
  ok("nearest first", L.every((x, i) => i === 0 || L[i - 1].days <= x.days));
  w.goTab("today"); w.renderAll();
  const c = d.querySelector(".gm-cu");
  ok("Today shows the card", !!c, (d.querySelector("#sections") || d.body).textContent.slice(0, 200));
  ok("three in view, the rest under Later", c && c.querySelectorAll(":scope > div[role=list] > .gm-cu-row").length === 3 && /Later \(\d+\)/.test(c.textContent));
  ok("each row has a moon and a when", c && c.querySelectorAll(".gm-moon").length === L.length && /in 6 days/.test(c.textContent));
  ok("nothing to type", c && !c.querySelector("input, textarea, select"));
  // the buffer as water in a glass vessel: the level is the months, a gold line is the aim; still for reduced motion
  w.gmWorkSet("me", "contract"); w.goTab("money"); w.renderAll();
  const v = d.querySelector(".gm-vessel svg");
  ok("the buffer is drawn as a vessel with its aim line", !!v && /Buffer: [\d.]+ months of 12 aimed for/.test(v.getAttribute("aria-label")) && /12m/.test(v.textContent), v && v.getAttribute("aria-label"));
  ok("the wave rests when less motion is asked for", /prefers-reduced-motion: reduce\)\{\.gm-wave\{animation:none\}/.test(html));
  console.log("test155 coming up: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
