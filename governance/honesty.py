#!/usr/bin/env python3
"""Does the estate's AI answer honestly? A short, repeatable check you can run on your own estate (doc 89).

    ./securax ai honesty                     ask the default chat model the probes below and score each answer
    ./securax ai honesty --model twin        another model
    ./securax ai honesty --json              the same, for the cockpit or a routine

Each probe is a question where a model that guesses gets caught: a false premise, a fact it cannot know, a circular number
that does not exist, today's date, a sum, an exact format, a figure that changes. An answer passes when it shows the honest
behaviour (it rejects the premise, says it does not know, gives the right date or number, keeps the format). The check is
deliberately simple: it looks for words, so read the answers it prints when a probe fails. Run it after changing models or
keys. The probes are in governance/honesty.json. Standard library only. Exit codes: 0 all passed, 1 some failed, 2 no answer.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROBES = ROOT / "governance" / "honesty.json"


def load() -> list[dict]:
    return json.loads(PROBES.read_text("utf-8"))["probes"]


def today_patterns(at: dt.date) -> list[str]:
    return [at.strftime("%d %B").lstrip("0"), at.strftime("%B %d").replace(" 0", " "), at.strftime("%d %B"), at.isoformat(),
            at.strftime("%d/%m/%Y"), at.strftime("%d-%m-%Y")]


def grade(probe: dict, answer: str, at: dt.date | None = None) -> bool:
    a = (answer or "").split("\n\n(Answered by the small offline model")[0].strip()     # the gateway's note is not the answer
    if probe.get("exact") is not None:
        return a.strip(" .\n\"'`*").upper() == probe["exact"].upper()
    if probe.get("today"):
        at = at or (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=330)).date()
        return any(p.lower() in a.lower() for p in today_patterns(at))
    ok = any(re.search(p, a, re.I) for p in probe.get("pass_any", []))
    bad = any(re.search(p, a, re.I) for p in probe.get("fail_any", []))
    return ok and not bad


def ask(url: str, model: str, question: str, key: str = "", timeout: float = 180) -> tuple[int, str]:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": question}]}).encode()
    hdr = {"Content-Type": "application/json", **({"Authorization": f"Bearer {key}"} if key else {})}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=body, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:                       # noqa: S310 (the estate's own gateway)
            d = json.loads(r.read())
            return 200, ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:300]
    except (OSError, ValueError) as exc:
        return 0, str(exc)[:300]


def run(model: str, url: str, key: str = "", asker=ask, at: dt.date | None = None) -> dict:
    rows = []
    for p in load():
        st, ans = asker(url, model, p["q"], key)
        rows.append({"id": p["id"], "kind": p["kind"], "status": st, "passed": st == 200 and grade(p, ans, at),
                     "answer": ans[:400], "why": p["why"]})
    answered = [r for r in rows if r["status"] == 200]
    return {"model": model, "probes": len(rows), "answered": len(answered), "passed": sum(r["passed"] for r in rows), "rows": rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ai honesty", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=os.environ.get("HONESTY_MODEL", "bank-assistant"))
    ap.add_argument("--url", default=os.environ.get("SECURAX_GATEWAY_URL", "http://localhost:8080"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = run(a.model, a.url, os.environ.get("SECURAX_GATEWAY_KEY", ""))
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        print(f"HONESTY CHECK · model {a.model}: does it refuse to guess?\n")
        for r in res["rows"]:
            mark = "✔" if r["passed"] else ("·" if r["status"] != 200 else "✗")
            print(f"  {mark} {r['kind']:<14} {r['why']}")
            if not r["passed"]:
                print("      answer: " + (r["answer"].replace("\n", " ")[:240] or f"(no answer, HTTP {r['status'] or 'none'})"))
        print(f"\n{res['passed']} of {res['probes']} honest." + ("" if res["answered"] else
              "  The gateway did not answer: is the estate up?  ./securax up"))
        if res["answered"] and res["passed"] < res["probes"]:
            print("Read the failed answers above. A small offline model fails most of these: ./securax keys adds a stronger free one.")
    if not res["answered"]:
        return 2
    return 0 if res["passed"] == res["probes"] else 1


if __name__ == "__main__":
    sys.exit(main())
