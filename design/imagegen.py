"""Sovereign local image generation — the 'Design' parity (opt-in).

Claude's Design/image features, done on YOUR box: text-to-image against a LOCAL Stable-Diffusion
server (AUTOMATIC1111 or ComfyUI), so prompts and outputs never leave the machine. No API key, no
cloud, ₹0 recurring. This module is the CLIENT + a thin saver; the model server itself is an
opt-in compose service (profile `design`) that only matters if you enable it — it never affects
default startup.

Honest constraints: a real SDXL-class model wants a GPU; on a CPU-only laptop generation is slow.
That is why this ships as opt-in and the image server is NOT in the default profiles.

Design for testability: the HTTP call and the clock are injected, so request-building, response
parsing and PNG saving are unit-tested OFFLINE with zero network and a tiny fake image.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

OUT_DIR = Path(__file__).resolve().parent / "out"
DEFAULT_A1111 = os.environ.get("IMAGE_API_URL", "http://localhost:7860")

# backend -> (path, request-builder, response-extractor)
Poster = Callable[[str, dict], dict]   # (url, json_body) -> parsed json


def _a1111_body(prompt: str, negative: str, width: int, height: int, steps: int) -> dict:
    return {"prompt": prompt, "negative_prompt": negative, "width": width, "height": height,
            "steps": steps, "sampler_name": "DPM++ 2M", "cfg_scale": 7}


def _a1111_images(resp: dict) -> list[str]:
    # A1111 returns {"images": ["<base64 png>", ...]}
    return list(resp.get("images") or [])


def _save_png(b64: str, path: Path) -> Path:
    try:
        raw = base64.b64decode(b64.split(",", 1)[-1], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"image is not valid base64 ({exc})")
    if not raw:
        raise ValueError("decoded image is empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def generate(prompt: str, *, negative: str = "", width: int = 768, height: int = 768,
             steps: int = 25, base_url: Optional[str] = None, backend: str = "a1111",
             out_dir: Optional[Path] = None, poster: Optional[Poster] = None,
             now: Optional[float] = None) -> dict:
    """Generate image(s) from a prompt against a local SD server. Saves PNGs under design/out and
    returns their paths. `poster(url, body) -> json` is injected (httpx in production, a fake in
    tests). Only the A1111 txt2img contract is wired today; the seam is ready for ComfyUI."""
    if not prompt.strip():
        raise ValueError("prompt is empty")
    if backend != "a1111":
        raise ValueError(f"backend '{backend}' not supported yet (a1111 only)")
    base = (base_url or DEFAULT_A1111).rstrip("/")
    body = _a1111_body(prompt, negative, width, height, steps)
    poster = poster or _default_poster
    resp = poster(base + "/sdapi/v1/txt2img", body)
    images = _a1111_images(resp)
    if not images:
        return {"ok": False, "error": "server returned no images", "saved": []}
    out = Path(out_dir) if out_dir else OUT_DIR
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime(now if now is not None else time.time()))
    uniq = uuid.uuid4().hex[:6]      # avoids clobbering across same-second runs
    saved = []
    for i, b64 in enumerate(images):
        p = out / f"{stamp}-{uniq}-{i}.png"
        saved.append(str(_save_png(b64, p)))
    return {"ok": True, "saved": saved, "count": len(saved),
            "prompt": prompt, "backend": backend, "server": base}


def _default_poster(url: str, body: dict) -> dict:
    import httpx
    with httpx.Client(timeout=600.0) as c:   # image gen is slow, esp. on CPU
        r = c.post(url, json=body)
        r.raise_for_status()
        return r.json()


def main(argv=None) -> int:
    import argparse
    import sys
    ap = argparse.ArgumentParser(prog="design.imagegen",
                                 description="Sovereign local text-to-image (opt-in; needs a local SD server).")
    ap.add_argument("prompt")
    ap.add_argument("--negative", default="")
    ap.add_argument("--width", type=int, default=768)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--url", default=None, help=f"SD server (default {DEFAULT_A1111})")
    args = ap.parse_args(argv)
    try:
        res = generate(args.prompt, negative=args.negative, width=args.width,
                       height=args.height, steps=args.steps, base_url=args.url)
    except Exception as exc:  # noqa: BLE001
        print(f"image generation failed: {exc}\n"
              "Is the local image server running?  docker compose -f local/compose/docker-compose.yml "
              "-f local/compose/design.yml --profile design up -d  (needs a GPU for usable speed)",
              file=sys.stderr)
        return 1
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
