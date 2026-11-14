"""Robustness and security audit of the Life OS (test campaign 2026-11-14, risk-based per ISTQB: the app holds a person's most
private data and is used daily, so its failures cost most).

Usage: python3 guiding-map/tests/robustness_audit.py [OUTDIR]     exit 1 on any finding

Rounds:
  A. Stored XSS: every text value the app keeps (a restored backup or a sync peer can set any of them) is replaced by an
     attack string; every screen is then drawn in both themes. Nothing may run, and no attack element may appear.
  B. Corrupted storage: each key in turn is set to broken JSON, the wrong type, or an empty object; the app must still
     open, draw every screen, and raise no page error (a damaged key must never brick a person's life record).
  C. The lock as a state machine: a damaged lock record must not lock the person out for ever; while locked, the keyboard
     reaches only the lock's own controls; nothing personal is in the accessibility tree.
"""
import importlib.util
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

GM = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/gm-robustness")
_s = importlib.util.spec_from_file_location("gm_ui_audit_for_robustness", GM / "tests" / "ui_audit.py")
UA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(UA)

TRAP = "window.__x=function(n){(window.__hits=window.__hits||[]).push(n)};"
DRAW_ALL = """() => { const ids=[...document.querySelectorAll('.section')].map(s=>s.id).filter(Boolean); const bad=[];
  for (const th of ['dark','light']) { document.documentElement.setAttribute('data-theme', th);
    for (const id of ids) { try { goTab(id); } catch (e) { bad.push(id+': '+e.message); } } }
  try { goTab('today'); } catch (e) {} return {ids: ids.length, bad}; }"""


def boot(b, init=""):
    ctx = b.new_context(viewport={"width": 412, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.add_init_script(TRAP + init)
    return ctx, pg, errs


def realistic(b):
    """A lived-in app: setup, thirty days of check-ins, money facts, a quarter's goals (the UI audit's own seed)."""
    ctx, pg, errs = boot(b)
    pg.goto((GM / "index.html").as_uri()); pg.wait_for_timeout(1200)
    UA.seed(pg)
    for js in ("gmQuickSetup()", "gmLifeSet('fFixed','80000'); gmLifeSet('ef','400000'); gmLifeSet('fSip','30000')",
               "gmQuarter()", "gmClose()"):
        try:
            pg.evaluate(js); pg.wait_for_timeout(150)
        except Exception:
            pass
    data = pg.evaluate("Object.fromEntries(Object.keys(localStorage).map(k=>[k,localStorage.getItem(k)]))")
    ctx.close()
    return data


def poison(value, n, where):
    """Every string leaf becomes an attack string that calls __x(n); n maps back to the key and path."""
    if isinstance(value, str):
        where.append(None)
        i = len(where) - 1
        return f"Zq\"'><img src=x onerror=__x({i})><svg onload=__x({i})>" if i % 3 else f"javascript:__x({i})"
    if isinstance(value, list):
        return [poison(v, n, where) for v in value]
    if isinstance(value, dict):
        return {k: poison(v, n, where) for k, v in value.items()}
    return value


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    findings = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        data = realistic(b)
        keys = sorted(k for k in data if k != "gm_lock")
        print(f"seeded {len(keys)} storage keys")

        # A. stored XSS through every text value
        where, plan = [], {}
        for k in keys:
            try:
                v = json.loads(data[k])
            except Exception:
                v = data[k]
            start = len(where)
            pv = poison(v, 0, where)
            plan[k] = json.dumps(pv) if not isinstance(v, str) or data[k].startswith('"') else pv
            for i in range(start, len(where)):
                where[i] = k
        # One key at a time, so a hang or a hit names its key; the rest of the store stays realistic.
        drawn = 0
        for k in keys:
            ctx, pg, errs = boot(b, "const D=" + json.dumps(data) + ";for(const k in D)localStorage.setItem(k,D[k]);"
                                 + f"localStorage.setItem({json.dumps(k)},{json.dumps(plan[k])});")
            try:
                pg.goto((GM / "index.html").as_uri(), timeout=12000); pg.wait_for_timeout(700)
                pg.evaluate(DRAW_ALL); drawn += 1
            except Exception as e:
                findings.append(f"A '{k}' with attack text: the app hangs or fails to open ({str(e).splitlines()[0][:90]})")
                ctx.close(); continue
            hits = pg.evaluate("window.__hits||[]")
            live = pg.evaluate("document.querySelectorAll('img[src=x][onerror],svg[onload]').length")
            js_links = pg.evaluate("[...document.querySelectorAll('a[href]')].filter(a=>/^\\s*javascript:/i.test(a.getAttribute('href'))).length")
            if hits:
                findings.append(f"A stored XSS: a value in '{k}' ran as code")
            if live:
                findings.append(f"A stored XSS: '{k}' put {live} attack element(s) into the page")
            if js_links:
                findings.append(f"A stored XSS: '{k}' made {js_links} link(s) with a javascript: address")
            if errs:
                findings.append(f"A '{k}' with attack text: page error {errs[0]}")
            ctx.close()
        print(f"A: {len(where)} text values poisoned across {len(keys)} keys; {drawn} keys drew every screen in both themes")

        # B. corrupted storage, one key at a time
        bad_values = ["{broken", "[]", "{}", "42", "null"]
        for k in keys:
            for bv in bad_values:
                ctx, pg, errs = boot(b, "const D=" + json.dumps(data) + ";for(const k in D)localStorage.setItem(k,D[k]);"
                                     + f"localStorage.setItem({json.dumps(k)},{json.dumps(bv)});")
                pg.goto((GM / "index.html").as_uri()); pg.wait_for_timeout(500)
                try:
                    r = pg.evaluate(DRAW_ALL)
                    alive = pg.evaluate("!!document.querySelector('#sections') && document.body.innerText.length > 200")
                except Exception as e:
                    r, alive = {"bad": [str(e)[:120]]}, False
                if errs or r["bad"] or not alive:
                    findings.append(f"B '{k}' = {bv}: " + ("; ".join((errs + r["bad"])[:2]) or "the app did not open"))
                ctx.close()
        print(f"B: {len(keys)} keys x {len(bad_values)} corruptions tried")

        # C. the lock
        for bad in ['{}', '{"id":"x"}', '{"broken', '{"salt":"","hash":""}']:
            ctx, pg, errs = boot(b, f"localStorage.setItem('gm_lock',{json.dumps(bad)});")
            pg.goto((GM / "index.html").as_uri()); pg.wait_for_timeout(700)
            locked = pg.evaluate("document.documentElement.classList.contains('gm-locked')")
            if locked and bad.startswith("{") and not bad.startswith('{"broken'):
                # A record that can never be satisfied must not be a life sentence: there must be a way back in.
                can = pg.evaluate("""async()=>{ try { const r=JSON.parse(localStorage.getItem('gm_lock')); return !!(r && r.id && r.salt && r.hash); } catch(e){ return false; } }""")
                if not can:
                    findings.append(f"C a damaged lock record {bad} locks the person out with no way in (no credential, no usable code)")
            if errs:
                findings.append(f"C lock record {bad}: page error {errs[0]}")
            ctx.close()
        ctx, pg, errs = boot(b, "localStorage.setItem('gm_lock','{\"id\":\"x\",\"salt\":\"eA\",\"hash\":\"y\",\"idle\":5}');")
        pg.goto((GM / "index.html").as_uri()); pg.wait_for_timeout(800)
        start = pg.evaluate("(document.activeElement.textContent||'').trim()")
        if start != "Unlock":
            findings.append(f"C the lock opens with the focus on '{start[:20]}', not on Unlock (one Enter should open it)")
        outside = []
        for _ in range(25):
            pg.keyboard.press("Tab")
            o = pg.evaluate("(()=>{const a=document.activeElement; return a && a!==document.body && !a.closest('#gmLock') ? (a.id||a.tagName)+':'+(a.textContent||'').trim().slice(0,20) : ''})()")
            if o:
                outside.append(o)
        if outside:
            findings.append(f"C while locked, the keyboard reaches {len(set(outside))} control(s) behind the lock, e.g. {outside[0]}")
        snap = pg.accessibility.snapshot() if hasattr(pg, "accessibility") else None
        txt = json.dumps(snap or {})
        if "Saving" in txt or "Net worth" in txt:
            findings.append("C while locked, personal figures are in the accessibility tree")
        ctx.close()
        b.close()
    (OUT / "findings.json").write_text(json.dumps(findings, indent=1))
    for f in findings[:60]:
        print("✘ " + f)
    print(f"ROBUSTNESS AUDIT: {'PASS' if not findings else 'FAIL'} ({len(findings)} findings)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
