// v68: the focus timer, on Today only and used sparingly. One small secondary button under the one open action starts a
// 25-minute block; the slim bar at the top works the minutes out from the stored start time (so a sleeping phone or a
// reload stays right); when it is up a calm done message offers the next step; after four blocks the button rests for the
// day; and a Settings switch hides it entirely. No streaks, scores or sounds.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const ymd = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
const day = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return ymd(d); };
const today = ymd(new Date());
const seed = { gm_inbox: [{ id: "fakeLate", t: "Fake renew the health policy", next: "Fake renew the health policy", kind: "action", due: day(-3), vital: true, area: "Insurance", created: 1 }] };
const active = new Map();
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    Object.entries(seed).forEach(([k, v]) => w.localStorage.setItem(k, JSON.stringify(v)));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    const si = w.setInterval.bind(w), ci = w.clearInterval.bind(w);
    w.setInterval = function (fn, ms) { const id = si(fn, ms); active.set(id, ms); return id; };
    w.clearInterval = function (id) { active.delete(id); return ci(id); };
  } });
const timers = () => [...active.values()].filter(ms => ms === 15000).length;
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  const buttons = () => [...sec().querySelectorAll("button")];
  w.goTab("today");

  // 1. one small secondary button under the one open action
  const start = buttons().find(b => /Focus 25 min on this/.test(b.textContent));
  ok("Today's one open action offers 'Focus 25 min on this'", !!start, sec().textContent.slice(0, 300));
  ok("the focus button is secondary, never a primary", start && !/btn-p/.test(start.className));
  ok("the focus button is at least 44 px tall", start && /min-height:\s*44px/.test(start.getAttribute("style") || ""), start && start.getAttribute("style"));
  ok("no focus interval runs before a block starts", timers() === 0, timers());

  // 2. starting a block stores gm_focus and shows the slim running bar
  start.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  const f = JSON.parse(w.localStorage.getItem("gm_focus") || "null");
  ok("starting a block stores gm_focus", f && f.mins === 25 && typeof f.start === "number" && /Fake renew the health policy/.test(f.task || ""), JSON.stringify(f));
  const bar = d.getElementById("gmFocusBar");
  ok("the slim bar shows the task, the minutes left and Stop", bar && /Fake renew the health policy/.test(bar.textContent) && /min left/.test(bar.textContent) && /Stop/.test(bar.textContent), bar && bar.textContent);
  ok("exactly one 15 s interval runs while a block is running", timers() === 1, timers());

  // 3. a block whose stored start is 26 minutes ago is done: message shown, running block cleared, timer stopped
  const old = JSON.parse(w.localStorage.getItem("gm_focus"));
  old.start = Date.now() - 26 * 60 * 1000;
  w.localStorage.setItem("gm_focus", JSON.stringify(old));
  w.renderAll();
  ok("with a start 26 minutes ago the page shows the done message", /look far away for 5 minutes/.test(d.body.textContent), (d.getElementById("gmFocusBar") || {}).textContent);
  ok("the running block is cleared", !w.localStorage.getItem("gm_focus") || JSON.parse(w.localStorage.getItem("gm_focus")) === null, w.localStorage.getItem("gm_focus"));
  ok("no 15 s interval is left running after a block ends", timers() === 0, timers());
  ok("the done bar offers 'Mark the action done'", /Mark the action done/.test((d.getElementById("gmFocusBar") || {}).textContent || ""));

  // 4. after four blocks today the button rests for the day
  w.localStorage.setItem("gm_focus_log", JSON.stringify({ [today]: 4 }));
  w.renderAll();
  const rest = buttons().find(b => /Enough focus blocks today; work freely/.test(b.textContent));
  ok("after 4 logged blocks today the button says enough, work freely", !!rest, buttons().map(b => b.textContent).join("|"));
  ok("and it is disabled for the day", rest && rest.disabled === true);
  ok("no focus interval runs while resting", timers() === 0, timers());

  // 5. the Settings switch hides the timer entirely
  w.localStorage.setItem("gm_focus_show", "false");
  w.renderAll();
  ok("with the switch off no focus button renders", !buttons().some(b => /Focus 25 min|Enough focus blocks/.test(b.textContent)), buttons().map(b => b.textContent).join("|"));
  ok("with the switch off no focus bar renders", !d.getElementById("gmFocusBar"));

  console.log("test68 focus timer: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
