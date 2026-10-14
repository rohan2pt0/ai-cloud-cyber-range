"""Storage: sizes parse, the forecast is honest about not knowing, advice appears when it should, tidy never deletes without --yes."""
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("storage", REPO / "governance" / "storage.py")
st = importlib.util.module_from_spec(spec)
sys.modules["storage"] = st
spec.loader.exec_module(st)
DAY = 86400


def test_parse_size_and_human():
    assert st.parse_size("16.24GB") == 16_240_000_000 and st.parse_size("125.8MB") == 125_800_000 and st.parse_size("0B") == 0 and st.parse_size("5kB") == 5000 and st.parse_size("") == 0
    assert st.human(1_500_000_000) == "1.5 GB" and st.human(12) == "12 B"


def rows(daily_growth, n=10, base=10e9, start=1_000_000):
    return [{"ts": start + i * DAY, "estate": base + i * daily_growth} for i in range(n)]


def test_forecast_collecting_flat_and_growing():
    assert st.forecast(rows(1e9, n=2), 50e9)["state"] == "collecting"
    assert st.forecast([{"ts": 1, "estate": 1}, {"ts": 2, "estate": 2}, {"ts": 3, "estate": 3}], 5e9)["state"] == "collecting"       # under two days of data
    assert st.forecast(rows(0), 50e9)["state"] == "flat"
    f = st.forecast(rows(1e9), 50e9)
    assert f["state"] == "growing" and abs(f["days"] - 50) <= 1 and abs(f["bytes_per_day"] - 1e9) < 1e6


def measure(free_pct=50, backups=0, newest=None, reclaim=0, vols=()):
    return {"disk": {"free_pct": free_pct, "free": 100e9, "total": 200e9, "path": "/"}, "backups": {"count": 1 if newest is not None else 0, "bytes": backups, "newest_age_days": newest, "dir": "b"},
            "docker": True, "docker_usage": {"Images": {"bytes": reclaim, "reclaimable_bytes": reclaim}}, "volumes": list(vols), "home": {"bytes": 0, "dir": "h"}, "estate_bytes": 1}


def test_advice_by_situation():
    ok = st.advice(measure(newest=1), {"state": "flat"})
    assert len(ok) == 1 and "Nothing needs doing" in ok[0]
    assert "URGENT" in st.advice(measure(free_pct=5, newest=1), {"state": "flat"})[0]
    assert any("plan a clean-up" in a for a in st.advice(measure(free_pct=15, newest=1), {"state": "flat"}))
    assert any("full in about 20 days" in a for a in st.advice(measure(newest=1), {"state": "growing", "days": 20, "bytes_per_day": 2e9}))
    assert any("No backup yet" in a for a in st.advice(measure(), {"state": "flat"}))
    assert any("reclaimed safely" in a for a in st.advice(measure(newest=1, reclaim=8e9), {"state": "flat"}))
    assert any("model store" in a for a in st.advice(measure(newest=1, vols=[{"name": "vulnbank-range_ollama", "bytes": 9e9}]), {"state": "flat"}))


def test_history_is_recorded_at_most_every_twelve_hours(tmp_path):
    p = tmp_path / "h.jsonl"
    m = {"ts": 1000, "estate_bytes": 5, "disk": {"free": 9}, "backups": {"bytes": 1}}
    assert st.record(m, path=p) is True
    assert st.record({**m, "ts": 1000 + 3600}, path=p) is False
    assert st.record({**m, "ts": 1000 + 13 * 3600}, path=p) is True
    assert len(st.load_history(p)) == 2


def test_tidy_without_yes_only_describes(monkeypatch):
    called = []
    monkeypatch.setattr(st, "docker_json", lambda *a, **k: called.append(a) or "Total reclaimed space: 1GB")
    out = st.tidy(False)
    assert all(o.startswith("would remove") for o in out) and not called
    out = st.tidy(True)
    assert len(called) == 2 and all("reclaimed 1GB" in o for o in out)
    assert all(a[0] in ("image", "builder") and "volume" not in a for a in called)              # never touches volumes


def test_measure_counts_backups(tmp_path, monkeypatch):
    b = tmp_path / "backups"
    b.mkdir()
    (b / "securax-1.tar.gz").write_bytes(b"x" * 1000)
    monkeypatch.setattr(st, "docker_json", lambda *a, **k: None)
    monkeypatch.setattr(st, "HOME", tmp_path / "home")
    m = st.measure(root=tmp_path, backups=b)
    assert m["backups"]["count"] == 1 and m["backups"]["bytes"] == 1000 and m["docker"] is False and json.dumps(m)
