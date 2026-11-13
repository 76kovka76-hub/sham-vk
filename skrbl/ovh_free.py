"""Probe a no-key, published-free OVHcloud SDXL endpoint for SKRBL.

OVHcloud officially lists SDXL 1.0 as Free with 2 anonymous requests/minute
per IP; this module has NO paid fallback and NO API key or credit card.
Requires a real preview to be accepted before publishing any output.
"""
import argparse
import base64
import io
import json
import os
import threading
import time
from pathlib import Path

import requests
from PIL import Image

from free_horde_test import PANELS, ROOT, make_comic

API = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/images/generations"
MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
SPACING_SECONDS = 36  # Below official anonymous 2/minute limit, per IP.
lock = threading.Lock()
next_request_at = 0.0

STYLE = (
    "Single scene from a connected four-frame funny hand-drawn rough pencil "
    "comic series on slightly stained off-white paper. Original intentionally "
    "crooked amateur black ink and graphite sketch; dense chaotic hand hatching, "
    "ugly goofy expressive human faces, huge uneven wide eyes, ragged scribble "
    "hair, crooked teeth, exaggerated action and gestures. Funny visual slapstick "
    "with lots of tiny props in a densely detailed background. Sketchbook cartoon "
    "with subtle blue-gray penciled clothing and occasional red pencil eyelids. "
    "SAME exhausted, scruffy black-spiky-haired adult man in loose striped blue "
    "pajamas throughout the sequence, but vary facial expression and pose with "
    "the story. Off-kilter amateur ballpoint pen drawing, NOT anime, NOT "
    "photorealistic, NOT vector art, NOT smooth digital painting, NO embedded "
    "words or captions, no lettering, no speech bubbles, no logos, safe for work."
)


def _one_request(prompt):
    global next_request_at
    with lock:
        delay = next_request_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        # Rate-limit starts, not completions. The host IP is shared,
        # so 429 errors can still happen if others use the free endpoint.
        next_request_at = time.monotonic() + SPACING_SECONDS
        r = requests.post(
            API,
            json={"model": MODEL, "prompt": prompt, "size": "1024x1024", "n": 1},
            headers={"accept": "application/json", "Content-Type":"application/json"},
            timeout=160,
        )
    if r.status_code == 429:
        raise RuntimeError("OVH_FREE_RATE_LIMIT_429: Shared anonymous IP limited; no fallback")
    if r.status_code in (401, 402, 403):
        raise RuntimeError("OVH_FREE_UNAVAILABLE: Anonymous SDXL refused access (HTTP "
                           + str(r.status_code) + "); no paid fallback")
    r.raise_for_status()
    data = r.json()
    choices = data.get("data") or []
    if not choices or not isinstance(choices[0], dict):
        raise RuntimeError("No image from free OVH SDXL")
    b64 = choices[0].get("b64_json")
    if not isinstance(b64, str) or not b64:
        raise RuntimeError("OVH SDXL returned no b64_json image")
    raw = base64.b64decode(b64, validate=True)
    if len(raw) > 20_000_000:
        raise RuntimeError("OVH image too large")
    with Image.open(io.BytesIO(raw)) as im:
        image = im.convert("RGB")
    if min(image.size) < 512:
        raise RuntimeError("OVH SDXL low-resolution image rejected")
    return image


def generate_frame(index, panel):
    prompt = STYLE + " Scene action: " + panel["prompt"] + (
        ". Detailed black graphite hatching and DIY pen lines, "
        "physical comedy, show all background objects, no text."
    )
    image = _one_request(prompt)
    print("SKRBL_OVH_FRAME_READY:", index + 1, image.size, flush=True)
    return index, image, {"provider":"OVHcloud anonymous SDXL", "model": MODEL}


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true", help="One free frame to verify service")
    parser.add_argument("--preview", action="store_true", help="Four-frame complete comic")
    args=parser.parse_args()
    if args.probe == args.preview:
        parser.error("Choose one mode")
    if args.probe:
        _, img, meta = generate_frame(0, PANELS[0])
        out = ROOT / "ovh_probe.png"
        img.save(out)
        print("SKRBL_OVH_PROBE_READY:", out, flush=True)
    else:
        image_path=make_comic(frame_provider=generate_frame)
        print("SKRBL_OVH_FREE_COMIC_READY:", image_path, flush=True)
