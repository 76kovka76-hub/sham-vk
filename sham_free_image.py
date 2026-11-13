"""Entirely free anonymous SDXL image generator for SHAM.

Uses the OVHcloud free public endpoint without any API key or billing.
Supports SHAM's broad visual genre rotation and its coherent
joke/punchline bank. The web image is ALWAYS generated for the original meme;
no unlicensed stock photos, random scraped pictures or text-only fallback.
"""
import base64
import io
import os
import time

import requests
from PIL import Image
from horde_style import build_prompt
from style_catalog import STYLE_PROMPTS

API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/images/generations"
MODEL="stabilityai/stable-diffusion-xl-base-1.0"

def generate_image(post,slot,style):
    if style not in STYLE_PROMPTS:
        raise ValueError("Unknown SHAM visual genre: " + str(style))
    # SDXL sees the exact physical joke scene at the beginning of the prompt.
    prompt = build_prompt(post, slot, style)
    photo_only = os.getenv("SHAM_PHOTO_ONLY", "").lower() in ("true", "1", "yes")
    intro = (
        "RAW REAL-WORLD PHOTOGRAPH captured with a DSLR camera and natural optical lens. "
        "Life-like real actors, physical surfaces, believable environments, photographic lighting. "
        "A surreal situation staged with physical props for editorial photojournalism: "
        if photo_only else "Original humorous visual for a Russian meme. "
    )
    prompt = (
        intro
        + prompt
        + " Make the scene funny and visually self-explanatory. "
        + "No embedded text, no labels, no watermarks."
    )[:3200]
    request=requests.post(
        API,
        json={"model":MODEL,"prompt":prompt,"size":"1024x1024","n":1},
        headers={"Content-Type":"application/json","Accept":"application/json"},
        timeout=145,
    )
    if request.status_code in (401,402,403,429):
        raise RuntimeError("OVH free endpoint unavailable; HTTP "+str(request.status_code))
    request.raise_for_status()
    body=request.json()
    data=body.get("data") or []
    if not isinstance(data,list) or not data or not isinstance(data[0],dict):
        raise RuntimeError("OVH free SDXL returned no image")
    encoded=data[0].get("b64_json")
    if not isinstance(encoded,str):
        raise RuntimeError("OVH free SDXL did not return base64 image")
    raw=base64.b64decode(encoded,validate=True)
    if len(raw)>20*1024*1024 or len(raw)<10000:
        raise RuntimeError("OVH free SDXL image byte count out of range")
    with Image.open(io.BytesIO(raw)) as img:
        if min(img.size)<512:
            raise RuntimeError("OVH free image too small")
        artwork=img.convert("RGB")
    return artwork,{"service":"ovh_free_sdxl","style":style,"model":MODEL,
                    "prompt_scene":(post.get("visual") or "").strip()}
