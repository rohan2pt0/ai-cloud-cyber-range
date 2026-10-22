"""Each test starts with an empty per-caller rate limit: the limiter is per minute, so a long suite would otherwise make
later tests depend on how many chat calls earlier ones happened to make."""
import pytest


@pytest.fixture(autouse=True)
def _fresh_rate_limit_and_idempotency(tmp_path, monkeypatch):
    import app.main as m
    from app import baseline
    m._buckets.clear()
    m._IDEM.clear()
    monkeypatch.setattr(baseline, "STATE", tmp_path / "baselines.json")    # never write the real volume from a test
    baseline.reset()
    yield
    baseline.reset()
