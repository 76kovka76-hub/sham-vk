"""Image checks performed BEFORE text rendering and BEFORE VediSMM upload.

Cannot prove semantic joke-to-picture alignment without a vision model.
Reject blank/broken/near-identical artwork and keep the original scene
description in generation metadata for a future optional vision review.
"""
from PIL import Image, ImageOps, ImageStat

MIN_SIDE = 512
NEAR_DUPLICATE_BITS = 6


def fingerprint(image):
    """Stable 64-bit difference hash; compares content across resized images."""
    gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
    pix = list(gray.getdata())
    number = 0
    for y in range(8):
        for x in range(8):
            number = (number << 1) | int(pix[y * 9 + x] > pix[y * 9 + x + 1])
    return f"{number:016x}"


def distance(a, b):
    try:
        if len(a) != 16 or len(b) != 16:
            return 64
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except (TypeError, ValueError):
        return 64


def validate_artwork(image, state=None):
    if not isinstance(image, Image.Image) or min(image.size) < MIN_SIDE:
        raise ValueError("SHAM refuses damaged or undersized source image")
    rgb = image.convert("RGB")
    small = rgb.resize((160, 160), Image.Resampling.BILINEAR)
    gray = ImageOps.grayscale(small)
    lightness_std = ImageStat.Stat(gray).stddev[0]
    entropy = gray.entropy()
    if lightness_std < 5.0 or entropy < 2.0:
        raise ValueError("SHAM refuses nearly blank or flat-colour image")
    source_hash = fingerprint(rgb)
    recent = (state or {}).get("posts", [])[-100:]
    for item in recent:
        prior = item.get("image_source") or {}
        known_hash = prior.get("visual_hash") or item.get("visual_hash")
        if isinstance(known_hash, str) and distance(source_hash, known_hash) <= NEAR_DUPLICATE_BITS:
            raise ValueError("SHAM refuses a repeated or near-identical visual")
    return {"visual_hash": source_hash,
            "image_entropy": round(float(entropy), 2),
            "image_luminance_std": round(float(lightness_std), 2),
            "image_qa": "passed_basic_image_checks"}


def validate_joke_visual_brief(post, rendered_prompt):
    """Prompt compliance only, NOT image understanding."""
    scene = (post.get("visual") or "").strip()
    if len(scene.split()) < 6:
        raise ValueError("SHAM visual brief is too generic")
    if scene.lower() not in rendered_prompt.lower():
        raise ValueError("SHAM prompt omitted the exact visual joke scene")
    return True
