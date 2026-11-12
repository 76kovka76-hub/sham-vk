"""AI Horde: free, volunteer-powered image generator for SHAM.

Four of the 96 scheduled UTC slots use photorealistic *fictional* people.
The other 92 use anime aesthetics. No Openverse or cartoon fallback.
The volunteer queue is best-effort and may fail or time out.
"""
import base64
import hashlib
import io
import json
import os
import random
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageOps

API = "https://aihorde.net/api/v2"
CLIENT_AGENT = "SHAM-VK:1.0:https://github.com/76kovka76-hub/sham-vk"
NEGATIVE = (
    "low quality, lowres, worst quality, blurry, watermark, logo, subtitles, "
    "text, letters, cropped face, disfigured, extra fingers, bad hands, "
    "deformed features, multiple faces fused, uncanny, violence, gore, nudity"
)
SCENES = {
    "work": "in a modern office looking at a laptop and a mountain of paperwork",
    "wallet": "at a supermarket checkout shocked by the grocery total and holding a wallet",
    "phone": "lying on a sofa at night scrolling a smartphone past bedtime",
    "home": "standing in a kitchen looking in an almost empty refrigerator",
    "social": "reading a shocking message on a smartphone while sitting in a cafe",
    "life": "sitting in pajamas at a breakfast table facing a ridiculously early morning",
}
REACTIONS = [
    "comically surprised, mouth open, wide expressive eyes",
    "exhausted, resigned, deeply unimpressed",
    "trying not to laugh, eyebrows raised",
    "dramatically shocked, incredulous",
    "facepalm, frustrated but funny",
]


def style_for_slot(slot: str) -> str:
    """Four realistic pictures/day, at UTC 00:00, 06:00, 12:00, 18:00 slots."""
    try:
        date, hour, quarter = slot.rsplit("-", 2)
        if len(date) != 10 or not (0 <= int(hour) < 24) or not (0 <= int(quarter) < 4):
            raise ValueError("Invalid UTC slot")
        return "realistic" if int(hour) % 6 == 0 and int(quarter) == 0 else "anime"
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"Bad SHAM slot: {slot!r}") from exc


def build_prompt(post, slot, style):
    rnd = random.Random("SHAM-characters-" + slot)
    scene = SCENES.get(post.get("scene"), SCENES["life"])
    reaction = rnd.choice(REACTIONS)
    person = rnd.choice([
        "young adult man with dark short hair",
        "young adult woman with wavy brown hair",
        "adult man with curly hair",
        "adult woman with short black hair",
        "adult man with long brown hair tied back",
        "adult woman with a messy bun",
    ])
    common = (
        f"An original fictional {person}, {scene}, {reaction}. "
        "One clearly visible adult human face, expressive facial features, "
        "memorable comic reaction, scene tells a joke without any writing, "
        "cinematic dynamic composition, waist-up medium shot, subject centered, "
        "clear face with open space top and bottom for later meme captions, "
        "safe for work, no visible letters, no signatures."
    )
    if style == "realistic":
        return (
            "Hyperrealistic editorial photography, candid 35mm photography, "
            "natural human skin texture, highly realistic fictional person, "
            "professional lighting, rich colors, sharp focus. " + common
        )
    if style == "anime":
        return (
            "High quality hand-drawn Japanese anime illustration, polished anime "
            "character design, expressive anime eyes and facial emotions, vivid "
            "clean cel shading, detailed anime background, cinematic lighting, "
            "authentic 2D animation film frame. " + common
        )
    raise ValueError("SHAM only supports anime and realistic styles")


def _json(response):
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("AI Horde response is not a JSON object")
    return payload


def _download(generation):
    image_url = generation.get("img")
    if not isinstance(image_url, str):
        raise RuntimeError("AI Horde did not return an image URL")
    if image_url.startswith("data:image/") and ";base64," in image_url:
        raw = base64.b64decode(image_url.partition(";base64,")[2])
    elif urlparse(image_url).scheme == "https":
        response = requests.get(image_url, stream=True, timeout=55)
        try:
            response.raise_for_status()
            if urlparse(response.url).scheme != "https":
                raise RuntimeError("AI Horde image redirected to insecure URL")
            total = 0
            chunks = []
            for chunk in response.iter_content(65536):
                total += len(chunk)
                if total > 15 * 1024 * 1024:
                    raise RuntimeError("AI Horde image is too large")
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            response.close()
    else:
        raise RuntimeError("AI Horde image URL is not HTTPS")
    with Image.open(io.BytesIO(raw)) as im:
        if im.format not in ("JPEG", "PNG", "WEBP"):
            raise RuntimeError("Unsupported AI Horde image format")
        if min(im.size) < 384:
            raise RuntimeError("AI Horde image resolution is too low")
        return ImageOps.exif_transpose(im).convert("RGB")


def generate_image(post, slot, style, deadline_seconds=370):
    token = os.getenv("AIHORDE_API_KEY", "").strip() or "0000000000"
    prompt = build_prompt(post, slot, style)
    headers = {"apikey": token, "Client-Agent": CLIENT_AGENT}
    seed = int(hashlib.sha256(slot.encode()).hexdigest()[:8], 16)
    payload = {
        "prompt": prompt + " ### " + NEGATIVE,
        "params": {"width": 512, "height": 512, "steps": 20,
                   "n": 1, "cfg_scale": 7.5, "sampler_name": "k_euler_a",
                   "seed": str(seed)},
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
        "shared": False,
        "replacement_filter": True,
    }
    request = requests.post(API + "/generate/async", headers=headers,
                            json=payload, timeout=45)
    accepted = _json(request)
    request_id = accepted.get("id")
    if not isinstance(request_id, str) or not request_id:
        raise RuntimeError("AI Horde did not accept image generation: " + str(accepted)[:350])
    stop_at = time.monotonic() + deadline_seconds
    try:
        while time.monotonic() < stop_at:
            time.sleep(9)
            check = _json(requests.get(API + "/generate/check/" + request_id, timeout=30))
            if check.get("faulted") or check.get("is_possible") is False:
                raise RuntimeError("AI Horde generation faulted or unavailable")
            if not check.get("done"):
                continue
            status = _json(requests.get(API + "/generate/status/" + request_id, timeout=40))
            choices = status.get("generations") or []
            if not choices:
                raise RuntimeError("AI Horde completed without an image")
            result = choices[0]
            if result.get("censored"):
                raise RuntimeError("AI Horde censored the image; no VK post will be sent")
            image = _download(result)
            return image, {
                "service": "ai_horde", "style": style, "request_id": request_id,
                "model": result.get("model"), "seed": result.get("seed"),
                "worker": result.get("worker_name"),
            }
        raise RuntimeError("AI Horde generation queue timeout; no low-quality fallback")
    finally:
        # Best-effort cleanup prevents a timed-out anonymous job lingering in the queue.
        # Do not cancel a result that was already returned successfully.
        if time.monotonic() >= stop_at:
            try:
                requests.delete(API + "/generate/status/" + request_id,
                                headers=headers, timeout=15)
            except requests.RequestException:
                pass


def make_horde_image(post, slot, out: Path, font, centered_text):
    style = style_for_slot(slot)
    original, metadata = generate_image(post, slot, style)
    image = ImageOps.fit(original, (1080, 1080),
                         method=Image.Resampling.LANCZOS,
                         centering=(0.5, 0.48)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(270):
        strength = max(0, int(215 * (1 - y / 285)))
        d.line((0, y, 1079, y), fill=(2, 2, 8, strength))
    for y in range(805, 1080):
        strength = min(245, int(210 * ((y - 805) / 275) + 35))
        d.line((0, y, 1079, y), fill=(2, 2, 8, strength))
    image = Image.alpha_composite(image, overlay)
    d = ImageDraw.Draw(image)
    centered_text(d, post["top"], 18, 255, (255, 255, 255, 255), 72)
    centered_text(d, post["bottom"], 812, 1018, (255, 228, 45, 255), 72)
    d.text((540, 1054), "SHAM", font=font(29), anchor="mm",
           fill=(238, 238, 238, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    out.mkdir(parents=True, exist_ok=True)
    path = out / "sham_meme.png"
    image.convert("RGB").save(path, "PNG", optimize=True)
    (out / "image_source.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
