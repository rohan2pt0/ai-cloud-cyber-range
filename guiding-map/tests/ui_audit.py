"""UI AUDIT — use the Guiding Map as a person would, in a real browser, with realistic data, and measure what they would hit.

Quick setup, 30 days of check-ins, the quarterly check-in (wheel taps, goals, progress taps), the calendar file, adding a child,
integrations, an old Undo, pausing; then EVERY tab in dark and light mode: page errors, and WCAG AA contrast of every visible text.
Exit 0 only when every check passes, there is no page error and no text is below its contrast minimum.

    python3 guiding-map/tests/ui_audit.py [OUT_DIR]       (needs playwright + chromium; the sandbox journey runs it)
"""
import collections
import json
import pathlib
import random
import sys

from playwright.sync_api import sync_playwright

_pre = sorted(pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux*/chrome")) if pathlib.Path("/opt/pw-browsers").is_dir() else []
exe = str(_pre[0]) if _pre else None          # CI: playwright's own chromium
GM = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/gm-ui-audit")
CONTRAST_JS = r"""() => {
  function rgba(s){ const m=s.match(/rgba?\(([^)]+)\)/); if(!m) return null; const p=m[1].split(',').map(x=>parseFloat(x)); return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}; }
  function lum(c){ const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)}; return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b); }
  function blend(top,bot){ const a=top.a; return {r:top.r*a+bot.r*(1-a),g:top.g*a+bot.g*(1-a),b:top.b*a+bot.b*(1-a),a:1}; }
  function bgOf(el){ const stack=[]; let e=el; while(e && e.nodeType===1){ const cs=getComputedStyle(e); const c=rgba(cs.backgroundColor); if(cs.backgroundImage && cs.backgroundImage!=='none' && cs.backgroundImage.includes('gradient')){ const m=cs.backgroundImage.match(/rgba?\([^)]+\)|#[0-9a-f]{6}/i); if(m){ let g=m[0]; if(g[0]==='#'){g='rgb('+parseInt(g.slice(1,3),16)+','+parseInt(g.slice(3,5),16)+','+parseInt(g.slice(5,7),16)+')';} stack.push(rgba(g)); break; } } if(c && c.a>0){ stack.push(c); if(c.a>=0.99) break; } e=e.parentElement; }
    let base={r:255,g:255,b:255,a:1}; const bodyBg=rgba(getComputedStyle(document.body).backgroundColor); if(bodyBg&&bodyBg.a>0) base=bodyBg;
    for(let i=stack.length-1;i>=0;i--) base=blend(stack[i],base); return base; }
  const out=[]; const seen=new Set();
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let n; while((n=walker.nextNode())){ const t=n.textContent.trim(); if(t.length<2) continue; const el=n.parentElement; if(!el||!el.offsetParent) continue;
    const r=el.getBoundingClientRect(); if(r.width<2||r.height<2) continue; if(seen.has(el)) continue; seen.add(el);
    const cs=getComputedStyle(el); if(cs.visibility==='hidden'||parseFloat(cs.opacity)<0.2) continue;
    let fg=rgba(cs.color); if(!fg) continue; const bg=bgOf(el); fg=blend(fg,bg);
    const L1=lum(fg),L2=lum(bg); const ratio=(Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
    const size=parseFloat(cs.fontSize), bold=parseInt(cs.fontWeight)>=700; const need=(size>=24||(size>=18.66&&bold))?3:4.5;
    if(ratio<need) out.push({t:t.slice(0,60),ratio:Math.round(ratio*100)/100,need,fg:cs.color,bg:'rgb('+Math.round(bg.r)+','+Math.round(bg.g)+','+Math.round(bg.b)+')',cls:el.className&&String(el.className).slice(0,40),style:(el.getAttribute('style')||'').slice(0,80)});
  }
  return out; }"""
def seed(pg):
    random.seed(7)
    pg.evaluate("""() => { const S=window.S; const habits=HABITS.map(h=>h.id); const p={ex:.75,mf:.55,fm:.8,sl:.5,rd:.45};
      for(let i=1;i<=30;i++){ const d=new Date(); d.setDate(d.getDate()-i); const k=dKey(d); S.daily[k]=habits.filter(h=>Math.random()<(p[h]||.5)); }
      store('sovS',S);
      const e={},n={}; for(let i=0;i<14;i++){ const d=new Date(); d.setDate(d.getDate()-i); e[dKey(d)]=1+Math.floor(Math.random()*5); }
      n[dKey(new Date(Date.now()-86400000))]='slept late, skipped reading; good walk with family';
      localStorage.setItem('gm_energy',JSON.stringify(e)); localStorage.setItem('gm_notes',JSON.stringify(n)); }""")
def main():
    report = {"errors": [], "contrast": collections.defaultdict(list), "checks": []}
    def chk(name, cond, detail=""): report["checks"].append((name, bool(cond), str(detail)[:200]))
    with sync_playwright() as p:
        OUT.mkdir(parents=True, exist_ok=True)
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        ctx = b.new_context(viewport={"width": 412, "height": 900}, accept_downloads=True)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: report["errors"].append(str(e)))
        pg.on("console", lambda m: m.type == "error" and report["errors"].append("console: " + m.text))
        pg.goto((GM / "index.html").as_uri()); pg.wait_for_timeout(1200)
        # 1. quick setup with realistic numbers
        pg.evaluate("gmQuickSetup()")
        for v in ["37", "220000", "120000", "4500000"]:
            pg.fill("#gmQin", v); pg.click("#gmQok"); pg.wait_for_timeout(120)
        seed(pg); pg.reload(); pg.wait_for_timeout(1000)
        # life map fields a user would type, one in rupees by mistake (the runway bug)
        pg.evaluate("gmLifeSet('fFixed','80000'); gmLifeSet('ef','400000'); gmLifeSet('fSip','30000'); gmLifeSet('fEF','10000')")
        v = pg.evaluate("[...document.querySelectorAll('#gmVitals > div')].map(d=>d.innerText.replace(/\\n/g,' '))")
        chk("runway is sane when the emergency fund is typed in rupees", any("5.0m" in x for x in v), v)
        # 2. quarterly check-in: wheel 8 taps -> pick 2 goals
        pg.evaluate("gmQuarter()"); pg.wait_for_timeout(150)
        for score in [6, 4, 5, 7, 6, 5, 3, 6]:
            pg.click(f"#gmOverlay [data-v='{score}']"); pg.wait_for_timeout(80)
        sug = pg.evaluate("[...document.querySelectorAll('#gmOverlay [data-i]')].map(e=>e.innerText)")
        chk("goal suggestions come from the lowest wheel scores", sug and "joy" in sug[0].lower(), sug[:2])
        pg.click("#gmOverlay [data-i='0']"); pg.click("#gmOverlay [data-i='1']"); pg.click("#gmQfin"); pg.wait_for_timeout(200)
        okrs = pg.evaluate("S.okrs.map(o=>o.o+' ('+o.krs.length+')')")
        chk("two goals with two results each are saved", len(okrs) == 2 and all("(2)" in o for o in okrs), okrs)
        pg.evaluate("gmClose()")
        # grade later with taps
        pg.evaluate("gmQuarter({gradeOnly:true})"); pg.wait_for_timeout(100)
        for g in ["0.5", "0.25", "0.75", "1"]:
            pg.click(f"#gmOverlay [data-v='{g}']"); pg.wait_for_timeout(80)
        chk("progress is updated with one tap per result", pg.evaluate("S.okrs[0].krs[0].v===0.5 && S.okrs[1].krs[1].v===1"), pg.evaluate("JSON.stringify(S.okrs)"))
        # 3. calendar file
        with pg.expect_download() as d:
            pg.evaluate("gmCalendar()")
        ics = pathlib.Path(d.value.path()).read_bytes().decode()
        chk("calendar file has 5 repeating events with reminders", ics.count("BEGIN:VEVENT") == 5 and ics.count("RRULE:") == 5 and ics.count("TRIGGER:-PT30M") == 5, ics[:120])
        chk("calendar file lines are folded to 75 octets and CRLF", all(len(x.encode()) <= 75 for x in ics.split("\r\n")) and "\r\n" in ics)
        (OUT / "life-os-rhythm.ics").write_text(ics)
        # 4. kids quick add
        pg.evaluate("goTab('kids')"); pg.wait_for_timeout(200)
        pg.fill("#gmKidN", "Aarav"); pg.fill("#gmKidD", "2021-06-14"); pg.click("button[onclick=\"gmKidAdd()\"]"); pg.wait_for_timeout(300); print("kids", pg.evaluate("JSON.stringify(P.kids)"))
        chk("a child is added from the Kids tab and the plan appears", "Aarav" in pg.inner_text("#sections"), pg.inner_text("#sections")[:150])
        # 5. integrations: honest labels, numbers pasted
        pg.evaluate("goTab('growth')"); pg.wait_for_timeout(200)
        g = pg.inner_text("#sections")
        chk("integrations say they are copy-in boxes, not live connections", "not live connections" in g and "Auto-fills" not in g)
        # 6. undo safety
        pg.evaluate("localStorage.setItem('gm_undo', JSON.stringify({at: Date.now()-10*86400000, label:'old change', data:{}}))")
        pg.evaluate("goTab('ops')"); pg.wait_for_timeout(200)
        chk("a 10-day-old undo is never offered", "old change" not in pg.inner_text("#sections"))
        before = pg.evaluate("Object.keys(S.daily).length")
        pg.evaluate("gmUndo()"); pg.wait_for_timeout(200)
        chk("…and calling it does not wipe data", pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('sovS')).daily).length") == before)
        # 7. recovery asks first
        pg.evaluate("gmRecoveryAsk(7)"); pg.wait_for_timeout(100)
        chk("pausing rituals asks before it acts", pg.locator("#gmOverlay").count() == 1 and not pg.evaluate("!!localStorage.getItem('gm_recovery')"))
        pg.evaluate("gmClose()")
        # 8. due now shows AAR at month end (simulate date via ritual window directly)
        chk("the After-Action Review is a monthly ritual", "Monthly After-Action Review" in pg.inner_text("#sections") or "Monthly After-Action Review" in pg.evaluate("document.getElementById('sections').textContent"))
        # 9. every tab in dark and light: errors + contrast
        tabs = pg.evaluate("TABS.map(t=>t[0])")
        pg.evaluate("gmCalmMore()")
        for theme in ["dark", "light"]:
            pg.evaluate(f"S.theme='{theme}'; store('sovS',S); applyTheme(); renderAll()")
            for t in tabs:
                pg.evaluate(f"goTab('{t}')"); pg.wait_for_timeout(150)
                if t == "ops":
                    pg.evaluate("document.querySelectorAll('#sections details').forEach(d=>d.open=true)")
                for item in pg.evaluate(CONTRAST_JS):
                    report["contrast"][f"{theme}:{t}"].append(item)
                if t in ("today", "okr", "wheel", "ops", "kids", "growth"):
                    pg.screenshot(path=str(OUT / f"{theme}-{t}.png"), full_page=True)
        b.close()
    # Probes to the estate (health, feed) are expected to fail from a file:// page: refused when nothing listens, CORS-blocked
    # when the estate IS running (the sandbox runner). Those are the environment, not the app; uncaught exceptions stay fatal.
    noise = ("ERR_CONNECTION_REFUSED", "ERR_NAME_NOT_RESOLVED", "Failed to load resource: net::ERR_FAILED")
    errs = [x for x in report["errors"] if not any(n in x for n in noise)
            and not (x.startswith("console: Access to fetch at 'http://localhost") and "blocked by CORS policy" in x)]
    print(json.dumps({"errors": errs[:20], "checks": report["checks"]}, indent=1))
    tot = sum(len(v) for v in report["contrast"].values())
    print("contrast failures:", tot)
    agg = collections.Counter()
    for k, v in report["contrast"].items():
        for i in v: agg[(k.split(":")[0], i["fg"], i["bg"], i["style"][:50] or i["cls"])] += 1
    for (th, fg, bg, st), c in agg.most_common(40): print(c, th, fg, "on", bg, "|", st)
    json.dump({k: v for k, v in report["contrast"].items()}, open(OUT / "contrast.json", "w"), indent=1)
    failed = [c for c in report["checks"] if not c[1]]
    summary = {"checks": len(report["checks"]), "failed": [c[0] for c in failed], "page_errors": errs, "contrast_failures": tot}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    return 0 if not failed and not errs and not tot else 1
if __name__ == "__main__":
    sys.exit(main())
