"""One-time SKRBL VK smoke test via VediSMM.

Does NOT call the SHAM publisher. Aborts unless the connected target exactly
matches VK group 243241856. Uses an idempotency key fixed for this one post.
"""
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

TARGET = "243241856"
BASE = "https://vedismm.ru/api/v1"
KEY = "skrbl-2026-11-13-first-pencil-test-v1"
ROOT = Path(__file__).resolve().parent
CAPTION = (
    "Зашёл за хлебом. По сумме будто купил пекарню целиком. "
    "Чек: «Ну что, бл***ь, богатый?»\n\n"
    "#SKRBL #юмор #карандашныемемы"
)


def _data(response, expected):
    response.raise_for_status()
    if response.status_code != expected:
        raise RuntimeError(f"VediSMM returned HTTP {response.status_code}; expected {expected}")
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise RuntimeError("Bad VediSMM API response")
    return body["data"]


def _target_account(headers):
    r = requests.get(BASE + "/accounts", headers=headers, timeout=35)
    r.raise_for_status()
    accounts = r.json().get("data")
    if not isinstance(accounts, list):
        raise RuntimeError("VediSMM account list unavailable")
    target = [a for a in accounts if a.get("network") == "vk"
              and str(a.get("external_id", "")).lstrip("-") == TARGET]
    if len(target) != 1 or str(target[0].get("status", "")).lower() != "active":
        raise RuntimeError("SKRBL group 243241856 is not linked and active: no publication attempted")
    return int(target[0]["id"])


def _valid_vk_url(url):
    if not isinstance(url, str):
        return False
    u = urlparse(url)
    return (u.scheme == "https" and
            u.hostname in ("vk.com", "www.vk.com", "vk.ru", "www.vk.ru")
            and re.fullmatch(r"/wall-243241856_\d+", u.path) is not None)


def render_image():
    import cairosvg
    dest = ROOT / "skrbl_test.png"
    source = ROOT / "test_hleb_chek.svg"
    if not source.is_file():
        raise RuntimeError("Missing sketch source")
    svg = source.read_text(encoding="utf-8")
    if "БЛ***Ь" not in svg or "SKRBL" not in svg:
        raise RuntimeError("Missing censored profanity or SKRBL branding on sketch")
    if CAPTION.count("#") != 3 or "бл***ь" not in CAPTION:
        raise RuntimeError("Incorrect caption or profanity masking")
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(dest),
                     output_width=1080, output_height=1080)
    from PIL import Image
    with Image.open(dest) as img:
        if img.size != (1080, 1080):
            raise RuntimeError("Invalid test meme dimensions")
    print("SKRBL_PENCIL_IMAGE_READY:", dest)
    return dest


def publish_one():
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN is not available")
    headers = {"Authorization": f"Bearer {token}"}
    account = _target_account(headers)
    print("CONFIRMED_TARGET_GROUP: vk" + TARGET)
    print("CONFIRMED_TARGET_VEDISMM_ACCOUNT:", account)
    img = render_image()
    with img.open("rb") as src:
        upload = requests.post(
            BASE + "/media", headers=headers,
            files={"file": ("SKRBL_test.png", src, "image/png")}, timeout=90)
    media = _data(upload, 201)
    mid = int(media.get("id") or 0)
    if mid < 1 or media.get("type") != "image" or media.get("status") != "ready":
        raise RuntimeError("Image upload not confirmed; no post created")
    draft = requests.post(
        BASE + "/posts",
        headers={**headers, "Idempotency-Key": KEY},
        json={"title": "SKRBL — первый карандашный мем (тест)",
              "content": CAPTION,
              "account_ids": [account], "media_ids": [mid]},
        timeout=45)
    post = _data(draft, 201)
    pid = int(post.get("id") or 0)
    version = int(post.get("version") or 0)
    if pid <= 0 or version <= 0 or post.get("status") != "draft" or not post.get("media"):
        raise RuntimeError("VediSMM draft missing an image or version")
    publish = requests.post(
        BASE + f"/posts/{pid}/publish",
        headers={**headers, "Idempotency-Key": KEY + "-publish"},
        json={"version": version}, timeout=45)
    job = _data(publish, 202)
    jid = job.get("id")
    if not isinstance(jid, str) or not jid:
        raise RuntimeError("VediSMM did not return a publication job")
    print("SKRBL_VEDISMM_POST_ID:", pid)
    print("SKRBL_VEDISMM_JOB_ID:", jid)
    for attempt in range(24):
        time.sleep(5)
        r = requests.get(BASE + f"/jobs/{jid}", headers=headers, timeout=30)
        state = _data(r, 200)
        status = state.get("status")
        if status in ("succeeded", "partially_succeeded"):
            good = [t for t in state.get("targets", [])
                    if t.get("account", {}).get("id") == account
                    and t.get("status") == "succeeded"
                    and _valid_vk_url(t.get("external_url"))]
            if not good:
                raise RuntimeError("VediSMM did not confirm VK SKRBL delivery")
            url = good[0]["external_url"]
            print("SKRBL_PUBLISHED_URL:", url)
            (ROOT / "test_result.json").write_text(
                json.dumps({"post_id": pid, "group_id": TARGET, "url": url},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            return
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"SKRBL publication failed: {status}")
    raise RuntimeError("VediSMM accepted SKRBL job but VK publication was not confirmed in 120s")


if __name__ == "__main__":
    if os.getenv("SKRBL_TEST_MODE") == "publish":
        publish_one()
    else:
        render_image()
        print("Preview only; no VK post created")
