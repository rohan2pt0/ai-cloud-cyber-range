"""Local image-gen client — request building, response parsing, PNG saving. All offline."""
import base64

import pytest

from design import imagegen

# a 1x1 transparent PNG, base64 — stands in for a generated image.
_PNG = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9"
        "awAAAABJRU5ErkJggg==")


def test_generate_builds_a1111_request_and_saves_png(tmp_path):
    captured = {}

    def poster(url, body):
        captured["url"] = url
        captured["body"] = body
        return {"images": [_PNG]}

    res = imagegen.generate("an isometric architecture diagram, blue accent",
                            width=512, height=512, steps=20, base_url="http://localhost:7860",
                            out_dir=tmp_path, poster=poster, now=0)
    assert res["ok"] and res["count"] == 1
    assert captured["url"] == "http://localhost:7860/sdapi/v1/txt2img"
    assert captured["body"]["width"] == 512 and captured["body"]["steps"] == 20
    saved = res["saved"][0]
    assert saved.endswith(".png")
    assert base64.b64decode(_PNG) == open(saved, "rb").read()   # exact bytes written


def test_empty_prompt_rejected():
    with pytest.raises(ValueError):
        imagegen.generate("   ", poster=lambda u, b: {"images": [_PNG]})


def test_unsupported_backend_rejected():
    with pytest.raises(ValueError):
        imagegen.generate("x", backend="midjourney", poster=lambda u, b: {})


def test_no_images_returns_not_ok(tmp_path):
    res = imagegen.generate("x", out_dir=tmp_path, poster=lambda u, b: {"images": []})
    assert res["ok"] is False and res["saved"] == []


def test_bad_base64_is_a_clean_error(tmp_path):
    with pytest.raises(ValueError):
        imagegen.generate("x", out_dir=tmp_path, poster=lambda u, b: {"images": ["@@not-base64@@"]})


def test_multiple_images_saved(tmp_path):
    res = imagegen.generate("x", out_dir=tmp_path, poster=lambda u, b: {"images": [_PNG, _PNG]}, now=0)
    assert res["count"] == 2 and len({s for s in res["saved"]}) == 2
