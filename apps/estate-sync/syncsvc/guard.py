"""Two guards for the sync service (doc 87): a request limit per device token, and an alert after repeated refused sign-ins.

    SYNC_RATE_LIMIT           requests one token (one node or device) may make per window   (default 600: about ten a second, room for a node serving many users)
    SYNC_RATE_WINDOW_S        the sliding window for that limit, in seconds                  (default 60)
    SYNC_REFUSED_ALERT_AT     refused sign-ins from one address that raise an alert          (default 10)
    SYNC_REFUSED_WINDOW_S     the sliding window for that count, in seconds                  (default 900, i.e. 15 minutes)

A token over its limit gets HTTP 429 with Retry-After, and is served again as soon as its oldest request leaves the window. Refused
sign-ins never lock anyone out: they only write ONE alert line per address when it crosses the threshold (again only after it has
fallen back below), and /healthz shows how many addresses are over it right now. Nothing here stores or prints a token: the limiter
keys on a short hash of it, and the alert names only the client address.

Memory is bounded: each tracker keeps at most MAX_KEYS keys (the least recently seen is dropped first) and at most a fixed number of
timestamps per key. The alert file keeps its last ALERT_LINES lines. Standard library only; the clock is injectable for tests.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections import OrderedDict, deque

MAX_KEYS = 1024
ALERT_LINES = 500


def env_int(name: str, default: int) -> int:
    """A positive whole number from the environment; anything else (empty, zero, negative, junk) keeps the safe default."""
    try:
        v = int(os.environ.get(name, "") or default)
    except ValueError:
        return default
    return v if v > 0 else default


def token_key(token: str) -> str:
    """What the limiter remembers instead of the token: a short one-way hash, never the token itself."""
    return "t:" + hashlib.sha256(token.encode("utf-8", "surrogatepass")).hexdigest()[:16]


class RateLimiter:
    """Sliding-window log: at most `limit` hits per `window` seconds per key."""

    def __init__(self, limit: int, window: float, max_keys: int = MAX_KEYS, clock=time.monotonic):
        self.limit, self.window, self.max_keys, self.clock = limit, float(window), max_keys, clock
        self._hits: OrderedDict[str, deque] = OrderedDict()
        self._lock = threading.Lock()

    def hit(self, key: str) -> float:
        """Record one request. Returns 0 when it is allowed, else the seconds until the key may try again (the hit is not recorded)."""
        now = self.clock()
        with self._lock:
            q = self._hits.get(key)
            if q is None:
                q = self._hits[key] = deque(maxlen=self.limit)
                while len(self._hits) > self.max_keys:
                    self._hits.popitem(last=False)
            else:
                self._hits.move_to_end(key)
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return max(0.001, q[0] + self.window - now)
            q.append(now)
            return 0.0


class RefusedSignins:
    """Refused sign-ins per client address in a sliding window; one alert line when an address reaches the threshold."""

    def __init__(self, threshold: int, window: float, alert_path: str | None, max_keys: int = MAX_KEYS,
                 clock=time.monotonic, wall=time.time):
        self.threshold, self.window, self.alert_path = threshold, float(window), alert_path
        self.max_keys, self.clock, self.wall = max_keys, clock, wall
        self._seen: OrderedDict[str, deque] = OrderedDict()
        self._alerted: set[str] = set()
        self._lock = threading.Lock()
        self._wlock = threading.Lock()            # one writer at a time for the alert file

    def _prune(self, addr: str, now: float) -> deque:
        q = self._seen[addr]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) < self.threshold:
            self._alerted.discard(addr)           # fell back below: a new burst may alert again
        return q

    def refused(self, addr: str) -> bool:
        """Count one refused sign-in from addr. True when this one raised the alert."""
        addr = (addr or "unknown")[:64]
        now = self.clock()
        with self._lock:
            if addr not in self._seen:
                self._seen[addr] = deque(maxlen=self.threshold * 4)
                while len(self._seen) > self.max_keys:
                    old, _ = self._seen.popitem(last=False)
                    self._alerted.discard(old)
            else:
                self._seen.move_to_end(addr)
            q = self._prune(addr, now)
            q.append(now)
            if len(q) < self.threshold or addr in self._alerted:
                return False
            self._alerted.add(addr)
            count = len(q)
        self._write({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.wall())), "addr": addr, "count": count,
                     "event": "refused sign-ins"})
        return True

    def over(self) -> int:
        """How many addresses are at or over the threshold right now."""
        now = self.clock()
        with self._lock:
            return sum(1 for a in list(self._seen) if len(self._prune(a, now)) >= self.threshold)

    def _write(self, rec: dict) -> None:
        if not self.alert_path:
            return
        line = json.dumps(rec, separators=(",", ":"))
        with self._wlock:
            self._append(line)

    def _append(self, line: str) -> None:
        try:
            os.makedirs(os.path.dirname(self.alert_path) or ".", exist_ok=True)
            try:
                with open(self.alert_path, encoding="utf-8") as f:
                    lines = f.read().splitlines()[-(ALERT_LINES - 1):]
            except FileNotFoundError:
                lines = []
            tmp = self.alert_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("\n".join([*lines, line]) + "\n")
            os.replace(tmp, self.alert_path)
        except OSError:
            pass                                  # an unwritable alert file must never turn into a failed request
