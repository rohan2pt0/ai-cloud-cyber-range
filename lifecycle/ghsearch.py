#!/usr/bin/env python3
"""One GitHub search, with a wait and one retry when GitHub answers 403 rate limit (queue github-api-backoff).

    from lifecycle.ghsearch import search
    search("repo:acme/range is:open")                  a code search
    search("repo:acme/range", kind="issues")           any search kind

A busy round's searches hit GitHub's secondary rate limit: a 403 that names a rate limit. One search waits `wait` seconds
(60 by default) and tries once more; a second rate limit raises a clear RuntimeError naming the wait. Any other error is
raised at once, with no retry. The runner and the sleep are injectable, so its test needs no network and no real wait.
"""
from __future__ import annotations

import subprocess
import time


def _output(result) -> str:
    return (getattr(result, "stdout", "") or "") + (getattr(result, "stderr", "") or "")


def _rate_limited(result) -> bool:
    return getattr(result, "returncode", 0) == 403 and "rate limit" in _output(result).lower()


def search(query: str, kind: str = "code", run=subprocess.run, sleep=time.sleep, wait: int = 60) -> str:
    """Run `gh api` for one search and return its output, waiting once and retrying once on a rate limit."""
    cmd = ["gh", "api", "-X", "GET", f"search/{kind}", "-f", f"q={query}"]
    result = run(cmd, capture_output=True, text=True)
    if _rate_limited(result):
        sleep(wait)
        result = run(cmd, capture_output=True, text=True)
        if _rate_limited(result):
            raise RuntimeError(f"GitHub still rate-limited after waiting {wait}s and retrying once: {_output(result).strip()}")
    if getattr(result, "returncode", 0) != 0:
        raise RuntimeError(f"gh search failed ({result.returncode}): {_output(result).strip()}")
    return getattr(result, "stdout", "") or ""
