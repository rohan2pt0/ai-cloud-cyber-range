"""governance/modelcheck.py (doc 105, G4): a local model whose digest differs from the approved one reads CHANGED, an unknown
one UNLISTED, and an approval is private and needs a reason. Weight files are scanned for pickle code without loading them.
All digests and files here are fake."""
import importlib.util
import pathlib
import pickle
import zipfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("securax_modelcheck_t", ROOT / "governance" / "modelcheck.py")
mc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(mc)

LIST = """NAME                ID              SIZE      MODIFIED
qwen2.5:1.5b        65ec06548149    986 MB    2 days ago
qwen2.5:0.5b        deadbeefcafe    397 MB    2 days ago
mystery:latest      abcdefabcdef    1.1 GB    1 hour ago
"""


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_VAULT_DIR", str(tmp_path))
    return tmp_path


def test_listed_changed_and_unlisted_models_are_told_apart(vault):
    res = {r["name"]: r["state"] for r in mc.check(mc.parse_list(LIST), mc.approved())}
    assert res == {"qwen2.5:1.5b": "ok", "qwen2.5:0.5b": "changed", "mystery:latest": "unlisted"}


def test_an_approval_needs_a_reason_stays_private_and_then_passes(vault):
    local = mc.parse_list(LIST)
    with pytest.raises(ValueError, match="reason is required"):
        mc.approve("mystery", local, "  ")
    mc.approve("mystery", local, "fake: built in-house from a reviewed Modelfile", by="tester")
    f = vault / "model-digests.json"
    assert oct(f.stat().st_mode & 0o777) == "0o600"
    assert {r["name"]: r["state"] for r in mc.check(local, mc.approved())}["mystery:latest"] == "ok"


def test_every_shipped_default_model_has_an_approved_digest():
    shipped = {"qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:7b", "qwen2.5-coder:7b", "qwen2.5-coder:14b", "llama-guard3:1b"}
    ok = mc.approved(mc.REGISTRY)
    assert shipped <= set(ok) and all(len(ok[m]["digest"]) == 64 for m in shipped)


class _Boom:
    def __reduce__(self):
        import os
        return (os.system, ("echo fake",))


def test_a_pickle_that_would_run_code_on_load_is_caught_without_loading_it(tmp_path):
    bad = tmp_path / "weights.ckpt"
    bad.write_bytes(pickle.dumps(_Boom()))
    good = tmp_path / "plain.pkl"
    good.write_bytes(pickle.dumps({"layer": [1.0, 2.0]}))
    zipped = tmp_path / "model.pt"
    with zipfile.ZipFile(zipped, "w") as z:
        z.writestr("archive/data.pkl", pickle.dumps(_Boom()))
    res = {pathlib.Path(r["file"]).name: r["bad"] for r in mc.scan(tmp_path)}
    assert res["weights.ckpt"] and res["model.pt"] and res["plain.pkl"] == []
    assert any(g.startswith(("posix", "nt", "os")) for g in res["weights.ckpt"])
