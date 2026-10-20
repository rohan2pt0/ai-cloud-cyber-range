#!/usr/bin/env python3
"""Run SecuRAX on several machines at once, all with the same Life OS data, so no single machine is needed (doc 86).

    ./securax nodes                     this node, the nodes it syncs with, and how the last round with each went
    ./securax nodes invite              the one line to run on ANOTHER machine so it joins this one
    ./securax nodes add URL TOKEN [--pull-only]
                                        sync with another node (its /sync address and one of its tokens; --pull-only for a beta node:
                                        it takes from that node and never sends back)
    ./securax nodes remove URL          stop syncing with it (both keep their data)

A node is any machine running the estate: this laptop, a VPS, a Mac mini, a cloud or private-cloud instance. Nodes reach each other
privately over Tailscale (doc 58), through the same address the phones use, so nothing new is opened to the internet. Every node
holds every person's data; the merge gives the same result in any order, so there is no primary to lose. Settings go to
local/compose/.env (mode 600). Standard library only. Exit codes: 0 done, 1 the other node did not answer, 2 bad usage.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

import online
import synclink

HUB = "http://127.0.0.1:8088/sync"           # this node's own sync service, through the Life OS front door


def peers() -> list[list[str]]:
    return [x.split("|") for x in online.env_get("SYNC_PEERS").split(",") if x.strip()]


def save(items: list[list[str]]) -> None:
    online.env_set({"SYNC_PEERS": ",".join("|".join(i) for i in items)})


def token() -> str:
    return next((t.strip() for t in online.env_get("SYNC_TOKENS").split(",") if t.strip()), "")


def get(url: str, tok: str, timeout: float = 10):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:            # noqa: S310 (an address the person gave)
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (OSError, ValueError):
        return 0, None


def main(argv: list[str] | None = None, say=print, fetch=get) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "status"
    if cmd == "status":
        st, me = fetch(f"{HUB}/peers", token())
        items = peers()
        say(f"This node: {(me or {}).get('node') or online.env_get('SYNC_NODE_NAME') or 'this machine'}"
            + ("" if st == 200 else "  (its sync service is not running: ./securax up)"))
        if not items:
            say("It syncs with no other node yet. To add one, run this on the OTHER machine's estate:  ./securax nodes invite")
            say("then paste the line it prints here.")
            return 0
        last = {p["url"]: p for p in (me or {}).get("peers", [])}
        for url, *rest in items:
            p, mode = last.get(url, {}), (" · pull only (beta)" if rest[1:2] == ["pull"] else "")
            state = ("✔ in step" if p.get("ok") else "✗ " + p.get("error", "")) if p else "· not tried yet"
            say(f"  {state:<40} {url}{mode}" + (f"   (last {p['at']}, pulled {p['pulled']}, sent {p['pushed']})" if p.get("ok") else ""))
        return 0 if all(last.get(u, {}).get("ok") for u, *_ in items) else 1
    if cmd == "invite":
        name, tok = synclink.tailscale_name(), token()
        if not tok:
            say("This node has no sync token yet: run  ./securax up  once, then this again.")
            return 2
        if not name:
            say("This node has no private address yet, so other nodes cannot reach it. Install Tailscale here (doc 58: ./securax phones),")
            say("then run this again. Every node of yours joins the same Tailscale account.")
            return 2
        say("On the other machine's estate, run (it keeps the token private: it goes into that machine's .env only):\n")
        say(f"  ./securax nodes add https://{name}/sync {tok}\n")
        say("Then run the same invite THERE and add it HERE, so the two sync both ways.")
        return 0
    if cmd == "add" and len(argv) >= 3:
        url, tok, pull = argv[1].rstrip("/"), argv[2], "--pull-only" in argv[3:]
        if not url.startswith(("https://", "http://")) or not url.endswith("/sync"):
            say("The address is the other node's /sync address, e.g. https://vps.tail1234.ts.net/sync (its invite prints it).")
            return 2
        st, users = fetch(f"{url}/users", tok)
        if st != 200:
            say(f"✗ {url} did not accept that token (HTTP {st or 'no answer'}). Is the other estate up, and on Tailscale? "
                "Run its  ./securax nodes invite  again and paste that exact line.")
            return 1
        items = [i for i in peers() if i[0] != url] + [[url, tok] + (["pull"] if pull else [])]
        save(items)
        say(f"✔ syncing with {url}" + (" (pull only: this node takes from it and never sends)" if pull else "")
            + f"; it holds {len(users or [])} person(s)' data. Restarting the sync service…")
        return 0
    if cmd == "remove" and len(argv) == 2:
        url = argv[1].rstrip("/")
        left = [i for i in peers() if i[0] != url]
        if len(left) == len(peers()):
            say(f"{url} is not a node this one syncs with (./securax nodes).")
            return 2
        save(left)
        say(f"✔ stopped syncing with {url}; both keep the data they have. Restarting the sync service…")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
