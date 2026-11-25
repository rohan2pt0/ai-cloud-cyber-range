"""The launch gates (governance/release-gates.json, docs/securax/release-readiness.md): the registry stays honest, each probe can fail,
and only a 1.0.0 or later tag is held back."""
import importlib.util
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture()
def rg():
    spec = importlib.util.spec_from_file_location("release_gates_under_test", ROOT / "governance" / "release_gates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LAUNCHES = {"open": "the public launch", "paid": "the paid edition"}
QUEUE = {"items": [{"id": "fix-it", "state": "open"}, {"id": "finished", "state": "done"}]}


def gate(**over):
    g = {"id": "a-gate", "area": "secrets", "blocks": ["open"], "probe": "fake", "title": "A thing that must be true before launch",
         "why": "because a person would be hurt if it were not"}
    g.update(over)
    return g


def reg_of(*gates):
    return {"launches": LAUNCHES, "gates": list(gates)}


def test_the_real_registry_is_honest_and_every_probe_exists(rg):
    reg = rg.load()
    assert rg.problems(reg) == []
    assert {g["probe"] for g in reg["gates"] if "probe" in g} <= set(rg.PROBES)
    assert len(reg["gates"]) >= 30 and {a for g in reg["gates"] for a in g["blocks"]} == {"open", "paid"}
    areas = {g["area"] for g in reg["gates"]}
    assert {"secrets", "supply-chain", "threat-models", "data-leaving-device", "privacy", "investment-advice", "disclaimers", "abuse"} <= areas


def test_a_gate_that_goes_red_without_a_record_fails(rg, monkeypatch):
    monkeypatch.setitem(rg.PROBES, "fake", lambda reg: (False, "the thing is missing"))
    probs = rg.problems(reg_of(gate()), queue=QUEUE)
    assert len(probs) == 1 and "record it on purpose" in probs[0] and "the thing is missing" in probs[0]


def test_a_recorded_failure_needs_a_live_queue_item(rg, monkeypatch):
    monkeypatch.setitem(rg.PROBES, "fake", lambda reg: (False, "the thing is missing"))
    rec = dict(open_since="2026-11-15", fix="build the thing", due="2026-12-01")
    assert rg.problems(reg_of(gate(queue="fix-it", **rec)), queue=QUEUE) == []
    for q in ("finished", "never-written-down"):
        probs = rg.problems(reg_of(gate(queue=q, **rec)), queue=QUEUE)
        assert len(probs) == 1 and "missing or done while the gate still fails" in probs[0]


def test_a_record_left_on_a_gate_that_now_passes_fails(rg, monkeypatch):
    monkeypatch.setitem(rg.PROBES, "fake", lambda reg: (True, "it is there"))
    probs = rg.problems(reg_of(gate(open_since="2026-11-15", fix="build the thing", queue="fix-it", due="2026-12-01")), queue=QUEUE)
    assert len(probs) == 1 and "remove open_since" in probs[0]
    assert rg.problems(reg_of(gate()), queue=QUEUE) == []


def test_an_attest_is_go_only_with_a_date_and_where_the_evidence_is(rg):
    waiting = {k: v for k, v in gate(attest=None, how="turn the setting on", queue="fix-it", due="2026-12-01").items() if k != "probe"}
    assert rg.judge(reg_of(waiting))[0]["state"] == "waiting-owner"
    assert rg.problems(reg_of(waiting), queue=QUEUE) == []
    undated = dict(waiting, due=None)
    assert "needs how, a live queue item and a due date" in rg.problems(reg_of(undated), queue=QUEUE)[0]
    for half in ({"on": "2026-12-01"}, {"evidence": "the letter in the vault"}, {"on": "soon", "evidence": "the letter in the vault"}):
        assert rg.judge(reg_of(dict(waiting, attest=half)))[0]["state"] == "waiting-owner"
    done = dict(waiting, attest={"on": "2026-12-01", "evidence": "the letter in the vault"})
    assert rg.judge(reg_of(done))[0]["state"] == "go"


def test_a_gate_is_a_probe_or_an_attest_never_both_or_neither(rg, monkeypatch):
    monkeypatch.setitem(rg.PROBES, "fake", lambda reg: (True, "it is there"))
    both = gate(attest={"on": "2026-12-01", "evidence": "the letter in the vault"})
    assert any("exactly one" in p for p in rg.problems(reg_of(both), queue=QUEUE))
    assert any("does not exist" in p for p in rg.problems(reg_of(gate(probe="no_such_probe")), queue=QUEUE))


def test_a_paid_only_gate_does_not_hold_the_public_launch(rg, monkeypatch):
    monkeypatch.setitem(rg.PROBES, "fake", lambda reg: (True, "it is there"))
    monkeypatch.setitem(rg.PROBES, "fake_paid", lambda reg: (False, "no terms yet"))
    rows = rg.judge(reg_of(gate(), gate(id="terms", blocks=["paid"], probe="fake_paid")))
    assert rg.verdict(rows, "open") is True and rg.verdict(rows, "paid") is False


def test_only_a_1_0_or_later_tag_is_held_back(rg, monkeypatch):
    assert [rg.tag_needs_launch(t) for t in ("v0.9.0", "0.12.3", "v1.0.0", "v2.3.1", "nightly")] == [False, False, True, True, False]
    monkeypatch.setattr(rg, "judge", lambda reg=None: [{"id": "x", "area": "secrets", "blocks": ["open"], "state": "no-go", "kind": "probe",
                                                         "title": "t", "detail": "d", "fix": "f", "due": "2026-12-01"}])
    assert rg.main(["--for-tag", "v0.9.0"]) == 0
    assert rg.main(["--for-tag", "v1.0.0"]) == 1
    assert rg.main([]) == 1 and rg.main(["--launch", "paid"]) == 0          # nothing blocks paid in this fake


def test_the_release_workflow_asks_the_gate_and_stays_signed(rg, monkeypatch):
    rel = (ROOT / ".github" / "workflows" / "release.yml").read_text()
    assert 'governance/release_gates.py --for-tag "$TAG"' in rel
    assert rg.release_signed({})[0]
    for lost in ("actions/attest-build-provenance", "anchore/sbom-action", "SHA256SUMS", "draft: true"):
        monkeypatch.setattr(rg, "read", lambda p, lost=lost: rel.replace(lost, "gone"))
        ok, detail = rg.release_signed({})
        assert not ok and "release.yml lost" in detail, lost


def test_a_third_party_step_on_a_movable_tag_is_found_and_githubs_own_are_not(rg, monkeypatch):
    flow = ("permissions:\n  contents: read\njobs:\n  a:\n    steps:\n      - uses: actions/checkout@v7\n      - uses: github/codeql-action/upload-sarif@v4\n"
            "      - uses: someone/build-thing@v3\n      - uses: other/scan@" + "ab12" * 10 + "   # v2.1.0\n      - uses: ./.github/workflows/release.yml\n")
    monkeypatch.setattr(rg, "workflows", lambda: {"ci.yml": flow})
    assert rg.unpinned_actions() == ["ci.yml: someone/build-thing@v3"]
    assert rg.actions_pinned({})[0] is False


def test_every_action_in_the_real_workflows_is_pinned_to_a_commit(rg):
    ok, detail = rg.actions_pinned({})
    assert ok, detail                                                    # the real workflows


def test_a_workflow_that_hands_a_stranger_write_access_or_a_shell_is_caught(rg):
    safe = "permissions:\n  contents: read\njobs:\n  a:\n    env:\n      TASK: ${{ github.event.issue.title }}\n    if: github.event.label.name == 'x'\n    steps:\n      - run: echo \"$TASK\"\n"
    assert rg.workflow_problems({"ok.yml": safe}) == []
    assert any("pull_request_target" in p for p in rg.workflow_problems({"a.yml": "on: pull_request_target\npermissions:\n  contents: read\n"}))
    assert any("no top-level permissions" in p for p in rg.workflow_problems({"b.yml": "on: push\njobs: {}\n"}))
    assert any("write-all" in p for p in rg.workflow_problems({"c.yml": "permissions: write-all\n"}))
    shell = "permissions:\n  contents: read\njobs:\n  a:\n    steps:\n      - run: |\n          echo ${{ github.event.pull_request.title }}\n      - run: echo ${{ github.head_ref }}\n"
    assert sum("goes into a shell" in p for p in rg.workflow_problems({"d.yml": shell})) == 2
    assert rg.workflows_safe({})[0], rg.workflows_safe({})[1]            # the real workflows


def test_advice_shaped_wording_is_caught_and_plain_education_is_not(rg):
    def kinds(text):
        return {k for k, pat in rg.ADVICE.items() if re.search(pat, text, re.I)}
    assert kinds("Buy these shares before Friday") == {"tells the person to trade"}
    assert kinds("An assured return of twelve percent") == {"promises a return"}
    assert kinds("the next multibagger") == {"promises a return"}
    assert kinds("Ask your financial advisor inside the app") == {"calls us an adviser"}
    assert kinds("The top 5 mutual funds this year") == {"picks products"}
    for plain in ("A low-cost index fund spreads risk across the whole market.", "Check the adviser's registration with the regulator.",
                  "Scammers promise 'guaranteed' IPO allotments."):
        assert kinds(plain) == set(), plain


def test_a_new_advice_phrase_fails_and_a_reviewed_one_must_still_be_in_the_copy(rg, monkeypatch):
    monkeypatch.setattr(rg, "advice_hits", lambda: [("app.html", "promises a return", "… the match is a guaranteed 100% return. Tap …")])
    reviewed = {"advice_wording_reviewed": [{"phrase": "a guaranteed 100% return", "why": "an employer's match"}]}
    assert rg.no_recommendation(reviewed)[0]
    assert not rg.no_recommendation({"advice_wording_reviewed": []})[0]
    stale = {"advice_wording_reviewed": reviewed["advice_wording_reviewed"] + [{"phrase": "a phrase that is gone", "why": "old"}]}
    ok, detail = rg.no_recommendation(stale)
    assert not ok and "no longer in the copy" in detail


def test_the_storefront_never_calls_the_current_version_open_source(rg):
    for claim in ("The open-source edition stays free", "SecuRAX is open source", "free and open-source", "a FOSS platform", "the open source core"):
        assert re.search(rg.NOT_OPEN_SOURCE, claim, re.I), claim
    for fine in ("Open-source intelligence for your own life", "each version becomes MIT after two years", "built on open-source tools"):
        assert not re.search(rg.NOT_OPEN_SOURCE, fine, re.I), fine
    assert rg.licence_wording({})[0], rg.licence_wording({})[1]


def test_a_page_that_loads_from_another_site_or_names_a_tracker_is_caught(rg, monkeypatch):
    assert rg.no_trackers({})[0], rg.no_trackers({})[1]                  # the real pages
    pages = {"a.html": '<link rel="stylesheet" href="https://fonts.example.net/css">', "b.html": '<script src="https://cdn.example.net/x.js"></script>',
             "c.html": "<script>/* www.google-analytics.com/collect */</script>", "d.html": '<a href="https://example.org/read">a link is not a load</a>'}
    monkeypatch.setattr(rg, "shipped_pages", lambda: list(pages))
    monkeypatch.setattr(rg, "read", lambda p: pages[p])
    ok, detail = rg.no_trackers({})
    assert not ok
    for only in ("a.html", "b.html", "c.html"):
        monkeypatch.setattr(rg, "shipped_pages", lambda only=only: [only])
        assert not rg.no_trackers({})[0], only
    monkeypatch.setattr(rg, "shipped_pages", lambda: ["d.html"])
    assert rg.no_trackers({})[0]


def test_an_outside_address_in_the_code_must_belong_to_a_declared_flow(rg, monkeypatch):
    assert rg.flows_declared(rg.load())[0], rg.flows_declared(rg.load())[1]     # the real flows, before anything is faked
    flow = {"id": "backup", "hosts": ["drive.example.net"], "what": "a sealed copy of the data", "when": "only after the person connects it",
            "to": "the person's own account", "protection": "sealed on the device", "model": "hosted-apps"}
    monkeypatch.setattr(rg, "code_hosts", lambda: {"drive.example.net"})
    assert rg.flows_declared({"flows": [flow]})[0]
    monkeypatch.setattr(rg, "code_hosts", lambda: {"drive.example.net", "new.example.net"})
    assert "which no flow declares" in rg.flows_declared({"flows": [flow]})[1]
    monkeypatch.setattr(rg, "code_hosts", lambda: set())
    assert "no longer in the code" in rg.flows_declared({"flows": [flow]})[1]
    monkeypatch.setattr(rg, "code_hosts", lambda: {"drive.example.net"})
    assert "does not say when" in rg.flows_declared({"flows": [dict(flow, when="")]})[1]


def test_a_legal_page_needs_every_part_and_its_links(rg, monkeypatch):
    files = {"PRIVACY.md": "# Privacy\n" + "\n".join("## " + p.title() for p in rg.PRIVACY_PARTS), "README.md": "see PRIVACY.md", "website/index.html": '<a href="PRIVACY.md">'}
    monkeypatch.setattr(rg, "read", lambda p: files.get(p, ""))
    assert rg.privacy_notice({})[0]
    files["PRIVACY.md"] = files["PRIVACY.md"].replace("## Children", "")
    assert "children" in rg.privacy_notice({})[1]
    files["README.md"] = ""
    assert "a link from README.md" in rg.privacy_notice({})[1]
    del files["PRIVACY.md"]
    assert rg.privacy_notice({})[1] == "PRIVACY.md does not exist"


def test_the_doc_names_every_gate_and_the_command(rg):
    doc = (ROOT / "docs" / "securax" / "release-readiness.md").read_text()
    missing = [g["id"] for g in rg.load()["gates"] if f"`{g['id']}`" not in doc]
    assert not missing, f"docs/securax/release-readiness.md does not name: {missing}"
    assert "./securax release ready" in doc
    assert json.loads((ROOT / "governance" / "release-gates.json").read_text())["about"]
