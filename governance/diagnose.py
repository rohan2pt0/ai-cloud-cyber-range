"""Names, certificates and the site, diagnosed on one folded cockpit panel (doc 99): are addresses names, is the
certificate current, do the names resolve on this machine, and does the public site answer at your domain yet.
Each row says what is wrong and the one command that fixes it. Offline and fast: it reads files and asks this
machine's resolver, nothing else.

    python3 governance/diagnose.py          the same rows as text
"""
from __future__ import annotations

import html
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
E = html.escape


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)      # by path (LESSONS: names collide in sys.modules)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def checks(tls=None, vals: dict | None = None) -> list[dict]:
    """Rows of {what, ok (True, False, or None for 'nothing to fix, just know'), detail, cmd}."""
    tls = tls or _load("securax_tls_diag", "governance/tls.py")
    vals = vals if vals is not None else _load("securax_config_diag", "governance/config.py").values()
    rows = []
    on = tls.tls_is_on()
    dom = tls.domain()
    rows.append({"what": "Addresses are names", "ok": on,
                 "detail": f"https://hub.{dom} and the others" if on else "the estate still shows port numbers",
                 "cmd": "" if on else "./securax names"})
    if on:
        days = (tls.cert_info(tls.tls_dir() / "server.crt") or {}).get("days_left")
        rows.append({"what": "Certificate is current", "ok": None if days is None else days >= 30,
                     "detail": "no certificate found" if days is None else f"{days} days left",
                     "cmd": "./securax tls renew" if days is None or days < 30 else ""})
        hub = tls.host_of("hub", dom)
        res = tls.resolves(hub)
        rows.append({"what": "Names resolve on this machine", "ok": res is not None,
                     "detail": f"{hub} → {res}" if res else f"{hub} does not resolve: add a DNS record or a hosts-file line",
                     "cmd": "" if res else "./securax tls status"})
        rows.append({"what": "Each device trusts the estate", "ok": None,
                     "detail": "a browser warning on a device means it does not trust your authority yet",
                     "cmd": "./securax tls trust --apply"})
    sd = (vals.get("SITE_DOMAIN") or "").strip()
    live = (vals.get("SITE_LIVE") or "").strip().lower() in ("yes", "true", "1")
    url = vals.get("SITE_URL") or ""
    if sd and not live:
        rows.append({"what": "Public site at your domain", "ok": None,
                     "detail": f"answers at {url or 'GitHub Pages'}; {sd} is set but not live yet", "cmd": "./securax site live"})
    else:
        rows.append({"what": "Public site answers", "ok": bool(url), "detail": url or "no site address set", "cmd": "" if url else "./securax site"})
    return rows


def summary(rows: list[dict]) -> str:
    bad = sum(r["ok"] is False for r in rows)
    good = sum(r["ok"] is True for r in rows)
    return f"{good} fine" + (f" · {bad} to fix" if bad else "") + (f" · {len(rows) - good - bad} to know" if len(rows) - good - bad else "")


def html_card(rows: list[dict] | None = None) -> str:
    rows = checks() if rows is None else rows
    mark = {True: ("OK", "green"), False: ("Fix", "red"), None: ("Note", "unknown")}
    body = "".join(
        f"<tr><td><span class='dot {mark[r['ok']][1]}'>{mark[r['ok']][0]}</span></td><td><b>{E(r['what'])}</b><div class='muted'>{E(r['detail'])}</div></td>"
        f"<td>{'<code>' + E(r['cmd']) + '</code>' if r['cmd'] else ''}</td></tr>" for r in rows)
    return (f"<details class='card panel' id='names'><summary><b>Names and site</b> <span class='muted'>· {E(summary(rows))}</span></summary>"
            f"<table class='areas'><tbody>{body}</tbody></table></details>")


if __name__ == "__main__":
    for r in checks():
        print(f"  {'✔' if r['ok'] else ('✘' if r['ok'] is False else '·')} {r['what']:<32} {r['detail']}" + (f"   → {r['cmd']}" if r["cmd"] else ""))
    sys.exit(0)
