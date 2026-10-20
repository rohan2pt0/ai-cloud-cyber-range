"""Service checks, the way an exercise's scoring bot does them: is each required service up and answering properly?

Each check returns (ok, detail). It never logs in and never changes anything: a port that is open but answers wrongly
(a web page without the expected text, a DNS server that does not resolve the name) is a failure, as in a real exercise.
Standard library only, so the same code runs on the laptop and inside the small scoring container.
"""
from __future__ import annotations

import http.client
import random
import shutil
import socket
import ssl
import struct
import subprocess

TIMEOUT = 3.0


def _banner(ip: str, port: int, prefix: bytes, timeout: float) -> tuple[bool, str]:
    with socket.create_connection((ip, port), timeout=timeout) as s:
        s.settimeout(timeout)
        data = s.recv(256)
    text = data.decode("latin-1", "replace").strip()[:80]
    return (data.startswith(prefix), text or "no greeting")


def tcp(ip: str, port: int, timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    with socket.create_connection((ip, port), timeout=timeout):
        return True, "port open"


def ssh(ip: str, port: int, timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    return _banner(ip, port, b"SSH-", timeout)


def smtp(ip: str, port: int, timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    return _banner(ip, port, b"220", timeout)


def _web(ip: str, port: int, tls: bool, expect: str, timeout: float) -> tuple[bool, str]:
    if tls:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False          # exercise hosts use their own certificates; the bot checks the service, not the CA
        ctx.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection(ip, port, timeout=timeout, context=ctx)
    else:
        conn = http.client.HTTPConnection(ip, port, timeout=timeout)
    try:
        conn.request("GET", "/", headers={"User-Agent": "securax-scoring-bot"})
        r = conn.getresponse()
        body = r.read(65536).decode("utf-8", "replace")
    finally:
        conn.close()
    if r.status >= 400:
        return False, f"HTTP {r.status}"
    if expect and expect not in body:
        return False, f"HTTP {r.status} but the page lacks {expect!r} (defaced or wrong site?)"
    return True, f"HTTP {r.status}"


def http_(ip: str, port: int, expect: str = "", timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    return _web(ip, port, False, expect, timeout)


def https(ip: str, port: int, expect: str = "", timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    return _web(ip, port, True, expect, timeout)


def dns_query(name: str, qid: int) -> bytes:
    q = b"".join(bytes([len(p)]) + p.encode("ascii") for p in name.rstrip(".").split(".")) + b"\0"
    return struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0) + q + struct.pack(">HH", 1, 1)   # recursion desired, one A question


def dns(ip: str, port: int, query: str = "", timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    qid = random.randrange(1, 65535)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        s.sendto(dns_query(query or "localhost", qid), (ip, port))
        data, _ = s.recvfrom(4096)
    if len(data) < 12:
        return False, "short reply"
    rid, flags, _qd, an = struct.unpack(">HHHH", data[:8])
    if rid != qid:
        return False, "reply id does not match"
    rcode = flags & 0xF
    if rcode:
        return False, f"error code {rcode} for {query}"
    if an == 0:
        return False, f"no answer for {query}"
    return True, f"{an} answer(s) for {query}"


def ping(ip: str, port: int = 0, timeout: float = TIMEOUT, **_) -> tuple[bool, str]:
    """The "HOST" check: one ICMP echo. Exercise rules require ping to stay allowed, so a host that drops it scores as down."""
    if not shutil.which("ping"):
        return False, "no ping program on the scoring machine"
    p = subprocess.run(["ping", "-c", "1", "-W", str(max(1, int(timeout))), ip], capture_output=True, text=True, timeout=timeout + 5)
    return (p.returncode == 0, "answers ping" if p.returncode == 0 else "no reply to ping")


RUN = {"tcp": tcp, "ssh": ssh, "smtp": smtp, "http": http_, "https": https, "dns": dns, "ping": ping}


def run(row: dict, timeout: float = TIMEOUT) -> tuple[bool, str]:
    try:
        return RUN[row["check"]](row["ip"], row["port"], expect=row.get("expect", ""), query=row.get("query", ""), timeout=timeout)
    except (OSError, http.client.HTTPException, ssl.SSLError, UnicodeError, subprocess.SubprocessError) as e:
        return False, (type(e).__name__ + ": " + str(e))[:120]
