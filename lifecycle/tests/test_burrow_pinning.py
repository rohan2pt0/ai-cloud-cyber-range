"""Installers are pinned by hash and run from a file: a tampered download must be refused BEFORE it runs, and none of our own
install paths may pipe a download into a shell."""
import importlib.util
import pathlib
import re
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("burrow", REPO / "lifecycle" / "burrow.py")
burrow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(burrow)

PIPE = re.compile(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(\w+=\S+\s+)*(ba|z)?sh\b", re.I)


def test_spore_never_pipes_a_download_into_a_shell():
    for role, kw in (("server", {}), ("agent", {"join_url": "https://10.0.0.1:6443"})):
        assert not PIPE.search(burrow.install_script(role, "n1", tok="t", **kw))


def test_tampered_k3s_installer_is_refused_before_it_runs(tmp_path):
    script = burrow.install_script("server", "n1", tok="t")
    block = script[script.index("# 2. k3s, pinned"):script.index("systemctl enable --now")]
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    marker = tmp_path / "ran"
    fake = bin_ / "curl"        # serves a payload that would leave a marker if executed
    fake.write_text('#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = "-o" ] && out="$2"; shift; done\n'
                    f'printf "touch {marker}\\n" > "$out"\n')
    fake.chmod(0o755)
    r = subprocess.run(["bash", "-c", "set -e\n" + block], env={"PATH": f"{bin_}:/usr/bin:/bin"}, capture_output=True, text=True)
    assert r.returncode != 0 and "refusing to run it" in r.stdout
    assert not marker.exists(), "the tampered installer ran"


def test_repo_install_paths_have_no_pipe_to_shell():
    paths = ["local/scripts/bootstrap-laptop.sh", "local/scripts/wsl-setup.sh", "WINDOWS-QUICKSTART.md",
             "infra/terraform/lifecycle/modules/tree-aws/user_data.sh.tftpl", "lifecycle/burrow.py"]
    for p in paths:
        assert not PIPE.search((REPO / p).read_text("utf-8")), p
