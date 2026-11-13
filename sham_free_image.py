"""Entirely free anonymous SDXL image generator for SHAM.

Uses the OVHcloud free public endpoint without any API key or billing.
Preserves SHAM's existing 4 realistic / 92 anime UTC slots and its coherent
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

API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/images/generations"
MODEL="stabilityai/stable-diffusion-xl-base-1.0"

def generate_image(post,slot,style):
    if style not in ("anime","realistic"):
        raise ValueError("Only the approved SHAM visual styles are supported")
    prompt=build_prompt(post,slot,style)
    # Explicitly describe a visible physical situation, not only a portrait.
    prefix=(
        "Funny staged cinematic photo of a REALISTIC FICTIONAL adult in an "
        "absurd everyday slapstick situation; highly expressive human face, "
        "believable human skin and lighting. Photographic, not anime. "
        if style=="realistic" else
        "Funny lively anime comedy frame with exaggerated expressions, "
        "comedic physical action, rich environment, expressive animated face. "
        "Illustrated, not photorealistic. "
    )
    # Ask for the exact action and prop FIRST; SDXL can truncate late instructions.
    funny_visual=(post.get("visual") or "").strip()
    prompt=(prefix+"Scene: "+funny_visual+". "+prompt+
            " Funny visible situation, unusual prop or action, one main face, "
            "no embedded captions, no letters, no watermarks, no logos, SFW.")[:3200]
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
                    "prompt_scene":funny_visual}
