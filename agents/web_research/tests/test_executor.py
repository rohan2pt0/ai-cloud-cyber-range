"""Approved-action executor — a write happens ONLY with explicit approval and only after every
gate re-validates; every attempt is audited and credentials are never logged. All offline."""
from agents.web_research import Action, execute_action


def _resolver(mapping):
    def r(host, port, *a, **k):
        ip = mapping.get(host)
        if ip is None:
            raise OSError("no such host")
        return [(2, 1, 6, "", (ip, 0))]
    return r


PUBLIC = _resolver({"shop.example": "93.184.216.34", "evil.example": "10.0.0.5"})


def _run(action, approve, allow=None, deny=None, resolver=PUBLIC):
    log = []
    done = []
    res = execute_action(action, approve=approve, allow=allow if allow is not None else ["shop.example"],
                         deny=deny, resolver=resolver,
                         perform=lambda a: (done.append(a) or (200, "ok")),
                         audit_log=lambda e: log.append(e))
    return res, log, done


def test_refuses_without_approval_and_never_performs():
    a = Action("POST", "https://shop.example/checkout", {"card": "secret"}, reason="buy")
    res, log, done = _run(a, approve=False)
    assert not res["executed"] and "approval required" in res["outcome"]
    assert done == []                                   # the request was never made
    assert len(log) == 1 and log[0]["approved"] is False


def test_audit_never_contains_credentials():
    a = Action("POST", "https://shop.example/login",
               {"password": "hunter2"}, {"Authorization": "Bearer sekret"}, reason="login")
    _res, log, _done = _run(a, approve=True)
    blob = str(log[0])
    assert "hunter2" not in blob and "sekret" not in blob   # body/headers are never audited
    assert log[0]["url"].endswith("/login") and log[0]["outcome"] == "executed"


def test_executes_only_when_approved_allowlisted_and_safe():
    a = Action("POST", "https://shop.example/submit", {"q": "x"}, reason="submit form")
    res, log, done = _run(a, approve=True)
    assert res["executed"] and res["status"] == 200
    assert len(done) == 1 and log[0]["outcome"] == "executed"


def test_refuses_off_allowlist_even_when_approved():
    a = Action("POST", "https://other.example/x", reason="x")
    res, log, done = _run(a, approve=True, allow=["shop.example"])
    assert not res["executed"] and "allowlist" in res["outcome"]
    assert done == []


def test_refuses_ssrf_internal_target_even_when_approved():
    a = Action("POST", "http://169.254.169.254/latest/", reason="meta")
    res, log, done = _run(a, approve=True, allow=["*"])
    assert not res["executed"] and "SSRF" in res["outcome"]
    assert done == []


def test_refuses_allowlisted_host_resolving_to_private_ip():
    a = Action("POST", "https://evil.example/x", reason="rebind")
    res, _log, done = _run(a, approve=True, allow=["evil.example"])   # resolves to 10.0.0.5
    assert not res["executed"] and "DNS" in res["outcome"]
    assert done == []


def test_get_and_head_are_refused_as_reads():
    for m in ("GET", "HEAD"):
        a = Action(m, "https://shop.example/x", reason="read")
        res, _log, done = _run(a, approve=True, allow=["shop.example"])
        assert not res["executed"] and "read" in res["outcome"]
        assert done == []


def test_perform_error_is_recorded_not_raised():
    a = Action("POST", "https://shop.example/x", reason="x")
    log = []

    def boom(_a):
        raise RuntimeError("network down")

    res = execute_action(a, approve=True, allow=["shop.example"], resolver=PUBLIC,
                         perform=boom, audit_log=lambda e: log.append(e))
    assert not res["executed"] and "error" in res["outcome"]
    assert log[0]["allowed"] is True
