"""The names-and-site diagnosis (doc 99): each row names what is wrong and the one command that fixes it, and the
cockpit carries it folded. Offline: the TLS module is a stand-in."""
import importlib.util
import pathlib
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_diagnose_t", ROOT / "governance" / "diagnose.py")
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)


def fake_tls(on=True, days=80, resolves="127.0.0.1"):
    return types.SimpleNamespace(tls_is_on=lambda: on, domain=lambda: "securax.localhost", tls_dir=lambda: pathlib.Path("/nonexistent"),
                                 cert_info=lambda p: {"days_left": days} if days is not None else {}, host_of=lambda n, d: f"{n}.{d}",
                                 resolves=lambda fq: resolves)


def by(rows):
    return {r["what"]: r for r in rows}


def test_names_off_points_to_the_one_command():
    rows = by(dg.checks(fake_tls(on=False), {"SITE_URL": "https://o.github.io/r/"}))
    assert rows["Addresses are names"]["ok"] is False and rows["Addresses are names"]["cmd"] == "./securax names"
    assert "Certificate is current" not in rows and rows["Public site answers"]["ok"] is True


def test_a_short_certificate_an_unresolved_name_and_a_domain_not_live_are_each_named():
    rows = by(dg.checks(fake_tls(days=10, resolves=None), {"SITE_DOMAIN": "example.org", "SITE_LIVE": "no", "SITE_URL": "https://o.github.io/r/"}))
    assert rows["Certificate is current"]["ok"] is False and rows["Certificate is current"]["cmd"] == "./securax tls renew"
    assert rows["Names resolve on this machine"]["ok"] is False and "hub.securax.localhost" in rows["Names resolve on this machine"]["detail"]
    site = rows["Public site at your domain"]
    assert site["ok"] is None and site["cmd"] == "./securax site live" and "example.org" in site["detail"]
    assert dg.summary(list(rows.values())) == "1 fine · 2 to fix · 2 to know"


def test_the_panel_is_folded_and_carries_every_row():
    rows = dg.checks(fake_tls(), {"SITE_URL": "https://o.github.io/r/"})
    card = dg.html_card(rows)
    assert card.startswith("<details class='card panel' id='names'>") and " open" not in card[:60]
    assert card.count("<tr>") == len(rows) and "./securax tls trust --apply" in card
