"""SecuRAX sandbox harness — a clean "user machine" that runs the REAL product.

Principle: test the product exactly as a user receives it. Nothing here re-implements the product:
  * the working tree is copied into a fresh directory (what `git clone` would give you, plus your
    uncommitted changes, so you test what you are about to commit);
  * the REAL `./securax` CLI is executed (up / down / doctor / guard / providers / update …);
  * the REAL docker-compose.yml and the REAL images run (nginx, LiteLLM, Ollama, Open WebUI,
    and the gateway/estate-sync images built from the repo's own Dockerfiles);
  * the only additions are a `docker-compose.override.yml` (which compose auto-loads) that
      - impersonates the cloud providers at the NETWORK level (fake_providers.py), so real keys and
        real spend are not needed but the unmodified LiteLLM config is exercised, and
      - on hosts behind a TLS-inspecting proxy, makes containers trust that CA (no-op elsewhere).

Standard library + PyYAML (+ Playwright for the browser journeys).
"""
from __future__ import annotations

import json
import os
import pathlib
import pty
import re
import select
import shutil
import subprocess
import time
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path(os.environ.get("SANDBOX_WORK", "/tmp/securax-sandbox"))
CLONE = WORK / "clone"
OUT = REPO / "sandbox" / "out"
SHOTS = OUT / "shots"

GATEWAY = "http://127.0.0.1:8080"
GUIDING_MAP = "http://127.0.0.1:8088"
WEBUI = "http://127.0.0.1:3000"
FAKE_CTL = "http://127.0.0.1:19000"

PROVIDER_HOSTS = ["generativelanguage.googleapis.com", "api.groq.com", "openrouter.ai", "api.openai.com",
                  "api.deepseek.com", "api.mistral.ai", "api.x.ai", "api.perplexity.ai", "api.anthropic.com"]
LITE_SERVICES = "gateway litellm ollama open-webui guiding-map estate-sync"
PROXY_CA = pathlib.Path("/root/.ccr/ca-bundle.crt")    # present only inside the Claude Code cloud sandbox


def sh(cmd, cwd=None, env=None, timeout=300, stdin: str | None = None) -> tuple[int, str]:
    """Run a command, return (rc, combined output). Output goes via a file so background children
    (e.g. the model pull `./securax up` backgrounds) can never keep a pipe open and hang us."""
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / f".sh-{os.getpid()}-{time.time_ns()}.log"
    with open(log, "wb") as f:
        try:
            p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout, stdout=f, stderr=subprocess.STDOUT,
                               input=(stdin.encode() if stdin is not None else None),
                               stdin=(None if stdin is not None else subprocess.DEVNULL))
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = 124
    out = log.read_text(errors="replace")
    log.unlink(missing_ok=True)
    return rc, re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", out)


class Resp:
    def __init__(self, status: int, headers: dict, text: str):
        self.status, self.headers, self.text = status, headers, text

    def json(self):
        try:
            return json.loads(self.text)
        except Exception:  # noqa: BLE001
            return None


class Sandbox:
    def __init__(self, work: pathlib.Path = WORK):
        self.clone = work / "clone"
        self.env_path = self.clone / "local" / "compose" / ".env"
        self.version = (REPO / "VERSION").read_text().strip()
        self.behind_tls_proxy = PROXY_CA.exists() and bool(os.environ.get("HTTPS_PROXY"))

    # ───────────────────────────── building the "user machine" ─────────────────────────────
    def fresh_clone(self) -> None:
        """Copy tracked + untracked-but-not-ignored files (i.e. what you are about to commit)."""
        if self.clone.exists():
            shutil.rmtree(self.clone)
        self.clone.mkdir(parents=True)
        rc, files = sh(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=REPO)
        for rel in filter(None, files.split("\0")):
            if rel.startswith("sandbox/out/"):
                continue
            src = REPO / rel
            if not src.is_file():
                continue
            dst = self.clone / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        self._make_certs()
        self._host_quirks()
        self._write_override()

    def _make_certs(self) -> None:
        d = self.clone / "sandbox" / "out" / "certs"
        d.mkdir(parents=True, exist_ok=True)
        run = lambda *a: sh(list(a), cwd=d)  # noqa: E731
        run("openssl", "genrsa", "-out", "ca.key", "2048")
        run("openssl", "req", "-x509", "-new", "-nodes", "-key", "ca.key", "-sha256", "-days", "30",
            "-subj", "/CN=SecuRAX Sandbox CA", "-out", "ca.crt",
            "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign",
            "-addext", "subjectKeyIdentifier=hash")
        run("openssl", "genrsa", "-out", "server.key", "2048")
        run("openssl", "req", "-new", "-key", "server.key", "-subj", "/CN=fake-providers", "-out", "server.csr")
        # Strict TLS verification (Python 3.13 / OpenSSL 3) rejects certs without these extensions.
        (d / "ext.cnf").write_text(
            "subjectAltName=" + ",".join(f"DNS:{h}" for h in PROVIDER_HOSTS) + "\n"
            "basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n"
            "extendedKeyUsage=serverAuth\nauthorityKeyIdentifier=keyid,issuer\nsubjectKeyIdentifier=hash\n")
        rc, out = run("openssl", "x509", "-req", "-in", "server.csr", "-CA", "ca.crt", "-CAkey", "ca.key",
                      "-CAcreateserial", "-out", "server.crt", "-days", "30", "-sha256", "-extfile", "ext.cnf")
        assert (d / "server.crt").exists(), f"cert generation failed: {out[-300:]}"
        os.chmod(d / "server.key", 0o644)    # the fake runs as root in a throwaway container

    def _host_quirks(self) -> None:
        """Behind a TLS-inspecting proxy (the Claude Code cloud sandbox) containers don't trust the
        proxy's CA, so `pip install` inside the PRODUCT's own Dockerfiles fails. We fix the ENVIRONMENT
        (a local base image that trusts the CA), never the product. Elsewhere this is a no-op."""
        if not self.behind_tls_proxy:
            return
        hf = self.clone / "sandbox" / "out" / "hostfix"
        hf.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROXY_CA, hf / "ca-bundle.crt")
        (hf / "Dockerfile").write_text(
            "FROM python:3.12-slim\nCOPY ca-bundle.crt /etc/ssl/certs/ca-certificates.crt\n"
            "ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt PIP_CERT=/etc/ssl/certs/ca-certificates.crt "
            "REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt\n")
        rc, out = sh(["docker", "build", "-q", "-t", "sbx-python-ca", str(hf)], timeout=300)
        if rc == 0:
            sh(["docker", "tag", "sbx-python-ca", "python:3.12-slim"])

    def _write_override(self) -> None:
        import yaml
        sb = "/sandbox/out"
        override: dict = {"services": {
            "fakeproviders": {
                "image": "vulnbank/llm-gateway:dev", "pull_policy": "never", "user": "0", "profiles": ["ai"],
                "command": ["python", "/sandbox/fakes/fake_providers.py"], "healthcheck": {"disable": True},
                "environment": {"FAKE_CERT": f"{sb}/certs/server.crt", "FAKE_KEY": f"{sb}/certs/server.key"},
                "volumes": ["../../sandbox:/sandbox:ro"],
                "ports": ["127.0.0.1:19000:9000"],
                "networks": {"modelplane": {"aliases": PROVIDER_HOSTS}},
            },
            "litellm": {
                "environment": {"SSL_CERT_FILE": f"{sb}/certs/ca.crt", "REQUESTS_CA_BUNDLE": f"{sb}/certs/ca.crt",
                                "LITELLM_LOCAL_MODEL_COST_MAP": "True"},
                "volumes": ["../../sandbox:/sandbox:ro"],
                "depends_on": ["fakeproviders"],
            },
        }}
        if self.behind_tls_proxy:   # ollama pulls models over TLS; open-webui must not wait on HuggingFace
            override["services"]["ollama"] = {
                "environment": {"SSL_CERT_FILE": f"{sb}/hostfix/ca-bundle.crt"},
                "volumes": ["../../sandbox:/sandbox:ro"]}
        override["services"]["open-webui"] = {"environment": {"HF_HUB_OFFLINE": "1", "OFFLINE_MODE": "true"}}
        (self.clone / "local" / "compose" / "docker-compose.override.yml").write_text(yaml.safe_dump(override))

    # ───────────────────────────── configuring the user's machine ─────────────────────────────
    def reset_env(self, **kv: str) -> None:
        """A brand-new .env exactly as `./securax` would create it (copy of .env.example) + overrides."""
        ex = (self.clone / "local" / "compose" / ".env.example").read_text()
        self.env_path.write_text(ex)
        self.set_env(**kv)

    def set_env(self, **kv: str) -> None:
        txt = self.env_path.read_text() if self.env_path.exists() else ""
        for k, v in kv.items():
            if re.search(rf"(?m)^{k}=", txt):
                txt = re.sub(rf"(?m)^{k}=.*$", f"{k}={v}", txt)
            else:
                txt += f"\n{k}={v}\n"
        self.env_path.write_text(txt)

    def get_env(self, key: str) -> str:
        m = re.search(rf"(?m)^{key}=(.*)$", self.env_path.read_text())
        return m.group(1).strip() if m else ""

    # ───────────────────────────── driving the REAL product ─────────────────────────────
    def securax(self, *args: str, timeout: int = 900, cwd: pathlib.Path | None = None) -> tuple[int, str]:
        return sh(["bash", "./securax", *args], cwd=cwd or self.clone, timeout=timeout)

    def compose(self, *args: str, timeout: int = 600) -> tuple[int, str]:
        return sh(["docker", "compose", *args], cwd=self.clone / "local" / "compose", timeout=timeout)

    def down(self) -> None:
        if self.clone.exists():
            self.securax("down", timeout=180)

    def pty_session(self, args: list[str], script: list[tuple[str, str]], timeout: int = 120) -> tuple[int, str]:
        """Run the CLI on a real pseudo-terminal and answer its prompts (for the interactive wizards)."""
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.clone)
            os.execvp("bash", ["bash", "./securax", *args])
        buf, pos, i, deadline = b"", 0, 0, time.time() + timeout
        while time.time() < deadline:
            r, _, _ = select.select([fd], [], [], 0.5)
            if r:
                try:
                    data = os.read(fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                buf += data
            if i < len(script) and script[i][0].encode() in buf[pos:]:
                pos = len(buf)
                time.sleep(0.4)          # a person types after the prompt appears, not before
                os.write(fd, (script[i][1] + "\n").encode())
                i += 1
        try:
            _, status = os.waitpid(pid, 0)
            rc = os.waitstatus_to_exitcode(status)
        except ChildProcessError:
            rc = -1
        return rc, re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf.decode(errors="replace")).replace("\r", "")

    # ───────────────────────────── probing ─────────────────────────────
    def http(self, method: str, url: str, body=None, headers: dict | None = None, timeout: int = 60,
             follow: bool = True) -> Resp:
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json", **(headers or {})}
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(req, timeout=timeout) as r:
                return Resp(r.status, dict(r.headers), r.read().decode(errors="replace"))
        except urllib.error.HTTPError as e:
            return Resp(e.code, dict(e.headers), e.read().decode(errors="replace"))
        except Exception as e:  # noqa: BLE001
            return Resp(0, {}, f"{type(e).__name__}: {e}")

    def wait_http(self, url: str, timeout: int = 180, ok: tuple = (200,)) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if self.http("GET", url, timeout=5).status in ok:
                return True
            time.sleep(2)
        return False

    def wait_until(self, fn, timeout: int = 120, every: float = 2.0) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                if fn():
                    return True
            except Exception:  # noqa: BLE001
                pass
            time.sleep(every)
        return False

    def local_model(self) -> str:
        return self.get_env("LOCAL_MODEL") or "qwen2.5:1.5b"      # the SHIPPED default — test what users get

    def master_key(self) -> str:
        return self.get_env("LITELLM_MASTER_KEY") or "sk-range-dev"

    def chat(self, model: str, text: str, stream: bool = False, timeout: int = 240) -> Resp:
        return self.http("POST", f"{GATEWAY}/v1/chat/completions",
                         {"model": model, "stream": stream, "messages": [{"role": "user", "content": text}]},
                         headers={"Authorization": f"Bearer {self.master_key()}"}, timeout=timeout)

    @staticmethod
    def answer(r: Resp) -> str:
        j = r.json()
        try:
            return j["choices"][0]["message"]["content"]
        except Exception:  # noqa: BLE001
            return ""

    def models(self) -> list[str]:
        j = self.http("GET", f"{GATEWAY}/v1/models", timeout=20).json() or {}
        return [m["id"] for m in j.get("data", [])]

    def ollama_has(self, model: str) -> bool:
        rc, cid = sh(["docker", "compose", "ps", "-q", "ollama"], cwd=self.clone / "local" / "compose")
        cid = cid.strip()
        if rc != 0 or not cid:
            return False
        rc, out = sh(["docker", "exec", cid, "ollama", "list"])
        return rc == 0 and model in out

    # ───────────────────────────── the fake cloud providers ─────────────────────────────
    def fake(self, provider: str, mode: str) -> None:
        self.http("POST", f"{FAKE_CTL}/ctl/mode", {"provider": provider, "mode": mode}, timeout=10)

    def fake_reset(self) -> None:
        self.http("POST", f"{FAKE_CTL}/ctl/reset", {}, timeout=10)

    def fake_log(self, provider: str = "") -> list[dict]:
        return self.http("GET", f"{FAKE_CTL}/ctl/log?provider={provider}", timeout=10).json() or []

    def logs(self, service: str, tail: int = 25) -> str:
        return self.compose("logs", "--no-color", "--tail", str(tail), service, timeout=60)[1]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D401
        return None


# ───────────────────────────── browser (Playwright) ─────────────────────────────
def chromium_path() -> str | None:
    if os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"):
        return os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]
    base = pathlib.Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    for cand in sorted(base.glob("chromium*/chrome-linux*/chrome")) + sorted(base.glob("chromium/chrome")):
        return str(cand)
    return None   # let Playwright use its own managed browser (e.g. in CI after `playwright install`)


class Browser:
    """Context manager: `with Browser() as b: page = b.page()` — a real Chromium, headless."""
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        kw = {"headless": True, "args": ["--no-sandbox"]}
        exe = chromium_path()
        if exe:
            kw["executable_path"] = exe
        self._b = self._pw.chromium.launch(**kw)
        return self

    def page(self, width: int = 1280, height: int = 900):
        ctx = self._b.new_context(viewport={"width": width, "height": height})
        p = ctx.new_page()
        p.set_default_timeout(20000)
        return p

    def __exit__(self, *a):
        try:
            self._b.close()
        finally:
            self._pw.stop()


def shot(page, name: str) -> str:
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    return str(path)
