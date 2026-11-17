"""Synthetic people: three friends with goals in their own words use the Life OS on a 375 px phone, seeing only what a
person sees. Each step reads the controls on screen (their role and visible name), picks the one whose words best match the
goal, then taps, types or scrolls. It writes steps, wrong taps and dead ends for each friend.

    python3 sandbox/synthetic_users.py OUTDIR

It opens guiding-map/index.html from disk with fake seed data and a 375 x 812 phone viewport. Needs Chromium and the
playwright package for the python that runs it; it skips and says so in plain words when one is missing. OUTDIR gets
report.json and summary.md and the command ends with "SYNTHETIC USERS: PASS" or the list of dead ends. Fake data only,
no network, no LLM.
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import os
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent
GOALS = HERE / "goals.json"
INDEX = ROOT / "guiding-map" / "index.html"
VIEWPORT = {"width": 375, "height": 812}
FIELD_ROLES = ("textbox", "searchbox", "spinbutton", "combobox")
STOP = set("a an the and or on in at to of for with by from as is are was were be been it its this that these those "
           "my your his her our their i you he she we they me us them do does did done can could should would will "
           "shall may might must".split())
SELECTOR = ("button, [role=button], [role=menuitem], [role=tab], [role=link], a[href], "
            "input, select, textarea, summary, [onclick]")
META_JS = """(els) => {
  const roleOf = (e, tag) => {
    const r = e.getAttribute('role');
    if (r) return r;
    if (tag === 'button' || tag === 'summary') return 'button';
    if (tag === 'a') return 'link';
    if (tag === 'select') return 'combobox';
    if (tag === 'textarea') return 'textbox';
    if (tag === 'input') {
      const t = (e.type || 'text').toLowerCase();
      if (t === 'checkbox') return 'checkbox';
      if (t === 'radio') return 'radio';
      if (t === 'number') return 'spinbutton';
      if (['text', 'date', 'search', 'email', 'tel', 'url', 'password'].indexOf(t) >= 0) return 'textbox';
      return 'button';
    }
    return e.getAttribute('onclick') ? 'button' : 'generic';
  };
  const nameOf = (e, tag) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    if (tag === 'input' || tag === 'select' || tag === 'textarea') {
      if (e.labels && e.labels[0]) return (e.labels[0].innerText || '').trim();
      const ph = e.getAttribute('placeholder');
      if (ph) return ph.trim();
      return '';
    }
    return (e.innerText || e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 160);
  };
  const out = [];
  els.forEach((e, i) => {
    if (e.id === 'mo' || e.id === 'sections' || e.id === 'gmMoreSheet') return;
    if (e.disabled) return;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return;
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    const tag = e.tagName.toLowerCase();
    const role = roleOf(e, tag);
    const name = nameOf(e, tag);
    if (!name) return;
    const choices = tag === 'select' ? Array.from(e.options).map(o => (o.textContent || '').trim()) : [];
    out.push({i: i, role: role, name: name, choices: choices,
              value: (tag === 'input' || tag === 'textarea' || tag === 'select') ? String(e.value || '') : '',
              checked: !!e.checked});
  });
  return out;
}"""


def chromium_path() -> str:
    env = os.environ.get("PLAYWRIGHT_CHROMIUM", "").strip()
    if env and pathlib.Path(env).exists():
        return env
    local = pathlib.Path("/opt/pw-browsers/chromium")
    return str(local) if local.exists() else ""


def has_playwright() -> bool:
    return importlib.util.find_spec("playwright") is not None


def load_goals(path: pathlib.Path | str = GOALS) -> dict:
    data = json.loads(pathlib.Path(path).read_text())
    return data if isinstance(data, dict) else {}


def _stem(t: str) -> str:
    return t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t


def tokens(text) -> list[str]:
    if isinstance(text, (list, tuple)):
        text = " ".join(str(x) for x in text)
    return [_stem(t) for t in re.findall(r"[a-z0-9]+", str(text).lower())]


def _terms(text) -> set[str]:
    return {t for t in tokens(text) if t not in STOP}


def _seen(control: dict) -> set[str]:
    out = _terms(control.get("name", ""))
    for choice in control.get("choices") or []:
        out.update(_terms(choice))
    return out


def score(goal_words, control: dict) -> int:
    return len(_terms(goal_words) & _seen(control))


def rank(goal_words, controls: list[dict]) -> list[dict]:
    wanted = _terms(goal_words)
    seen = {id(c): _seen(c) for c in controls}
    freq: dict[str, int] = {}
    for terms in seen.values():
        for t in terms:
            freq[t] = freq.get(t, 0) + 1

    def weight(c: dict) -> float:
        return sum(1.0 / freq[t] for t in wanted & seen[id(c)])

    def field_first(c: dict) -> int:
        return 0 if str(c.get("role", "")).lower() in FIELD_ROLES else 1

    ordered = sorted(controls, key=lambda c: (-weight(c), field_first(c), len(str(c.get("name", "")))))
    for c in ordered:
        c["match"] = round(weight(c), 3)
    return ordered


def _day_after(days: int) -> str:
    d = _dt.date.today() + _dt.timedelta(days=days)
    return d.isoformat()


def _value_for(goal: dict, name: str) -> str:
    for label, value in goal.get("inputs") or []:
        if str(label).lower() == str(name).lower():
            v = str(value)
            m = re.match(r"^@today\+(\d+)$", v)
            return _day_after(int(m.group(1))) if m else v
    return ""


def _text_visible(page, text: str) -> bool:
    loc = page.get_by_text(text, exact=False)
    for i in range(min(loc.count(), 25)):
        try:
            if loc.nth(i).is_visible():
                return True
        except Exception:
            pass
    return False


def _button_visible(page, name: str) -> bool:
    loc = page.get_by_role("button", name=name, exact=True)
    for i in range(min(loc.count(), 10)):
        try:
            if loc.nth(i).is_visible():
                return True
        except Exception:
            pass
    return False


def success(page, check: dict) -> bool:
    for name in check.get("all_filled") or []:
        loc = page.get_by_label(name, exact=True)
        if not loc.count() or not str(loc.first.input_value() or "").strip():
            return False
    for text in check.get("visible_all") or []:
        if not _text_visible(page, text):
            return False
    for name in check.get("buttons") or []:
        if not _button_visible(page, name):
            return False
    absent = check.get("absent")
    if absent and _text_visible(page, absent):
        return False
    return True


def controls_on(page) -> list[dict]:
    scope = "#mo.open" if page.locator("#mo.open").count() else "#sections"
    locs = page.locator(scope).locator(SELECTOR)
    total = min(locs.count(), 400)
    meta = locs.evaluate_all(META_JS) if total else []
    out = []
    for item in meta:
        if item["i"] >= total:
            continue
        item["locator"] = locs.nth(item["i"])
        out.append(item)
    return out


def _key(control: dict) -> str:
    return f'{control.get("role")}|{control.get("name")}'


def _open_tab(page, label: str) -> None:
    if label.lower() == "today":
        page.locator("#gmNav").get_by_role("button", name="Today", exact=True).first.tap(timeout=5000)
    else:
        page.locator("#gmNav").get_by_role("button", name="More", exact=True).first.tap(timeout=5000)
        page.wait_for_timeout(200)
        item = page.locator("#gmMoreSheet").get_by_role("menuitem", name=re.compile(re.escape(label), re.I)).first
        item.scroll_into_view_if_needed()
        item.tap(timeout=5000)
    page.wait_for_timeout(350)


def _act(page, goal: dict, control: dict, step: dict) -> None:
    role = str(control.get("role", "")).lower()
    loc = control["locator"]
    name = control.get("name", "")
    loc.scroll_into_view_if_needed(timeout=4000)
    if role == "combobox":
        wanted = (goal.get("select") or {}).get("option") or goal.get("words", "")
        choices = control.get("choices") or []
        pick = max(choices, key=lambda c: score(wanted, {"name": c})) if choices else ""
        loc.select_option(label=pick, timeout=5000)
        step["typed"] = pick
    elif role in ("textbox", "searchbox", "spinbutton"):
        value = _value_for(goal, name)
        loc.fill(value, timeout=5000)
        step["typed"] = value
    elif role == "checkbox":
        if not control.get("checked"):
            loc.tap(timeout=5000)
    else:
        loc.tap(timeout=5000)


def _choose(goal: dict, controls: list[dict], tried: set[str]) -> dict | None:
    matched = [c for c in rank(goal.get("words", ""), controls)
               if c.get("match", 0) > 0 and _key(c) not in tried]
    fields = [c for c in matched if str(c.get("role", "")).lower() in FIELD_ROLES
              and (str(c.get("role", "")).lower() == "combobox" or not c.get("value"))]
    return (fields or matched or [None])[0]


def _wrong(pick: dict, value: float) -> bool:
    return value < 0.5 and str(pick.get("role", "")).lower() not in FIELD_ROLES


def _take(page, goal: dict, pick: dict, n: int, tried: set[str]) -> tuple[dict, str]:
    step = {"n": n, "control": pick.get("name", ""), "role": pick.get("role", ""),
            "score": round(float(pick.get("match", 0)), 3)}
    try:
        _act(page, goal, pick, step)
    except Exception as exc:
        return step, f"step {n}: could not use {pick.get('name', '')}: {str(exc)[:120]}"
    tried.add(_key(pick))
    return step, ""


def play(page, goal: dict) -> dict:
    steps, wrong_taps, dead_ends = [], [], []
    tried = set()
    scrolled = False
    reached = success(page, goal.get("success") or {})
    limit = min(int(goal.get("max_steps") or 15), 15)
    for n in range(1, limit + 1):
        if reached:
            break
        pick = _choose(goal, controls_on(page), tried)
        if pick is None:
            if scrolled:
                dead_ends.append(f"step {n}: no visible control matches the goal")
                break
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(250)
            scrolled = True
            continue
        scrolled = False
        step, error = _take(page, goal, pick, n, tried)
        if _wrong(pick, step["score"]):
            wrong_taps.append(step)
        if error:
            dead_ends.append(error)
            break
        steps.append(step)
        page.wait_for_timeout(250)
        reached = success(page, goal.get("success") or {})
    if not reached and not dead_ends:
        dead_ends.append(f"not reached within {limit} steps")
    return {"steps": steps, "wrong_taps": wrong_taps, "dead_ends": dead_ends, "reached": reached}


def run(outdir: pathlib.Path | str) -> dict:
    from playwright.sync_api import sync_playwright

    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    data = load_goals()
    seed = data.get("seed") or {}
    goals = data.get("goals") or []
    report = {"goals": [], "viewport": VIEWPORT, "started": _dt.datetime.now().isoformat(timespec="seconds")}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path() or None, headless=True)
        try:
            for goal in goals:
                ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2, is_mobile=True, has_touch=True,
                                          color_scheme="dark")
                ctx.add_init_script("const D=" + json.dumps(seed) + ";"
                                    "for (const k in D) localStorage.setItem(k, JSON.stringify(D[k]));")
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e, errs=errors: errs.append(str(e)[:160]))
                started = time.time()
                try:
                    page.goto(INDEX.as_uri())
                    page.locator("#sections").wait_for(state="visible", timeout=15000)
                    page.wait_for_timeout(600)
                    _open_tab(page, str(goal.get("start_tab") or "Today"))
                    result = play(page, goal)
                except Exception as exc:
                    result = {"steps": [], "wrong_taps": [], "dead_ends": [f"could not start: {str(exc)[:160]}"],
                              "reached": False}
                result.update({"id": goal.get("id", ""), "friend": goal.get("friend", ""),
                               "words": goal.get("words", ""), "start_tab": goal.get("start_tab", ""),
                               "seconds": round(time.time() - started, 1), "page_errors": errors})
                report["goals"].append(result)
                ctx.close()
        finally:
            browser.close()
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (out / "summary.md").write_text(summary_md(report))
    return report


def _row(g: dict) -> str:
    return (f"| {g.get('id')} | {'yes' if g.get('reached') else 'no'} | {len(g.get('steps') or [])} | "
            f"{len(g.get('wrong_taps') or [])} | {len(g.get('dead_ends') or [])} |")


def _goal_lines(g: dict) -> list[str]:
    lines = [f"## {g.get('id')}: {g.get('words')}", "", f"- Friend: {g.get('friend')}",
             f"- Start tab: {g.get('start_tab')}",
             f"- Reached: {'yes' if g.get('reached') else 'no'} in {len(g.get('steps') or [])} steps "
             f"({g.get('seconds')}s)"]
    for step in g.get("steps") or []:
        typed = f" -> {step['typed']}" if step.get("typed") else ""
        lines.append(f"  {step['n']}. {step['role']} '{step['control']}'{typed} (match {step['score']})")
    if g.get("wrong_taps"):
        lines.append("- Wrong taps: " + "; ".join(x.get("control", "") for x in g["wrong_taps"]))
    lines += [f"- Dead end: {dead}" for dead in g.get("dead_ends") or []]
    lines += [f"- Page error: {err}" for err in g.get("page_errors") or []]
    return lines + [""]


def summary_md(report: dict) -> str:
    goals = report.get("goals", [])
    lines = ["# Synthetic people", "",
             f"Phone {VIEWPORT['width']} x {VIEWPORT['height']}, three friends, goals in their own words.", "",
             "| goal | reached | steps | wrong taps | dead ends |", "|---|---|---|---|---|"]
    lines += [_row(g) for g in goals]
    lines.append("")
    for g in goals:
        lines += _goal_lines(g)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out" / "synthetic-users"
    if not chromium_path():
        print("SYNTHETIC USERS: SKIP (no Chromium: set PLAYWRIGHT_CHROMIUM or install /opt/pw-browsers/chromium)")
        return 0
    if not has_playwright():
        print("SYNTHETIC USERS: SKIP (no playwright for this python: pip install playwright)")
        return 0
    report = run(out)
    bad = [g for g in report.get("goals", []) if not g.get("reached")]
    for g in report.get("goals", []):
        print(f"{g.get('id')}: {'reached' if g.get('reached') else 'NOT reached'} "
              f"({len(g.get('steps') or [])} steps, {len(g.get('wrong_taps') or [])} wrong taps, "
              f"{len(g.get('dead_ends') or [])} dead ends)")
    if bad:
        for g in bad:
            for dead in g.get("dead_ends") or []:
                print(f"{g.get('id')}: {dead}")
        print("SYNTHETIC USERS: FAIL")
        return 1
    print(f"SYNTHETIC USERS: PASS -> {out / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
