"""The support packet says what is wrong without carrying anything private: settings as names only, logs scrubbed."""
import datetime as dt
import importlib.util
import json
import pathlib
import zipfile

_s = importlib.util.spec_from_file_location("support_packet", pathlib.Path(__file__).resolve().parent.parent / "support_packet.py")
sp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(sp)


def test_scrub_removes_contacts_keys_numbers_and_the_home_path():
    fake_key, fake_card = "sk-" + "Q" * 20, " ".join(["4111"] * 4)   # built at run time so no scanner reads them as real
    raw = ("mail someone@example.org; token=abc123secret; Authorization: Bearer abcdefgh; "
           f"key {fake_key}; card {fake_card}; /home/example-user/securax/x.log")
    out = sp.scrub(raw, home="/home/example-user")
    for leak in ("someone@", "abc123secret", "abcdefgh", fake_key, fake_card, "/home/example-user"):
        assert leak not in out, leak
    assert "~/securax/x.log" in out
    assert sp.scrub("2026-11-01 09:30 run ok", home="/nowhere") == "2026-11-01 09:30 run ok"     # dates are not numbers to hide
    assert "<number>" in sp.scrub("call 98765 43210", home="/nowhere")


def test_settings_show_names_never_values(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\nGATEWAY_KEY=very-secret-value\nEMPTY=\nQUOTED=''\n")
    out = sp.settings(env)
    assert "very-secret-value" not in out
    assert out.splitlines() == ["GATEWAY_KEY=<set>", "EMPTY=<empty>", "QUOTED=<empty>"]
    assert "not been set up" in sp.settings(tmp_path / "missing.env")


def test_the_packet_is_a_private_zip_with_the_routine_runs(tmp_path):
    (tmp_path / "VERSION").write_text("9.9.9\n")
    (tmp_path / "routines").mkdir()
    (tmp_path / "routines" / ".history.json").write_text(json.dumps({"brief": [{"t": "2026-11-01T09:00", "code": 1, "found": True}]}))
    (tmp_path / "routines" / ".log").write_text("run brief for someone@example.org\n")
    files = sp.collect(tmp_path, quick=True)
    assert "SecuRAX 9.9.9" in files["versions.txt"]
    assert "brief: 2026-11-01T09:00 code 1 flagged" in files["routines.txt"]
    assert "someone@" not in files["log-tail.txt"]
    path = sp.write(files, tmp_path / "out", dt.datetime(2026, 11, 1, 9, 30))
    assert path.name == "securax-support-20261101-0930.zip" and (path.stat().st_mode & 0o077) == 0
    assert {"README.txt", "versions.txt", "settings.txt", "routines.txt", "log-tail.txt"} <= set(zipfile.ZipFile(path).namelist())
