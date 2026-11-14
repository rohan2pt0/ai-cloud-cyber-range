// v97: start simple grows gently (owner, 2026-11-14). A new person sees three doors (Money, Breaks, Life balance);
// one more door unlocks each week the app is used (risk, deadlines, systems, guide, stack), a just-unlocked door says
// "new", and "Show everything" still counts only what is left. The full sheet is unchanged when simple is off.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let P = 0, F = 0, e = [];
const ok = (c, m, d) => { c ? P++ : (F++, e.push(m + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const boot = (store) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { if (store) Object.keys(store).forEach((k) => w.localStorage.setItem(k, store[k]));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } }).window;
const day = (ago) => { const d = new Date(); d.setDate(d.getDate() - ago); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); };
const idOf = (b) => ((b.getAttribute("onclick") || "").match(/gmNavGo\('([^']+)'\)/) || [])[1];
const doors = (w) => {
  w.gmNavMore(true);
  const sh = w.document.getElementById("gmMoreSheet");
  const tiles = [...sh.querySelectorAll(".sh button[role=menuitem]")];
  return { sh, tiles, ids: tiles.map(idOf).filter(Boolean) };
};
const fresh = boot(null), grown = boot({ gm_first_open: JSON.stringify(day(15)) }), full = boot({ gm_simple: "false" });
setTimeout(() => {
  const main = ["today", "inbox", "okr", "ask"];
  // a new person: three doors, then Show everything whose number is what is left
  const a = doors(fresh);
  ok(a.ids.join() === "money,breaks,wheel", "a new person sees Money, Breaks and Life balance", a.ids.join());
  const leftA = fresh.TABS.filter((t) => main.indexOf(t[0]) < 0 && ["money", "breaks", "wheel"].indexOf(t[0]) < 0).length;
  ok(new RegExp("Show everything \\(" + leftA + " more\\)").test(a.sh.textContent), "Show everything stays and counts what is left", (a.sh.textContent.match(/Show everything[^<]*/) || [])[0]);
  ok(/^\d{4}-\d{2}-\d{2}$/.test(JSON.parse(fresh.localStorage.getItem("gm_first_open"))), "the first-open date is stored once, as a plain date");
  // fifteen days of use: two more doors, and only the newest says new
  const b = doors(grown);
  ok(b.ids.join() === "money,breaks,wheel,risk,deadlines", "two weeks unlock risk, then deadlines", b.ids.join());
  const risk = b.tiles.find((x) => idOf(x) === "risk"), dl = b.tiles.find((x) => idOf(x) === "deadlines");
  ok(risk && !risk.querySelector(".gm-new"), "risk unlocked a week ago, so it is not new");
  ok(dl && dl.querySelector(".gm-new") && /new/i.test(dl.textContent), "deadlines unlocked this week, so it says new", dl && dl.textContent);
  const leftB = grown.TABS.filter((t) => main.indexOf(t[0]) < 0 && ["money", "breaks", "wheel", "risk", "deadlines"].indexOf(t[0]) < 0).length;
  ok(new RegExp("Show everything \\(" + leftB + " more\\)").test(b.sh.textContent), "the count drops as doors unlock", (b.sh.textContent.match(/Show everything[^<]*/) || [])[0]);
  // everything mode is unchanged
  const c = doors(full);
  ok(c.ids.slice(0, 6).join() === "risk,deadlines,systems,money,breaks,wheel", "with simple off the full sheet keeps its order", c.ids.slice(0, 6).join());
  ok(!c.sh.querySelector(".gm-new"), "the full sheet carries no new labels");
  console.log("test97 start simple grows gently: " + P + " passed, " + F + " failed");
  if (F) { e.forEach((x) => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
