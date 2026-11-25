// test166: the real night sky (owner 2026-11-24): the stars, planets, Milky Way, meteors and comets the person would see if
// they looked up now. Pure checks on the engine (shared/sky.js with the catalogue in shared/stars.js), no browser.
const fs = require('fs'), path = require('path'), vm = require('vm');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const dir = path.join(__dirname, '..', 'shared'), ctx = { window: {}, Math, Date, Float32Array, Uint8ClampedArray, Intl, console };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(dir, 'stars.js'), 'utf8'), ctx);
vm.runInContext(fs.readFileSync(path.join(dir, 'sky.js'), 'utf8'), ctx);
const X = ctx.window.SXSky, t = (s) => Date.parse(s), MUM = [19.0, 72.8];
const angle = (r1, d1, r2, d2) => { const R = Math.PI / 180; return Math.acos(Math.min(1, Math.sin(d1 * R) * Math.sin(d2 * R) + Math.cos(d1 * R) * Math.cos(d2 * R) * Math.cos((r1 - r2) * R))) / R; };

// 1. sidereal time: Meeus, Astronomical Algorithms, example 12.a: 1987 April 10, 0h UT, GMST = 13h 10m 46.3668s = 197.693195 deg
ok("GMST matches Meeus example 12.a (within 0.001 deg)", Math.abs(X.gmst(Date.UTC(1987, 3, 10)) - 197.693195) < .001, X.gmst(Date.UTC(1987, 3, 10)));

// 2. the catalogue: the Yale Bright Star Catalogue to V 5.3, compact
const C = X.catalogue(t("2026-12-14T00:00:00Z"));
ok("between 1,500 and 2,500 catalogue stars", C && C.n >= 1500 && C.n <= 2500, C && C.n);
ok("the data file stays under 60 KB", fs.statSync(path.join(dir, 'stars.js')).size < 60000, fs.statSync(path.join(dir, 'stars.js')).size);
ok("the brightest is Sirius (V -1.46, RA 6h45m, Dec -16.7)", Math.abs(C.m[0] + 1.46) < .05 && Math.abs(C.ra[0] - 101.5) < 1 && Math.abs(C.dec[0] + 16.7) < .5, [C.m[0], C.ra[0], C.dec[0]].join(","));
ok("about thirty familiar constellations and the zodiac, as line sets", C.cons.length >= 30 && ["Ori", "UMa", "Cas", "Sco", "Leo", "Tau", "Gem", "Ari", "Cnc", "Vir", "Lib", "Sgr", "Cap", "Aqr", "Psc"].every(a => C.cons.some(k => k.ab === a)));

// 3. Polaris stands at the observer's latitude
let pol = -1; for (let i = 0; i < C.n; i++) if (C.dec[i] > 89 && C.m[i] < 2.3) pol = i;
for (const [lat, lon, name] of [[19.0, 72.8, "Mumbai"], [51.5, -.1, "London"], [40.7, -74, "New York"]]) {
  const a = [0, 6, 13, 19].map(h => X.starAltAz(C.ra[pol], C.dec[pol], t("2026-12-14T00:00:00Z") + h * 3600e3, lat, lon).alt);
  ok("Polaris is at the latitude within 1 deg from " + name, pol >= 0 && a.every(x => Math.abs(x - lat) < 1), a.map(x => x.toFixed(2)).join(","));
}

// 4. Sirius: below the horizon from Mumbai at noon in December, high at the winter midnight
const sNoon = X.starAltAz(C.ra[0], C.dec[0], t("2026-12-21T12:00:00+05:30"), ...MUM).alt, sMid = X.starAltAz(C.ra[0], C.dec[0], t("2026-12-22T00:00:00+05:30"), ...MUM).alt;
ok("Sirius is below the horizon at noon, 21 December 2026, Mumbai", sNoon < 0, sNoon);
ok("Sirius is well up at midnight, 22 December 2026, Mumbai", sMid > 30, sMid);
// Orion stands high in the south-west at 02:00 IST on the Geminid night, as the real sky has it
const ori = X.starAltAz(C.ra[C.cons.find(k => k.ab === "Ori").L[0][0]], C.dec[C.cons.find(k => k.ab === "Ori").L[0][0]], t("2026-12-14T02:00:00+05:30"), ...MUM);
ok("Betelgeuse high in the southern sky at 02:00 on 14 December 2026", ori.alt > 55 && ori.az > 150 && ori.az < 290, ori.alt.toFixed(1) + " / " + ori.az.toFixed(1));

// 5. the planets, against known events: the great conjunction of 21 December 2020 (Jupiter and Saturn 0.1 deg apart near
//    RA 20h10m = 302.5 deg, Dec -20.5 deg) and Jupiter's opposition of 3 November 2023 (opposite the sun)
const pc = X.planets(t("2020-12-21T18:00:00Z")), J = pc.find(p => p.name === "Jupiter"), S = pc.find(p => p.name === "Saturn");
ok("Jupiter at RA 302.5, Dec -20.5 on 21 December 2020 (within 2 deg)", Math.abs(J.ra - 302.5) < 2 && Math.abs(J.dec + 20.5) < 2, J.ra.toFixed(2) + " " + J.dec.toFixed(2));
ok("Jupiter and Saturn within half a degree at the great conjunction", angle(J.ra, J.dec, S.ra, S.dec) < .5, angle(J.ra, J.dec, S.ra, S.dec).toFixed(3));
const jo = X.planets(t("2023-11-03T05:00:00Z")).find(p => p.name === "Jupiter"), so = X.sun(t("2023-11-03T05:00:00Z"), 0, 0);
ok("Jupiter's phase angle is near 0 at its 2023 opposition (it faces the sun)", jo.phase < 1, jo.phase.toFixed(2));
ok("Jupiter at opposition is about magnitude -2.9", Math.abs(jo.mag + 2.9) < .25, jo.mag.toFixed(2));
const ve = X.planets(t("2026-11-24T12:00:00Z")).find(p => p.name === "Venus");
ok("Venus is the brightest planet and never fainter than -3.8", ve.mag < -3.8 && ve.mag > -5, ve.mag.toFixed(2));

// 6. colour and light
const bet = X.bvRGB(1.85), rig = X.bvRGB(-.03), sun = X.bvRGB(.65);
ok("Betelgeuse (B-V 1.85) is orange, Rigel (-0.03) blue-white", bet[0] > bet[2] + 40 && rig[2] >= rig[0], bet.join(",") + " / " + rig.join(","));
ok("B-V 0.65 gives a sun-like 5,800 K (Ballesteros)", Math.abs(sun.T - 5800) < 250, sun.T);
ok("the Milky Way is brightest toward the galactic centre", X.milkyWay(0, -2) > 3 * X.milkyWay(180, 0), X.milkyWay(0, -2).toFixed(2) + " / " + X.milkyWay(180, 0).toFixed(2));
ok("the Coalsack is dark against the band beside it", X.milkyWay(301.5, -.8) < .6 * X.milkyWay(296, -.8));

// 7. meteors: a Geminid peak night against a quiet one, at the same sky darkness
const gem = X.meteorRate(t("2026-12-14T02:00:00+05:30"), ...MUM, 6.0), quiet = X.meteorRate(t("2026-03-10T02:00:00+05:30"), ...MUM, 6.0);
ok("a Geminid peak night has more than 10 times the meteor rate of a quiet night", gem.total > 10 * quiet.total, gem.total.toFixed(1) + " vs " + quiet.total.toFixed(1));
ok("a quiet night is the sporadic background, 3 to 12 an hour", quiet.showers.length === 0 && quiet.total > 3 && quiet.total < 12, quiet.total.toFixed(1));
ok("no meteors in daylight", X.meteorRate(t("2026-12-14T13:00:00+05:30"), ...MUM, 6.0).total === 0);
ok("a bright moon lowers the rate (fewer faint meteors)", X.meteorRate(t("2026-12-14T02:00:00+05:30"), ...MUM, 4.5).total < gem.total / 2);

// 8. comets: only real ones, only when bright
ok("no comet is drawn when none on the list is bright now", X.cometsAt(t("2026-11-24T17:00:00Z")).length === 0 && X.cometsAt(t("2026-12-14T00:00:00Z")).length === 0);
ok("the same orbits do show NEOWISE in July 2020, when it was naked-eye", X.cometsAt(t("2020-07-15T00:00:00Z")).some(c => /NEOWISE/.test(c.name) && c.mag < 4), JSON.stringify(X.cometsAt(t("2020-07-15T00:00:00Z"))));
ok("an empty list draws none", X.cometsAt(t("2020-07-15T00:00:00Z"), []).length === 0);

// 9. the tap line names the brightest planet and the coming shower
X.placeSource = () => ({ lat: 19.0, lon: 72.8 });
const st = X.solve(t("2026-12-11T21:00:00+05:30")), line = X.nightLine(st, t("2026-12-11T21:00:00+05:30"));
ok("the tap line names a planet and the Geminids", /(Jupiter|Saturn|Venus|Mars|Mercury) (rising|setting|high) in the/.test(line) && /Geminids peak in 3 nights/.test(line), line);
ok("the sky darkens to magnitude 6 only in full night, by the real twilight", X.limitMag({ sun: { alt: -30 }, moon: { alt: -10, illum: 0 }, w: { cloud: 0 } }) === 6
  && X.limitMag({ sun: { alt: -6 }, moon: { alt: -10, illum: 0 }, w: { cloud: 0 } }) < 2.5 && X.limitMag({ sun: { alt: -30 }, moon: { alt: 50, illum: 1 }, w: { cloud: 0 } }) < 4.7);

console.log("test166 real night sky: " + P + " passed, " + F + " failed");
e.forEach(x => console.log("  FAIL " + x));
process.exit(F ? 1 : 0);
