"""The hosted Command Center door (doc 131): a static page that finds a machine of yours that is up, so the front door no longer needs a
machine. What is held here: the decisions (run in Node, no page), the page's safety (no inline code, no markup built from data, nothing
from another site), the contract with the node (one path, one sentence), and that it works from a subpath. The real-browser proof, with
simulated machines and the two false-green traps, is in the pull request."""
import json
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOOR = ROOT / "guiding-map" / "command"
CONF = ROOT / "local" / "compose" / "guiding-map.conf"
SERVICE = "securax-command-center"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is needed to run the door's logic")


def _node(js: str):
    code = "const L=require(%s);\n%s" % (json.dumps(str(DOOR / "door-logic.js")), js)
    out = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_addresses_are_checked_before_anything_trusts_them():
    r = _node("""console.log(JSON.stringify([
      L.cleanUrl('https://a.example/'), L.cleanUrl('https://a.example/hub'), L.cleanUrl('https://a.example/x?y=1#z'),
      L.cleanUrl('http://a.example/'), L.cleanUrl('http://localhost:8088'), L.cleanUrl('http://hub.securax.localhost/'),
      L.cleanUrl('https://user:pw@a.example/'), L.cleanUrl('javascript:alert(1)'), L.cleanUrl('ftp://a.example/'), L.cleanUrl(''), L.cleanUrl('not a url')]))""")
    assert r == ["https://a.example/", "https://a.example/hub/", "https://a.example/x/",
                 "", "http://localhost:8088/", "http://hub.securax.localhost/", "", "", "", "", ""]


def test_a_machine_is_cleaned_and_a_list_is_bounded():
    r = _node("""
      const v = L.validateNode({name:'<img src=x onerror=alert(1)>', url:'https://a.example/', role:'weird'});
      const many = []; for (let i = 0; i < 20; i++) many.push({name:'n'+i, url:'https://h'+i+'.example/'});
      many.push({name:'dup', url:'https://h0.example/'}); many.push({name:'bad', url:'http://remote.example/'});
      console.log(JSON.stringify({v: v, n: L.sanitizeList(many).length, none: L.validateNode(null), noName: L.validateNode({url:'https://b.example/'}).name,
                                   notList: L.sanitizeList('x').length}))""")
    assert "<" not in r["v"]["name"] and ">" not in r["v"]["name"]
    assert r["v"]["role"] == "primary"                       # an unknown role is never "standby" by accident
    assert r["n"] == 8                                       # bounded, no duplicates, no plain-http remote machine
    assert r["none"] is None and r["noName"] == "b.example" and r["notList"] == 0


def test_the_best_machine_is_chosen_active_active_then_active_passive():
    r = _node("""
      const n = (name, url, role) => ({name, url, role});
      const A = n('A','https://a/','primary'), B = n('B','https://b/','primary'), S = n('S','https://s/','standby');
      const st = (a, b, s) => ({'https://a/': {up: a[0], ms: a[1]}, 'https://b/': {up: b[0], ms: b[1]}, 'https://s/': {up: s[0], ms: s[1]}});
      const pick = (nodes, state) => { const p = L.pickBest(nodes, state); return [p.node && p.node.name, p.tier]; };
      console.log(JSON.stringify({
        fastest: pick([A,B,S], st([true,90],[true,40],[true,5])),          // two primaries share: the faster; the quicker standby is not used
        order:   pick([A,B,S], st([true,40],[true,40],[true,5])),          // equal speed: the one listed first
        other:   pick([A,B,S], st([false,0],[true,40],[true,5])),          // a primary lost: the other primary
        standby: pick([A,B,S], st([false,0],[false,0],[true,300])),        // no primary: only now the standby
        none:    pick([A,B,S], st([false,0],[false,0],[false,0])),
        unknown: pick([A,B,S], {}),                                         // nothing checked yet is not "up"
        empty:   pick([], {})}))""")
    assert r == {"fastest": ["B", "primary"], "order": ["A", "primary"], "other": ["B", "primary"],
                 "standby": ["S", "standby"], "none": [None, None], "unknown": [None, None], "empty": [None, None]}


def test_a_setup_link_round_trips_and_a_hostile_one_is_ignored():
    r = _node("""
      const nodes = [{name:'Server', url:'https://s.example/', role:'primary'}, {name:'Cloud', url:'https://c.example/', role:'standby'}];
      const frag = L.encodeSetup(nodes), enc = s => Buffer.from(s).toString('base64url');
      console.log(JSON.stringify({
        round: L.parseSetup('#' + frag), roundBare: L.parseSetup(frag),
        garbage: L.parseSetup('#n=AAAA'), wrong: L.parseSetup('#x=' + frag.slice(2)), empty: L.parseSetup(''), nul: L.parseSetup(null),
        evil: L.parseSetup('#n=' + enc(JSON.stringify([{name:'x', url:'javascript:alert(1)'}]))),
        plainHttp: L.parseSetup('#n=' + enc(JSON.stringify([{name:'x', url:'http://remote.example/'}]))),
        proto: L.parseSetup('#n=' + enc('[{"__proto__":{"polluted":1},"url":"https://p.example/"}]')),
        huge: L.parseSetup('#n=' + 'A'.repeat(5000)),
        polluted: ({}).polluted === undefined}))""")
    assert [n["url"] for n in r["round"]] == ["https://s.example/", "https://c.example/"] and r["round"][1]["role"] == "standby"
    assert r["roundBare"] == r["round"]
    for bad in ("garbage", "wrong", "empty", "nul", "evil", "plainHttp", "huge"):
        assert r[bad] is None, bad
    assert r["proto"] and r["proto"][0]["url"] == "https://p.example/" and r["polluted"] is True


def test_the_page_builds_no_markup_from_data_and_loads_nothing_from_elsewhere():
    ui = (DOOR / "door.js").read_text("utf-8") + (DOOR / "door-logic.js").read_text("utf-8")
    for bad in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function", "setTimeout('", 'setTimeout("'):
        assert bad not in ui, f"{bad} must never be used: text from a link or a machine is always set as text"
    html = (DOOR / "index.html").read_text("utf-8")
    assert not re.findall(r"<script(?![^>]*\bsrc=)[^>]*>\s*\S", html), "no inline script: the policy forbids it"
    assert "script-src 'self'" in html and "default-src 'none'" in html and "style-src 'self'" in html
    assert not re.findall(r'(?:src|href)="(?:https?:)?//', html), "nothing is loaded from another site"
    for u in re.findall(r'(?:src|href)="([^"#]+)"', html):
        assert not u.startswith("/"), f"{u}: root-absolute paths break under a subpath"


def test_the_door_and_the_node_agree_on_the_one_sentence():
    """The door believes a machine only when it says exactly this, from the one path; nginx says it."""
    js = (DOOR / "door.js").read_text("utf-8")
    assert "_door.json" in js and SERVICE in js and "j.ok === true" in js
    conf = CONF.read_text("utf-8")
    block = re.search(r"location = /_door\.json \{(.*?)\n    \}", conf, re.S)
    assert block, "the node must serve /_door.json"
    b = block.group(1)
    assert 'add_header Access-Control-Allow-Origin "*" always;' in b          # readable from the hosted page
    assert 'add_header Cache-Control "no-store" always;' in b                  # a status that is never remembered
    assert "return 200 '" + json.dumps({"ok": True, "service": SERVICE}, separators=(",", ":")) + "';" in b
    assert "proxy_pass" not in b and "set $" not in b, "it must answer itself: a proxied answer would say 'up' while a service is down"
    assert conf.count("{") == conf.count("}"), "nginx config braces must balance"


@pytest.mark.skipif(shutil.which("nginx") is None, reason="a real nginx is needed to parse the config")
def test_nginx_accepts_the_node_config(tmp_path):
    conf = tmp_path / "hub.conf"
    conf.write_text(CONF.read_text("utf-8").replace("listen 80;", "listen 127.0.0.1:18081;").replace("root /usr/share/nginx/html;", f"root {tmp_path};"))
    main = tmp_path / "nginx.conf"
    main.write_text(f"pid {tmp_path}/n.pid; error_log {tmp_path}/err.log; events {{}}\n"
                    f"http {{ access_log off; client_body_temp_path {tmp_path}/a; proxy_temp_path {tmp_path}/b; fastcgi_temp_path {tmp_path}/c; "
                    f"uwsgi_temp_path {tmp_path}/d; scgi_temp_path {tmp_path}/e; include {conf}; }}\n")
    out = subprocess.run(["nginx", "-t", "-p", str(tmp_path), "-c", str(main)], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr


def test_the_door_keeps_a_copy_on_the_device_and_never_touches_the_probes():
    sw = (DOOR / "sw.js").read_text("utf-8")
    shell = re.findall(r'"\./([^"]*)"', sw.split("const SHELL = [")[1].split("];")[0])
    for f in shell:
        assert not f or (DOOR / f).exists() or f in ("icon-192.png", "icon-512.png", "serif.woff2"), f"the offline shell names {f}, which is not shipped"  # icons and the serif are copied in at publish (test_pwa_publish checks the shipped shell)
    assert "url.origin !== self.location.origin" in sw, "the probes to your machines are other sites: the worker must pass them through"
    m = json.loads((DOOR / "manifest.json").read_text("utf-8"))
    assert m["start_url"] == "./index.html" and m["scope"] == "./" and m["display"] == "standalone"
