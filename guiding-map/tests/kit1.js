// kit1: Vantage (the first OS kit edition) used as a CISO would: start, capture and decide, tick a ritual, record a risk,
// start a goal, see the review rhythm come due, undo, back up and restore, sync merge rules, no script injection,
// and every screen renders. Data stays under its own names (osk:vantage:) and never touches the Life OS keys.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const PFX = "osk:vantage:";
const html = fs.readFileSync(path.join(__dirname, '..', 'vantage', 'index.html'), 'utf8');
const errs = [];
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/vantage/",
  beforeParse(w) {
    w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; w.URL.revokeObjectURL = () => {};
    w.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
    w.localStorage.setItem("gm_inbox", "[]");            // a Life OS key on the same address
    w.addEventListener("error", ev => errs.push(String(ev.message)));
  } });
const w = dom.window, d = w.document, K = () => w.OSK;
const main = () => d.getElementById("oskMain").innerHTML;
const click = (sel) => { const b = d.querySelector(sel); if (b) b.dispatchEvent(new w.MouseEvent("click", { bubbles: true })); return !!b; };
const set = (id, v) => { const x = d.getElementById(id); if (x) x.value = v; return !!x; };
const get = (k) => JSON.parse(w.localStorage.getItem(PFX + k) || "null");

setTimeout(() => {
  ok("the app started", !!K() && /Vantage/.test(d.title), d.title);
  const recent = (K().ed.whatsnew || []).some(n => K().days(n.date) <= 30);
  ok("recent kit news shows once on Today", !recent || /New in Vantage/.test(main()));
  if (recent) { click('[data-a="newsSeen"]'); ok("…and Got it hides it", !/New in Vantage/.test(main())); }
  ok("the core principles reached this app", K().ed.principles.filter(p => p.core).length >= 4 && K().ed.principles[0].core === true);
  ok("Today renders with the setup card", /Start in one minute/.test(main()));
  set("pfName", "Asha"); click('[data-a="profileSave"]');
  ok("profile saved and greeting uses it", /Asha/.test(main()) && get("profile").name === "Asha");

  // capture and decide
  set("ibText", "Renewal of the email security contract"); click('[data-a="ibAdd"]');
  ok("captured into the inbox", (get("inbox") || []).length === 1);
  K().go("inbox"); click('[data-a="ibDecide"]');
  set("ibNext", "Ask the vendor for the feature usage report"); click('[data-a="ibAction"]');
  ok("decided as an action with a date", get("inbox")[0].kind === "action" && !!get("inbox")[0].due);
  click('[data-a="ibDone"]');
  ok("action done", get("inbox")[0].done === true);

  // ritual
  K().go("today"); click('[data-a="ritTick"][data-x="brief"]');
  ok("ritual ticked for today", (get("rituals")[K().ymd()] || []).indexOf("brief") >= 0);
  ok("this week's wins show it", /ritual\(s\) kept/.test(main()));

  // a high risk without a date rises to Today
  K().go("registers:risks"); click('[data-a="regNew"]');
  set("rf_risk", "<img src=x onerror=window.__pwned=1> ransomware stops core systems"); set("rf_likelihood", "5"); set("rf_impact", "5"); set("rf_status", "Open");
  click('[data-a="regSave"]');
  ok("risk saved with its score", (get("reg.risks") || []).length === 1 && K().regScore({ score: ["likelihood", "impact"] }, get("reg.risks")[0]) === 25);
  ok("its text is shown as text, not markup", !d.querySelector("#oskMain img") && !w.__pwned);
  const n = K().nextStep();
  ok("the next step asks for a treatment date", n && /treatment date/.test(n.text), n && n.text);

  // goal from a starter
  K().go("goals"); click('[data-a="goalStarter"][data-x="0"]');
  ok("starter goal added with key results", (get("goals") || []).length === 1 && get("goals")[0].krs.length === 2);
  const kr = d.querySelector('input[data-c="krSet"]'); kr.value = "20"; kr.dispatchEvent(new w.Event("change", { bubbles: true }));
  ok("a key result moved halfway", Math.abs(K().krFrac(get("goals")[0].krs[0]) - 0.5) < 1e-9, JSON.stringify(get("goals")[0].krs[0]));

  // the rhythm comes due by itself
  w.localStorage.setItem(PFX + "started", JSON.stringify(K().addDays(K().ymd(), -10)));
  const due = K().nextStep();
  ok("a late review becomes the next step", due && /late|due today/.test(due.text), due && due.text);
  K().go("cadence"); click('[data-a="cadOpen"][data-x="w-risk"]'); click('[data-a="cadDone"][data-x="w-risk"]');
  ok("marking it done dates the next one a week on", K().cadenceDue(K().ed.modules.cadence.items[0]).due === K().addDays(K().ymd(), 7));

  // undo
  const before = (get("reg.risks") || []).length;
  K().go("registers:risks"); click('[data-a="regEdit"]'); click('[data-a="regDel"]');
  ok("deleted", (get("reg.risks") || []).length === before - 1);
  K().undo();
  ok("undo brings it back", (get("reg.risks") || []).length === before);

  // backup and restore
  const dump = K().dump();
  ok("the backup holds the app's data only", dump.app === "vantage" && dump.data["reg.risks"] && !dump.data["~undo"]);
  w.localStorage.removeItem(PFX + "goals"); K().load(dump);
  ok("restore brings the data back", (get("goals") || []).length === 1);
  let threw = false; try { K().load({ app: "other", data: {} }); } catch (x) { threw = true; }
  ok("a backup of another app is refused", threw);

  // sync merge rules
  const m0 = K().get("~meta", {}), t = (m0["profile"] || 0) + 1000;
  const remote = {}; remote[PFX + "profile"] = JSON.stringify({ name: "Asha R" }); remote["gm_inbox"] = '["not mine"]'; remote[PFX + "~undo"] = "[]";
  const meta = {}; meta[PFX + "profile"] = t;
  ok("a newer remote value is merged", K().merge(remote, meta) === 1 && get("profile").name === "Asha R");
  ok("other apps' keys and device-only keys are never taken", w.localStorage.getItem("gm_inbox") === "[]");
  const old = {}; old[PFX + "profile"] = JSON.stringify({ name: "stale" }); const om = {}; om[PFX + "profile"] = 1;
  K().merge(old, om);
  ok("an older remote value loses", get("profile").name === "Asha R");
  for (let i = 0; i < 12; i++) w.localStorage.setItem(PFX + "x" + i, "1");
  ok("a remote copy with far fewer of our keys is refused", K().merge({}, {}) === -1);

  // isolation and every screen
  const mine = Object.keys(w.localStorage).filter(k => k.indexOf("osk:") === 0);
  ok("every key the app wrote is under its own name", mine.every(k => k.indexOf(PFX) === 0) && mine.length > 5);
  const tabs = K().tabs();
  ok("all 18 screens are in the menu", tabs.length === 18, tabs.length);
  let broken = [];
  tabs.forEach(tb => { K().go(tb.id); if (/This screen hit a problem/.test(main()) || !main().trim()) broken.push(tb.id); });
  ok("every screen renders", !broken.length, broken.join(","));
  K().go("settings");
  ok("Settings marks the core principles and lists what is new", /core<\/span>/.test(main()) && /What's new/.test(main()));
  K().go("today");
  ok("the bottom menu shows four screens and More", d.querySelectorAll("#oskNav button").length === 5);
  ok("no page error", !errs.length, errs.join(" | "));

  console.log(`kit1 Vantage: ${P} passed, ${F} failed`); if (F) { console.log(e.join("\n")); process.exit(1); } process.exit(0);
}, 300);
