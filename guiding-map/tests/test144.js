// test144: seamless sync, slice 3 (owner 2026-11-18: "it asks me to sign in again every day"). Microsoft gives a browser
// app 24 hours of refresh, fixed. A passing error keeps the sign-in; a real "sign in again" starts a silent full-page
// renewal (prompt=none) at most once in 6 hours; only when Microsoft truly needs the person does one calm line appear.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const enc = o => Buffer.from(JSON.stringify(o)).toString("base64").replace(/=+$/, "");
function boot(url, answer, pre) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url,
    beforeParse(w) {
      w.localStorage.setItem("gm_mine_done", "true");
      w.localStorage.setItem("gm_ms_cfg", JSON.stringify({ id: "fake-app-id-one" }));
      w.localStorage.setItem("gm_ms_tok", JSON.stringify({ access_token: "fake-a", refresh_token: "fake-r", expires_at: 1 }));
      if (pre) pre(w);
      w.__calls = [];
      w.fetch = (u, o) => { w.__calls.push(String(u)); if (/oauth2\/v2\.0\/token/.test(String(u))) return Promise.resolve({ json: () => Promise.resolve(answer) }); return Promise.reject(new Error("offline")); };
      w.scrollTo = () => {}; w.alert = () => {};
    } });
}
const busy = boot("https://hub.securax.localhost/app/", { error: "server_error" });
const gone = boot("https://hub.securax.localhost/app/", { error: "invalid_grant" });
const back = boot("https://hub.securax.localhost/app/?error=login_required&error_description=x", {}, w => w.sessionStorage.setItem("gm_ms_silent", "1"));
const good = boot("https://hub.securax.localhost/app/?code=fake-code", { access_token: "fake-b", refresh_token: "fake-r2", expires_in: 3600,
  id_token: "x." + enc({ preferred_username: "someone" + String.fromCharCode(64) + "example.org" }) + ".y" },
  w => { w.sessionStorage.setItem("gm_pkce", "fake-verifier"); w.sessionStorage.setItem("gm_ms_silent", "1"); w.localStorage.setItem("gm_ms_needs_signin", "true"); });
setTimeout(async () => {
  // 1. a passing error keeps the sign-in
  await busy.window.gmMsToken().catch(() => {});
  const bt = JSON.parse(busy.window.localStorage.getItem("gm_ms_tok") || "null");
  ok("a passing Microsoft error keeps the sign-in", !!bt && bt.refresh_token === "fake-r" && !bt.stale, JSON.stringify(bt));
  ok("…and starts no renewal", !busy.window.localStorage.getItem("gm_ms_silent_at"));
  // 2. a real sign-in answer starts one silent renewal, then waits 6 hours
  await gone.window.gmMsToken().catch(() => {});
  const gt = JSON.parse(gone.window.localStorage.getItem("gm_ms_tok") || "null");
  ok("an expired refresh keeps the record (sync stays on) and marks it stale", !!gt && gt.stale === 1, JSON.stringify(gt));
  ok("…and starts a silent renewal", !!gone.window.localStorage.getItem("gm_ms_silent_at"));
  ok("a second renewal inside 6 hours is not started", gone.window.gmMsSilent() === false);
  // 3. Microsoft could not complete it silently: one calm line with one tap
  back.window.goTab("today"); back.window.renderAll();
  const line = back.window.document.querySelector(".gm-ms-again");
  ok("a silent renewal Microsoft could not finish shows one calm Sign in line", !!line && /Sign in/.test(line.textContent) && !/error/i.test(line.textContent), line && line.textContent);
  ok("…and the address bar is clean", !/error=/.test(back.window.location.href));
  // 4. a completed renewal keeps the account hint and clears the line
  await new Promise(r => setTimeout(r, 300));
  const ls = good.window.localStorage;
  ok("a completed renewal stores the new token", /fake-b/.test(ls.getItem("gm_ms_tok") || ""));
  ok("…keeps the account's sign-in name as the next hint", /someone/.test(ls.getItem("gm_ms_hint") || ""), ls.getItem("gm_ms_hint"));
  ok("…and clears the Sign in line", !ls.getItem("gm_ms_needs_signin"));
  console.log("test144 silent Microsoft renewal: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1800);
