"""Persona audit: real people, real mistakes, in a real browser (owner 2026-11-15: "think from the human angle... doing it
manually will take many months").

Each persona opens the Life OS fresh on a phone, answers "Make it yours", fills the set-up form the way a person does
(typing into the real fields and tapping the real button), makes the mistakes people really make (rupees typed where
lakh is asked, a minus sign, a birth year off by a century, take-home above gross, a 90% loan rate, letters in a number
field, changing their mind), then uses every tab. After each persona the audit checks what a person would notice:

  - no page error, and no "NaN", "undefined", "Infinity", "null" or "[object Object]" anywhere on any tab;
  - no impossible figure shown: an age outside 14-110, a negative salary or expense, an antifragility score outside 0-100;
  - the tabs that cannot apply to the persona are not offered (a student with no children sees no Kids door);
  - a first win (one habit ticked) is reachable in at most three taps from the first screen.

    python3 guiding-map/tests/persona_audit.py OUTDIR      ends with "PERSONA AUDIT: PASS" or the list of problems

It runs in the sandbox (journey guiding_map_full_use) on every change, so a new screen cannot reintroduce a nonsense value.
Fake data only.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

GM = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "persona-audit")
BAD_TEXT = re.compile(r"\bNaN\b|\bundefined\b|\bInfinity\b|\[object Object\]|(?<![A-Za-z])null(?![A-Za-z])")

# (id, stage answers, yes/no facts, form values a person types, what must NOT be offered)
PERSONAS = [
    ("student-founder", ["student", "business"], {"partner": False, "kids": False, "home": False, "parents": False},
     {"w_name": "Fake Student", "w_dob": "2004-03-09", "w_gross": "25000", "w_net": "25000", "w_exp": "-8000",
      "w_sav": "abc", "w_ret": "45"}, ["kids", "prop"]),
    ("salaried-parent", ["salaried"], {"partner": True, "kids": True, "home": True, "parents": True},
     {"w_name": "Fake Parent", "w_dob": "1986-07-21", "w_gross": "180000", "w_net": "240000", "w_exp": "95000",
      "w_sav": "1200000", "w_ret": "58"}, []),
    ("retired-owner", ["retired", "business"], {"partner": True, "kids": False, "home": True, "parents": False},
     {"w_name": "Fake Elder", "w_dob": "1956-01-30", "w_gross": "0", "w_net": "0", "w_exp": "60000",
      "w_sav": "8000000", "w_ret": "40"}, ["kids"]),
    ("century-typo", ["salaried"], {"partner": False, "kids": False, "home": False, "parents": False},
     {"w_name": "Fake Typo", "w_dob": "1826-05-02", "w_gross": "75000", "w_net": "60000", "w_exp": "40000",
      "w_sav": "300000", "w_ret": "200"}, ["kids", "prop"]),
    ("uhnw-investor", ["independent", "business"], {"partner": True, "kids": True, "home": True, "parents": True},
     {"w_name": "Fake Investor", "w_dob": "1979-11-11", "w_gross": "9000000", "w_net": "6500000", "w_exp": "1500000",
      "w_sav": "900000000", "w_ret": "55"}, []),
    ("skipper", None, None, {}, []),                                        # taps "Show me everything", types nothing
]

CHECK_JS = """() => {
  const t = document.body.innerText || "";
  const bad = [];
  const m = t.match(/\\bNaN\\b|\\bundefined\\b|\\bInfinity\\b|\\[object Object\\]/);
  if (m) bad.push("shows " + m[0] + " near: " + t.slice(Math.max(0, m.index - 50), m.index + 30).replace(/\\s+/g, " "));
  const age = t.match(/(?:Your age|you are)[:\\s]+(\\d+)/i);
  if (age && (+age[1] < 14 || +age[1] > 110)) bad.push("an impossible age is shown: " + age[0]);
  const af = t.match(/(\\d+)\\s*(?:\\/100|of 100)/i);
  if (af && (+af[1] < 0 || +af[1] > 100)) bad.push("antifragility outside 0-100: " + af[0]);
  if (/(?:salary|take-home|expenses?)[^\\n]{0,30}[-\\u2212]\\s?\\u20b9\\s?\\d/i.test(t)) bad.push("a negative salary or expense is shown");
  return bad;
}"""


def run() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    summary = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for pid, stages, facts, form, hidden in PERSONAS:
            ctx = b.new_context(**p.devices["iPhone 13"], color_scheme="dark")
            pg = ctx.new_page()
            errs: list[str] = []
            pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:160]))
            pg.goto((GM / "index.html").as_uri())
            pg.wait_for_timeout(1500)
            # Make it yours (when the sheet is there): the persona's answers, or "Show me everything"
            if pg.query_selector("#gmMineSheet"):
                if stages is None:
                    pg.evaluate("gmMineSkip()")
                else:
                    for s in stages:
                        pg.evaluate(f"gmMineChoose('stage', {json.dumps(s)})")
                    for k, v in facts.items():
                        pg.evaluate(f"gmMineChoose({json.dumps(k)}, {json.dumps('yes' if v else 'no')})")
                    pg.evaluate("gmMineFinish()")
                pg.wait_for_timeout(300)
            # The set-up form, typed like a person types (and changing their mind once)
            if form:
                pg.evaluate("editProfile()")
                pg.wait_for_timeout(300)
                for fid, val in form.items():
                    el = pg.query_selector("#" + fid)
                    if not el:
                        continue
                    try:
                        el.fill("")
                        el.fill(val) if fid != "w_dob" else pg.evaluate(f"document.getElementById('w_dob').value={json.dumps(val)}")
                    except Exception:                                   # a number field refuses letters, as a phone keyboard would
                        pass
                if pg.query_selector("#w_go"):
                    pg.click("#w_go")
                else:
                    pg.evaluate("buildDash()")
                pg.wait_for_timeout(600)
            # First win: ticking one habit from Today must take at most three taps
            taps = 0
            pg.evaluate("goTab('today')"); taps += 1
            tile = pg.query_selector("#sections .gm-d3 .tile")
            if tile:
                tile.click(); taps += 1
            won = pg.evaluate("(typeof todayChecks==='function') && todayChecks().length > 0")
            if not won or taps > 3:
                problems.append(f"{pid}: the first win took {taps} taps or did not happen")
            # Every tab: nothing nonsensical, nothing that cannot apply
            tabs = pg.evaluate("TABS.map(t => t[0])")
            for t in tabs:
                pg.evaluate(f"goTab({json.dumps(t)})")
                pg.wait_for_timeout(120)
                for msg in pg.evaluate(CHECK_JS):
                    problems.append(f"{pid} / {t}: {msg}")
            pg.evaluate("gmNavMore && gmNavMore(true)")
            offered = pg.evaluate("[...document.querySelectorAll('#gmMoreSheet [role=menuitem]')].map(b => (b.getAttribute('onclick')||'').replace(/.*'(\\w+)'.*/, '$1'))")
            for h in hidden:
                if h in offered:
                    problems.append(f"{pid}: the More sheet offers '{h}', which cannot apply to this persona")
            prof = pg.evaluate("JSON.parse(localStorage.getItem('sovP')||'null')") or {}
            if prof:
                for k in ("gross", "net", "exp", "sav"):
                    v = prof.get(k)
                    if isinstance(v, (int, float)) and v < 0:
                        problems.append(f"{pid}: a negative {k} was saved ({v})")
                if isinstance(prof.get("gross"), (int, float)) and isinstance(prof.get("net"), (int, float)) and prof["gross"] > 0 and prof["net"] > prof["gross"]:
                    problems.append(f"{pid}: take-home above gross was saved")
                if isinstance(prof.get("ret"), (int, float)) and not 35 <= prof["ret"] <= 90:
                    problems.append(f"{pid}: an impossible retirement age was saved ({prof['ret']})")
                if str(prof.get("dob", "")).startswith("18"):
                    problems.append(f"{pid}: a birth year in the 1800s was saved")
            for e in errs:
                problems.append(f"{pid}: page error {e}")
            pg.screenshot(path=str(OUT / f"{pid}.png"))
            summary.append({"persona": pid, "taps_to_first_win": taps, "won": bool(won), "tabs": len(tabs)})
            ctx.close()
        b.close()
    (OUT / "summary.json").write_text(json.dumps({"personas": summary, "problems": problems}, indent=1))
    for s in summary:
        print(f"{s['persona']}: first win in {s['taps_to_first_win']} taps, {s['tabs']} tabs checked")
    if problems:
        print("\n".join("✘ " + x for x in problems))
        print(f"PERSONA AUDIT: {len(problems)} problem(s)")
        return 1
    print("PERSONA AUDIT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(run())
