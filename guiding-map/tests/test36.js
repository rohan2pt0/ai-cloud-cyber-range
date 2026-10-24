// v36: "had your back" — the POSITIVE half of the estate feed. The Life OS home shows, up front, what the estate quietly
// did FOR you this week (a safe encrypted copy, a healthy estate, failures turned into fixes), drawn only from real events
// the estate already recorded (./securax lifefeed writes feed.wins). Small wins, shown — never folded, never invented.
const fs = require('fs'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = [];
const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
function boot(fetcher) {
  return new JSDOM(fs.readFileSync('index.html', 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) { w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
      w.fetch = (u, o) => fetcher ? fetcher(String(u), o) : Promise.reject(new Error("offline")); } });
}
const wins = [{ icon: "🛡", kind: "win", src: "backup", text: "Kept a safe, encrypted copy of your estate — newest backup is 1 day old, encrypted" },
  { icon: "🔧", kind: "win", src: "antifragile", text: "Turned 2 failure(s) into fixes — each one cannot bite twice" }];
const feedWith = (w) => ({ generated: "2026-10-24T08:00", items: [{ icon: "*", level: "info", text: "Certification now: CPTS", cmd: "./securax certs next" }], wins: w });
const fetcher = (feed) => (u) => u.endsWith("/portal/estate-feed.json") ? Promise.resolve({ ok: true, json: () => Promise.resolve(feed) }) : Promise.reject(new Error("offline"));

setTimeout(() => {
  const dom = boot(fetcher(feedWith(wins)));
  setTimeout(() => {
    const w = dom.window, d = w.document, txt = () => d.getElementById("sections").textContent;
    ok("Calm mode is the default (the home is rendered)", d.body.classList.contains("gm-calm") && txt().includes("worked out for you"), txt().slice(0, 120));
    ok("the home shows a 'had your back' card", /your estate had your back/i.test(txt()), txt().slice(0, 300));
    ok("it names the real wins, in plain words", txt().includes("safe, encrypted copy") && txt().includes("Turned 2 failure(s) into fixes"));
    ok("it says these are real and how to see more", txt().includes("Only things that really happened") && txt().includes("./securax progress"));
    const card = [...d.querySelectorAll(".road-col")].find((x) => /had your back/i.test(x.textContent));
    ok("the card is shown up front, not folded inside 'More today'", !!card && !card.closest("details"), card ? ("in details? " + !!card.closest("details")) : "no card");

    // empty wins → the card stays quiet (no false reassurance, no empty box)
    const dom2 = boot(fetcher(feedWith([])));
    setTimeout(() => {
      const t2 = () => dom2.window.document.getElementById("sections").textContent;
      ok("with no wins there is no card at all", !/had your back/i.test(t2()), t2().slice(0, 120));
      console.log("test36 had-your-back: " + P + " passed, " + F + " failed");
      if (F) { console.log(e.join("\n")); process.exit(1); } process.exit(0);
    }, 700);
  }, 700);
}, 100);
