// v141: S3 side income gets one small weekly system: "Build in public · this week's episode" (queue build-in-public,
// slice 1). One editable topic (prefilled from the newest done Inbox action), four one-tap steps kept in gm_bip
// {week:{steps:[...],link}}, a streak line of episodes published, the old S3 text folded under one closed
// "Why this works", and a permanent calendar item (bip-weekly, Saturday 10:00, 60 min). Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, box = d.getElementById("sections"), text = () => box.textContent;
  w.goTab("book");
  ok("S3 shows the Build in public card", text().includes("Build in public \u00b7 this week's episode"));
  const topic = d.getElementById("gmBipTopic");
  ok("the topic is one editable line", !!topic && topic.tagName === "INPUT" && topic.type === "text");
  ok("with no done Inbox action the topic falls back", !!topic && topic.value === "What I built or learned this week", topic && topic.value);
  const steps = [...box.querySelectorAll("input[data-bip]")];
  ok("four one-tap steps", steps.length === 4, steps.length + " steps");
  ["Record 10 min", "Cut one 60-second Short", "Post it with one lesson", "Log the link"].forEach((s, i) => ok("step " + (i + 1) + ": " + s, text().includes(s)));
  const whys = [...box.querySelectorAll("details")].filter(x => /^Why this works/.test(((x.querySelector("summary") || {}).textContent || "").trim()));
  ok("the original S3 text moves under one closed 'Why this works'",
    whys.length === 1 && !whys[0].hasAttribute("open") && /skill audit/i.test(whys[0].textContent) && /The ladder/i.test(whys[0].textContent),
    whys.length + " details");
  w.localStorage.setItem("gm_inbox", JSON.stringify([
    { id: "a1", t: "Older done action", kind: "action", done: "2026-11-01", created: 1 },
    { id: "a2", t: "Newest done action", kind: "action", done: "2026-11-17", created: 2 },
    { id: "a3", t: "Not done yet", kind: "action", done: "", created: 3 }
  ]));
  w.goTab("book");
  const topic2 = d.getElementById("gmBipTopic");
  ok("prefilled with the newest done Inbox action", !!topic2 && topic2.value === "Newest done action", topic2 && topic2.value);
  for (let i = 0; i < 4; i++) {
    const b = d.querySelectorAll("#sections input[data-bip]")[i];
    b.checked = true; b.dispatchEvent(new w.Event("change", { bubbles: true }));
  }
  const saved = JSON.parse(w.localStorage.getItem("gm_bip") || "{}");
  const week = Object.keys(saved)[0] || "";
  ok("state kept in gm_bip {week:{steps:[...],link}}",
    !!week && !!saved[week] && Array.isArray(saved[week].steps) && saved[week].steps.length === 4 &&
    saved[week].steps.every(Boolean) && typeof saved[week].link === "string", JSON.stringify(saved));
  ok("ticking all four shows the streak", /\b1 episode published\b/.test(text()), (text().match(/\d+ episodes? published/) || [""])[0]);
  const link = d.getElementById("gmBipLink");
  if (link) { link.value = "https://example.invalid/ep1"; link.dispatchEvent(new w.Event("change", { bubbles: true })); }
  const saved2 = JSON.parse(w.localStorage.getItem("gm_bip") || "{}");
  ok("the link is kept in the same week", !!week && saved2[week] && saved2[week].link === "https://example.invalid/ep1", week && saved2[week] && saved2[week].link);
  const reg = w.gmCalendarRegistry();
  const item = reg.filter(x => x.id === "bip-weekly")[0];
  ok("bip-weekly is a permanent calendar id", !!item && item.group === "bip" && item.v >= 1, JSON.stringify(item));
  const ics = w.gmCalendarICS("bip");
  ok("bip-weekly is Saturday 10:00 for 60 minutes",
    /DTSTART:2026\d{4}T100000/.test(ics) && /DTEND:2026\d{4}T110000/.test(ics) && /RRULE:FREQ=WEEKLY;BYDAY=SA/.test(ics), ics.split("\r\n").filter(l => /^(DTSTART|DTEND|RRULE)/.test(l)).join(" "));
  ok("the card adds the bip calendar", !!box.querySelector("[onclick=\"gmCalendar('bip')\"]"));
  console.log("test141 Build in public: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
