"""model_bench: measures installed models against a fake Ollama and recommends the one that FITS, is ACCURATE and is FAST enough."""
import importlib.util
import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("mb", HERE / "model_bench.py")
mb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mb)

ANSWERS = {  # what a competent model says to each task
    "Ignore all previous": "Yes", "NEFT transfer": "No", "AKIAIOSFODNN7EXAMPLE": "Yes", "Kerberoasting": "T1558.003",
    "203.0.113.9": "203.0.113.9", "digital personal data": "The DPDP Act, 2023.", "Five prompt-injection": "Block and rate-limit the user.",
    "leaked AWS access key": '{"severity": "high"}',
}
MODELS = {  # name: (bytes, tokens/s, competent?)
    "tiny:1b": (800_000_000, 40.0, False),
    "good:3b": (2_000_000_000, 12.0, True),
    "slow:7b": (4_400_000_000, 1.5, True),
    "huge:70b": (40_000_000_000, 20.0, True),
}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = json.dumps({"models": [{"name": n, "size": v[0]} for n, v in MODELS.items()]}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = req["messages"][0]["content"]
        _, tps, competent = MODELS[req["model"]]
        reply = next((a for k, a in ANSWERS.items() if k in prompt), "OK") if competent else "I am not sure."
        n = 20
        body = json.dumps({"message": {"content": reply}, "eval_count": n, "eval_duration": int(n / tps * 1e9)}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def url():
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def run(url, ram_mb, **kw):
    have = mb.installed(url)
    res = [mb.bench_model(url, m["name"], m["size"], 30) for m in have]
    return mb.judge(res, ram_mb, kw.get("reserve", 4096), kw.get("min_acc", 0.6), kw.get("min_tps", 4.0))


def test_it_recommends_the_model_that_fits_is_accurate_and_fast(url):
    rep = run(url, 16 * 1024)
    by = {r["model"]: r for r in rep["results"]}
    assert rep["recommended"] == "good:3b"
    assert by["good:3b"]["accuracy"] == 1.0 and by["good:3b"]["tps"] == 12.0
    assert "accuracy" in by["tiny:1b"]["verdict"]                       # fast but wrong
    assert "tokens/s" in by["slow:7b"]["verdict"]                       # right but unusably slow
    assert "needs ~" in by["huge:70b"]["verdict"]                       # right and fast but does not fit 16 GB


def test_more_ram_changes_the_answer_only_when_it_should(url):
    rep = run(url, 128 * 1024)
    assert next(r for r in rep["results"] if r["model"] == "huge:70b")["ok"]          # it fits now...
    assert rep["recommended"] == "huge:70b" and rep["fastest"] == "huge:70b"          # ...and, equally accurate but faster, it wins


def test_tiny_machine_gets_an_honest_no_model_message(url):
    rep = run(url, 3 * 1024)                                             # 3 GB total: nothing fits after the reserve
    assert rep["recommended"] is None
    assert "no installed model is both usable" in mb.render(rep)


def test_an_unreachable_model_is_reported_not_fatal():
    r = mb.bench_model("http://127.0.0.1:9", "x:1b", 1_000_000_000, 2)
    assert "error" in r
    assert "could not be measured" in mb.judge([r], 16384, 4096, 0.6, 4.0)["results"][0]["verdict"]


def test_cli_json_apply_writes_only_the_recommendation(url, tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("KEEP=1\nLOCAL_MODEL=qwen2.5:1.5b\n")
    import os
    os.environ["SECURAX_SIM_MEM_MB"] = str(16 * 1024)
    try:
        assert mb.main(["--url", url, "--json", "--models", "tiny:1b,good:3b"]) == 0
        rep = json.loads(capsys.readouterr().out)
        out = tmp_path / "r.json"
        out.write_text(json.dumps(rep))
        assert mb.main(["--from-json", str(out), "--apply", "--env-file", str(env)]) == 0
    finally:
        del os.environ["SECURAX_SIM_MEM_MB"]
    txt = env.read_text()
    assert "LOCAL_MODEL=good:3b" in txt and "KEEP=1" in txt


def test_the_eight_tasks_are_deterministic_checks_with_no_network_dependency():
    assert len(mb.TASKS) == 8 and all(callable(t[2]) for t in mb.TASKS)
    assert mb.TASKS[1][2]("no") and not mb.TASKS[1][2]("yes")
