"""Free volunteer image generator for SHAM with diverse visual genres.

The image must depict the specific joke, not a generic smiling anime portrait.
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
from style_catalog import STYLE_PROMPTS, style_for_slot

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
TOPIC_REACTIONS = {
    # A story-specific expression overrides the previous random emotion.
    "typing": "extremely anxious, tense and impatient, eyes fixed on the smartphone, visibly worried eyebrows, mouth closed, NOT smiling",
    "need_talk": "worried and alarmed, eyes wide with anxiety, holding smartphone in the foreground, NOT smiling",
    "date": "nervous and embarrassed on a first date, awkward shy smile, looking at another person",
    "voice_messages": "exasperated and bored, listening intently to phone, eyes rolling",
    "groupchat": "overwhelmed, tired, staring with disbelief at smartphone screen",
    "five_minute_meeting": "exhausted and bored on never-ending video meeting, blank expression",
    "boss_friday": "shocked and annoyed by new work message, furrowed eyebrows",
    "excel": "frustrated and bewildered by spreadsheet on laptop, serious expression",
    "deadline": "stressed and panicked staring at clock and laptop, NOT smiling",
    "after_vacation": "horrified by hundreds of unread emails, startled and exhausted",
    "salary": "shocked and distraught at small bank balance on phone, NOT smiling",
    "grocery_total": "in disbelief at expensive grocery receipt, worried surprised face",
    "discount": "surprised and conflicted about shopping bags and sale signs",
    "rent": "stunned and worried by expensive rental listing on laptop",
    "subscriptions": "annoyed and disappointed while reviewing charges on phone",
    "scrolling": "exhausted and sleepy while compulsively scrolling phone in dark bedroom",
    "battery": "desperately anxious, staring at smartphone battery dying, NOT smiling",
    "screen_time": "ashamed and shocked by huge phone usage hours",
    "photo_gallery": "embarrassed and cringing while looking at old photo on phone",
    "notifications": "overwhelmed by constant buzzing phone, exhausted",
    "fridge": "hungry and disappointed in nearly empty refrigerator",
    "dishes": "deeply exhausted staring at huge mountain of dirty dishes",
    "cleaning": "tired and annoyed surrounded by household clutter",
    "socks": "puzzled and suspicious holding one unpaired sock",
    "delivery": "hungry and impatient tracking food delivery on phone",
    "alarm": "sleepy and grumpy, tired eyes, reaching for buzzing alarm",
    "weekend": "disappointed and exhausted on Sunday night",
    "adult_bills": "stressed and weary reading utility bills at kitchen table",
    "fitness": "tired and sore after first workout, comically exhausted",
    "to_do": "overwhelmed and worried by extremely long to-do list",
}
SCENE_REACTIONS = {
    "work": "visibly tired and frustrated",
    "wallet": "shocked by prices and finances",
    "phone": "tired and focused on smartphone",
    "home": "exhausted by household chores",
    "social": "anxious and nervous reading messages on phone",
    "life": "grumpy and overwhelmed by ordinary life",
}



def build_prompt(post, slot, style):
    if style not in STYLE_PROMPTS:
        raise ValueError("Unknown SHAM visual genre: " + str(style))
    rng = random.Random("SHAM-characters-" + slot)
    from visual_gags import get_visual_gag

    # The per-joke scene is indispensable; the topic gag adds physical comedy.
    own_scene = (post.get("visual") or "").strip()
    gag = (get_visual_gag(post) or "").strip()
    scene = own_scene or gag or SCENES.get(post.get("scene"), SCENES["life"])
    if gag and gag != scene:
        scene += ". Additional physical comedy: " + gag
    reaction = TOPIC_REACTIONS.get(
        post.get("topic"),
        SCENE_REACTIONS.get(post.get("scene"), "surprised by the ridiculous situation"),
    )
    person = rng.choice([
        "adult man with dark short hair",
        "adult woman with wavy hair",
        "middle-aged man with curly hair",
        "middle-aged woman with short black hair",
        "elderly person with silver hair",
        "young adult person with messy hair",
        "adult with long braided hair",
        "adult with glasses and expressive eyebrows",
        "fictional adult in ordinary work clothes",
    ])
    framing = rng.choice([
        "dynamic wide shot showing environment and all essential props",
        "candid eye-level medium shot with the main action clearly visible",
        "dramatic low-angle view of the ridiculous event",
        "over-the-shoulder view of the comic situation",
        "off-center documentary-style composition with visible physical action",
    ])
    return (
        STYLE_PROMPTS[style] + " "
        "SPECIFIC JOKE TO DEPICT: " + scene + ". "
        "When people are required, use an original fictional " + person + ". "
        "When the action instead centers on animals or objects, depict those "
        "without inserting an unrelated human face. "
        "CHARACTER REACTION: " + reaction + ". "
        "CAMERA: " + framing + ". "
        "The image must physically show the exact joke setup and its key props; "
        "the image is not a generic portrait or generic background. "
        "Create one clear readable visual gag. Avoid extra unrelated objects. "
        "Leave clear negative space at top and bottom for separately typeset "
        "Russian meme captions. no visible letters, no embedded captions, "
        "no signs, no signatures, no watermarks. "
        "All human subjects are fictional adults."
    )


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


def make_horde_image(post, slot, out: Path, font, centered_text, style_override=None):
    if style_override is not None and style_override not in STYLE_PROMPTS:
        raise ValueError("Unknown SHAM preview visual genre")
    style = style_override or style_for_slot(slot)
    preferred = os.getenv("SHAM_FREE_IMAGE_PROVIDER", "horde").strip().lower()
    if preferred == "ovh":
        from sham_free_image import generate_image as ovh_free_image
        try:
            original, metadata = ovh_free_image(post, slot, style)
        except (requests.RequestException, ValueError, RuntimeError, OSError) as exc:
            print("::warning::Free OVH failed; using volunteer AI Horde: "
                  + str(exc)[:160], flush=True)
            original, metadata = generate_image(post, slot, style)
    elif preferred == "horde":
        original, metadata = generate_image(post, slot, style)
    else:
        raise ValueError("SHAM_FREE_IMAGE_PROVIDER must be ovh or horde")
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
