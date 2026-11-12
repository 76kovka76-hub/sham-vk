"""SHAM photographic memes with freely reusable CC0 photos from Openverse.

Photos are third-party photographs, not AI-generated originals. Openverse
license records should be periodically spot-checked against source pages.
A missing photo fails closed; no cartoon or text-only fallback is published.
"""
import hashlib
import io
import json
import random
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageOps

SEARCH_API = "https://api.openverse.org/v1/images/"
QUERIES = {
    "work": [
        "stressed office worker computer", "tired office laptop",
        "woman working computer", "frustrated businessman office",
        "worried employee workplace"],
    "wallet": [
        "surprised man money", "worried man wallet",
        "grocery shopping supermarket", "man bills money",
        "woman surprised shopping"],
    "phone": [
        "man smartphone night", "tired person using phone",
        "young man phone sofa", "woman smartphone bed",
        "man scrolling cellphone"],
    "home": [
        "man refrigerator kitchen", "empty refrigerator kitchen",
        "tired man at home", "man looking at food",
        "man kitchen fridge"],
    "social": [
        "surprised woman phone", "worried man smartphone",
        "man looking at phone", "woman texting smartphone",
        "shocked person reading phone"],
    "life": [
        "tired man morning", "sleepy person sofa",
        "confused man home", "young woman stressed",
        "exhausted person evening"],
}


def _search_photos(query, page):
    response = requests.get(
        SEARCH_API,
        params={"q": query, "license": "cc0", "category": "photograph",
                "page_size": 20, "page": page, "mature": "false"},
        headers={"User-Agent": "SHAM-Meme-Bot/1.0 (https://github.com/76kovka76-hub/sham-vk)"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise RuntimeError("Openverse returned invalid search response")
    return data["results"]


def _download_photo(item):
    for link in (item.get("url"), item.get("thumbnail")):
        if not isinstance(link, str) or urlparse(link).scheme != "https":
            continue
        try:
            response = requests.get(
                link, timeout=30,
                headers={"User-Agent": "SHAM-Meme-Bot/1.0 (https://github.com/76kovka76-hub/sham-vk)"},
                stream=True, allow_redirects=True,
            )
            response.raise_for_status()
            if not response.url.startswith("https://"):
                continue
            size = 0
            chunks = []
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > 9 * 1024 * 1024:
                    raise ValueError("Photo too large")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if len(raw) < 5000:
                continue
            with Image.open(io.BytesIO(raw)) as im:
                if im.format not in ("PNG", "JPEG", "WEBP"):
                    continue
                if min(im.size) < 400:
                    continue
                return ImageOps.exif_transpose(im).convert("RGB")
        except (requests.RequestException, ValueError, OSError):
            continue
        finally:
            try:
                response.close()
            except UnboundLocalError:
                pass
    return None


def choose_photo(post, slot, state):
    queries = QUERIES.get(post.get("scene"), QUERIES["life"])
    rng = random.Random(slot + "-SHAM-photo-v1")
    used = {
        str(p.get("photo_source", {}).get("id"))
        for p in state.get("posts", [])
        if isinstance(p.get("photo_source"), dict)
    }
    search_order = list(queries)
    rng.shuffle(search_order)
    errors = []
    for query in search_order:
        page = rng.randint(1, 4)
        try:
            items = _search_photos(query, page)
        except (ValueError, requests.RequestException) as err:
            errors.append(type(err).__name__)
            continue
        rng.shuffle(items)
        for item in items:
            if not isinstance(item, dict):
                continue
            source_id = str(item.get("id", ""))
            if not source_id or source_id in used:
                continue
            if item.get("license") != "cc0" or item.get("category") != "photograph":
                continue
            if item.get("mature") is True:
                continue
            if min(item.get("width") or 0, item.get("height") or 0) < 700:
                continue
            img = _download_photo(item)
            if img is not None:
                source = {
                    "id": source_id, "title": item.get("title", ""),
                    "creator": item.get("creator", ""),
                    "license": "CC0",
                    "source_url": item.get("foreign_landing_url", ""),
                    "photo_url": item.get("url", ""),
                    "query": query,
                }
                return img, source
    raise RuntimeError(
        "No new usable CC0 photographic meme image available from Openverse; "
        "publication safely cancelled. API issues: " + ",".join(errors[:5])
    )


def make_photo_image(post, slot, state, out, font, centered_text):
    photo, source = choose_photo(post, slot, state)
    out.mkdir(parents=True, exist_ok=True)
    image = ImageOps.fit(photo, (1080, 1080), method=Image.Resampling.LANCZOS,
                         centering=(0.5, 0.48))
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, 245):
        # A readable heading against every photographic background
        alpha = int(195 * (1 - y / 280) + 40)
        d.line((0, y, 1079, y), fill=(4, 4, 7, min(alpha, 240)), width=1)
    for y in range(805, 1080):
        alpha = int(235 * ((y - 805) / 275) + 10)
        d.line((0, y, 1079, y), fill=(2, 2, 6, min(alpha, 245)), width=1)
    image = Image.alpha_composite(image, overlay)
    d = ImageDraw.Draw(image)
    centered_text(d, post["top"], 22, 237, (255, 255, 255, 255), 75)
    centered_text(d, post["bottom"], 833, 1028, (255, 235, 0, 255), 75)
    d.text((540, 1057), "SHAM", font=font(29), anchor="mm",
           fill=(230, 230, 236, 245), stroke_width=2, stroke_fill=(14, 14, 14))
    path = out / "sham_meme.png"
    image.convert("RGB").save(path, "PNG", optimize=True)
    (out / "photo_source.json").write_text(
        json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path
