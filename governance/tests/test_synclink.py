"""The one-tap sync link: correct payload, the right addresses for HTTPS/plain, safe defaults, and a clear failure when sync is not set up."""
import base64
import importlib.util
import json
import pathlib
import sys

import pytest

G = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("securax_synclink", G / "synclink.py")
sl = importlib.util.module_from_spec(spec)
sys.modules["securax_synclink"] = sl
spec.loader.exec_module(sl)


def decode(link):
    frag = link.split("#sync=")[1]
    return json.loads(base64.urlsafe_b64decode(frag + "=" * (-len(frag) % 4)))


def test_https_link_uses_names_and_the_first_token():
    link, where = sl.build({"SYNC_TOKENS": "tokA,tokB", "COMPOSE_FILE": "docker-compose.yml:tls.yml", "SECURAX_DOMAIN": "securax.example.in"}, "me")
    assert link.startswith("https://hub.securax.example.in/#sync=") and where == "https://sync.securax.example.in/sync"
    assert decode(link) == {"url": "https://sync.securax.example.in/sync", "key": "tokA", "user": "me"}


def test_plain_link_uses_the_host_given():
    link, where = sl.build({"SYNC_TOKENS": "t"}, host="100.101.102.103")
    assert link.startswith("http://100.101.102.103:8088/#sync=") and decode(link)["url"] == "http://100.101.102.103:8089/sync"


def test_second_token_and_bad_index():
    assert decode(sl.build({"SYNC_TOKENS": "a,b"}, token_index=1)[0])["key"] == "b"
    with pytest.raises(SystemExit):
        sl.build({"SYNC_TOKENS": "a"}, token_index=3)


def test_no_token_is_a_plain_message_not_a_crash():
    with pytest.raises(SystemExit) as e:
        sl.build({})
    assert "./securax setup" in str(e.value)


def test_token_survives_awkward_characters_and_unicode_user():
    link, _ = sl.build({"SYNC_TOKENS": "a+b/c=d_e-f"}, user="me ✓")
    assert decode(link)["key"] == "a+b/c=d_e-f" and decode(link)["user"] == "me ✓"
    assert "=" not in link.split("#sync=")[1] and "+" not in link.split("#sync=")[1]            # URL-fragment safe
