"""The interview demo: one command seeds a played exercise of dummy data and serves the portal."""
import pathlib
import threading
import urllib.request

from exercise import demo, portal


def test_the_demo_seeds_a_played_game_and_serves_the_portal(tmp_path: pathlib.Path):
    g, tokens = demo.seed(tmp_path / "g")
    assert {"white", "red", "blue-8:Asha"} <= set(tokens)
    assert len(g.attacks(8)) == 2
    srv = portal.serve(g, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_address[1]}/", timeout=10) as r:
            assert r.status == 200
    finally:
        srv.shutdown()
