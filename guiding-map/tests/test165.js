// test165: the live sky (owner 2026-11-23): the sun from the NOAA equations, the moon and its phase from a lunar ephemeris,
// twilight bands at the real altitudes, cloud cover mapped to the cloud field, the place without asking, a scrim that keeps
// white text at AA at every sun altitude, and no weather fetch without the consent the wind already asks for. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1990-01-01", country: "India", cur: "INR", gross: 100000, net: 80000, exp: 50000, sav: 200000, ret: 60, tsav: 20, example: false };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
function boot(store, calls) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
      w.localStorage.setItem("gm_quick_done", "true"); Object.keys(store).forEach(k => w.localStorage.setItem(k, store[k]));
      w.matchMedia = mm; w.scrollTo = () => {};
      w.fetch = (u) => { calls.push(String(u)); return /open-meteo/.test(u)
        ? Promise.resolve({ ok: true, json: () => Promise.resolve({ current: { wind_speed_10m: 12, wind_direction_10m: 250, cloud_cover: 40, weather_code: 61, is_day: 1 } }) })
        : Promise.reject(new Error("offline")); };
    } });
}
const none = [], dNone = boot({}, none);
const off = [], dOff = boot({ gm_wind: JSON.stringify({ ok: false }) }, off);
const yes = [], dYes = boot({ gm_wind: JSON.stringify({ ok: true, lat: 19.1, lon: 72.9 }) }, yes);
setTimeout(() => {
  const w = dNone.window, X = w.SXSky, t = (s) => Date.parse(s);
  ok("the live sky is in the built Life OS", !!X && typeof X.sun === "function" && typeof X.moon === "function");
  // 1. the sun, against NOAA's solar calculator
  const sM = X.sun(t("2026-06-21T12:30:00+05:30"), 19.0, 72.8).alt, sL = X.sun(t("2026-12-21T12:00:00Z"), 51.5, -0.13).alt, sN = X.sun(t("2026-06-21T00:00:00+05:30"), 19.0, 72.8).alt;
  ok("Mumbai, 21 June 2026, 12:30 IST: the sun about 85 deg up (within 1 deg)", Math.abs(sM - 85) < 1, sM);
  ok("London, 21 December 2026, 12:00 UTC: about 15 deg (within 1 deg)", Math.abs(sL - 15) < 1, sL);
  ok("Mumbai at midnight: more than 40 deg below the horizon", sN < -40, sN);
  ok("the sun rises in the east and sets in the west", Math.abs(X.sun(t("2026-03-20T06:40:00+05:30"), 19, 72.8).az - 90) < 6 && Math.abs(X.sun(t("2026-03-20T18:50:00+05:30"), 19, 72.8).az - 270) < 6);
  // 2. the moon's phase, against known full and new moons (within a day)
  const peak = (iso, want) => { let best = null; for (let h = -72; h <= 72; h++) { const ms = t(iso) + h * 3600e3, k = X.moon(ms, 19, 72.8).illum, v = want === "full" ? k : -k;
    if (!best || v > best.v) best = { v, h }; } return best.h; };
  ok("full moon of 23 April 2024 (23:49 UTC) within a day", Math.abs(peak("2024-04-23T23:49:00Z", "full")) <= 24, peak("2024-04-23T23:49:00Z", "full"));
  ok("full moon of 18 September 2024 (02:34 UTC) within a day", Math.abs(peak("2024-09-18T02:34:00Z", "full")) <= 24, peak("2024-09-18T02:34:00Z", "full"));
  ok("new moon of 8 April 2024 (18:21 UTC, the eclipse) within a day", Math.abs(peak("2024-04-08T18:21:00Z", "new")) <= 24, peak("2024-04-08T18:21:00Z", "new"));
  ok("the phase has a name a person knows", X.moon(t("2024-04-23T23:49:00Z"), 19, 72.8).phase === "full moon" && X.moon(t("2024-04-15T19:13:00Z"), 19, 72.8).phase === "first quarter");
  // 3. twilight bands at the real altitudes
  const B = [[0, "day"], [-0.9, "civil"], [-5.9, "civil"], [-6.1, "nautical"], [-11.9, "nautical"], [-12.1, "astronomical"], [-17.9, "astronomical"], [-18.1, "night"]];
  ok("twilight switches at -6, -12 and -18 deg", B.every(([a, b]) => X.band(a) === b), JSON.stringify(B.map(([a]) => X.band(a))));
  const ps = X.placeSource; X.placeSource = () => ({ lat: 19, lon: 72.8 });   // Mumbai, as if the person had allowed it
  ok("the stars come out with the twilight: a dark sky at night, a bright one at noon",
    X.skyColour(60, 0, t("2026-06-21T00:00:00+05:30")).reduce((a, b) => a + b) < 120 && X.skyColour(60, 0, t("2026-06-21T12:30:00+05:30")).reduce((a, b) => a + b) > 300);
  X.placeSource = ps;
  // 4. cloud cover sets how much of the field is cloud; the weather code names what falls
  const covers = [0, 10, 25, 40, 60, 75, 90, 100], share = covers.map(c => X.cloudShare(c));
  ok("cloud_cover maps to the share of the sky that is cloud (within 5 points)", covers.every((c, i) => Math.abs(share[i] - c / 100) <= .05), share.map(x => x.toFixed(2)).join(","));
  ok("more cover, more cloud", share.every((s, i) => i === 0 || s >= share[i - 1]));
  ok("WMO codes: rain, drizzle, snow, fog, storm, clear", X.weatherKind(61) === "rain" && X.weatherKind(81) === "rain" && X.weatherKind(53) === "drizzle" && X.weatherKind(73) === "snow"
    && X.weatherKind(45) === "fog" && X.weatherKind(95) === "storm" && X.weatherKind(2) === "clear");
  // 5. the place, never asked: the allowed rounded place, else the time zone's city, else 0,0
  ok("no consent: the time zone's city (Asia/Kolkata gives Mumbai)", JSON.stringify(X.place("Asia/Kolkata")) === JSON.stringify({ lat: 19, lon: 72.8, src: "zone" }), JSON.stringify(X.place("Asia/Kolkata")));
  ok("an unknown zone: 0, 0", X.place("Mars/Olympus").lat === 0 && X.place("Mars/Olympus").lon === 0);
  // 6. the scrim: white text keeps AA (4.5:1) on every pixel of the sky, at every sun altitude through a day, clear or cloudy
  const lin = v => { v /= 255; return v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
  let worst = 99;
  for (let m = 0; m < 1440; m += 20) { const ms = t("2026-06-21T00:00:00+05:30") + m * 6e4;
    for (const alt of [0.5, 3, 10, 25, 50, 80]) for (const az of [0, 60, 120, 180, 240, 300]) {
      const c = X.capped(X.skyColour(alt, az, ms).map(lin)), L = .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; worst = Math.min(worst, 1.05 / (L + .05)); } }
  ok("white text on the scrimmed sky: at least 4.5:1 at every altitude and hour", worst >= 4.5, worst.toFixed(2));
  // 7. one line says what the sky is doing
  const line = X.describe(X.solve(t("2026-11-23T18:10:00+05:30")));
  ok("one tap says it in words: sun, cloud, moon, and the next sunrise or sunset", /^Your sky now: sun \d+° (above|below) the horizon/.test(line) && /moon/.test(line) && /(cloud|clear)/.test(line), line);
  // 7b. the lock by day (owner 2026-11-24: "Live sky is gone from lock screen"): the full sky, the sun in view, a scrim only behind the card
  X.placeSource = () => ({ lat: 19, lon: 72.8 });
  const card = { l: 24, r: 366, t: 196, b: 683 }, lumPx = (px, i) => .2126 * lin(px[i]) + .7152 * lin(px[i + 1]) + .0722 * lin(px[i + 2]);
  let open = 0, behind = 0, sunOk = [];
  for (const hm of ["07:00", "11:00", "15:59", "17:45"]) {
    const f = X.lockFrame(t("2026-11-24T" + hm + ":00+05:30"), 390, 844, card);
    for (let i = 0; i < f.gw * f.gh; i++) { const l = lumPx(f.px, i * 4); if (f.mask[i] === 0) open = Math.max(open, l); else if (f.mask[i] >= .999) behind = Math.max(behind, l); }
    const s = f.sun; sunOk.push(hm + (s.inView && (s.y > card.b || s.y < card.t) ? " in view" : " MISSING " + JSON.stringify(s)));
  }
  ok("the lock by day applies no global ceiling: the open sky is far brighter than the text ceiling", open > .3 && open > 2 * X.CAP, open.toFixed(3));
  ok("behind the card the scrim still holds every pixel under the ceiling (white text stays AA)", behind <= X.CAP + .005, behind.toFixed(3));
  ok("the sun is in the lock's view by day, never behind the card", sunOk.every(x => / in view$/.test(x)), sunOk.join("; "));
  ok("the scrim is soft and local: full behind the card, none in the open sky", X.scrimWeight(195, 400, card) === 1 && X.scrimWeight(195, 20, card) === 0 && X.scrimWeight(195, card.b + 30, card) > 0 && X.scrimWeight(195, card.b + 30, card) < 1);
  const night = X.lockFrame(t("2026-11-24T22:00:00+05:30"), 390, 844, card);
  ok("the night lock keeps its own sky (south or the moon, the horizon at the bottom)", night.a0 >= 0 && night.sun.inView === false);
  ok("no clouds are drawn when cloud_cover is unknown (no consent yet): a clear sky, never invented clouds", X.weatherSource() === null && X.cloudPlan(X.solve(Date.now()).w, 3).draw === false
    && X.cloudPlan({ real: true, cloud: 40, kind: "clear" }, 3.4).draw === true && X.cloudPlan({ real: false, cloud: 70, kind: "rain" }, 5).draw === false);
  // the caption: a city, or whole degrees; never the rounded place itself
  X.placeSource = () => ({ lat: 19.07, lon: 72.88 });
  const c1 = X.caption(X.solve(t("2026-11-24T15:59:00+05:30")));
  X.placeSource = () => ({ lat: 23.34, lon: 80.123 });
  const c2 = X.caption(X.solve(t("2026-11-24T15:59:00+05:30")));
  X.placeSource = () => null;
  const c3 = X.caption(X.solve(t("2026-11-24T15:59:00+05:30")));
  ok("the caption names the city near the person's place, the sun and the cloud reading", /^Your sky over Mumbai · sun \d+° · no cloud reading yet$/.test(c1), c1);
  ok("the caption names no place more precise than a city: whole degrees away from a known city, never decimals", c2 === c2.replace(/\d+\.\d+/g, "") && /Your sky over 23°N 80°E/.test(c2) && !/\d+\.\d/.test(c1 + c3), c2 + " | " + c3);
  ok("the time zone's city when no place is shared (Asia/Kolkata reads as Mumbai)", X.placeName({ lat: 19, lon: 72.8, src: "zone" }) === "Mumbai" && X.placeName({ lat: 0, lon: 0, src: "zone" }) === "" && X.placeName({ lat: 0, lon: 0, src: "none" }) === "");
  ok("the lock carries the caption style in the shared look", /\.sx-sky-cap\{[^}]*position:absolute/.test(html));
  X.placeSource = () => ({ lat: 19, lon: 72.8 });
  ok("the daypart follows the real sun", X.daypart(t("2026-11-23T13:00:00+05:30")) === "day" && X.daypart(t("2026-11-23T23:30:00+05:30")) === "night");
  X.placeSource = ps;
  // 8. surfaces opt in by attribute; a test DOM draws nothing (no canvas, no timer)
  const d = w.document; w.goTab("today"); w.renderAll();
  ok("the header and the greeting are sky surfaces", !!d.querySelector("header[data-sx-sky]") && !!d.querySelector(".gm-greet[data-sx-sky]"));
  w.goTab("life"); w.renderAll();
  ok("the net-worth hero is a sky surface, looking away from the sun", !!d.querySelector(".gm-hero[data-sx-sky='anti']"));
  ok("jsdom gets no canvas", d.querySelectorAll("canvas.sx-live-cv").length === 0);
  // 9. consent: no reading, no place, no fetch without it; with it, the same host and rounded place, more fields
  ok("no stored consent: no weather fetch", !none.some(u => /open-meteo/.test(u)), none.join(" "));
  dNone.window.gmWindFetch(true); dOff.window.gmWindFetch(true);
  ok("consent turned off: still no fetch", !none.concat(off).some(u => /open-meteo/.test(u)), off.join(" "));
  ok("no consent: the sky has no place and no reading of its own", dNone.window.SXSky.placeSource() === null && dNone.window.SXSky.weatherSource() === null);
  const om = yes.filter(u => /open-meteo/.test(u));
  ok("with consent: one call to the same host, the same rounded place, wind plus cloud_cover, weather_code, is_day", om.length >= 1
    && /^https:\/\/api\.open-meteo\.com\/v1\/forecast\?latitude=19\.1&longitude=72\.9&current=wind_speed_10m,wind_direction_10m,cloud_cover,weather_code,is_day$/.test(om[0]), om.join(" "));
  setTimeout(() => {
    const ws = dYes.window.SXSky.weatherSource(), st = JSON.parse(dYes.window.localStorage.getItem("gm_wind"));
    ok("the reading is kept for offline, with the wind", st.cloud === 40 && st.code === 61 && st.isDay === 1 && st.speed === 12);
    ok("the sky reads it: 40% cloud, rain", ws && ws.cloud === 40 && dYes.window.SXSky.weatherKind(ws.code) === "rain", JSON.stringify(ws));
    ok("the sky's place is the allowed, rounded one", JSON.stringify(dYes.window.SXSky.place()) === JSON.stringify({ lat: 19.1, lon: 72.9, src: "yours" }));
    console.log("test165 live sky: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
  }, 300);
}, 1900);
