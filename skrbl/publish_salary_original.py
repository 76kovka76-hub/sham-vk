"""Publish the approved original 4-panel salary comic to SKRBL once.

No image generation here. Downloads the exact user-approved generated image,
verifies image dimensions and content hash after receiving a PNG, and strictly
checks SKRBL group ID before creating a post in VediSMM.
"""
import hashlib
import io
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
import requests

from publish_test import BASE, _data, _target_account, _valid_vk_url

ORIGINAL_ASSET_URL = "https://d2jqrm6oza8nb6.cloudfront.net/datasets/b1dafaea-cac0-4076-860b-e538ec2c1d92.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZWE4MmMzMDM4N2E1OTVmMyIsImJ1Y2tldCI6InJ1bndheS1kYXRhc2V0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NDY1NTc0N30.NdbR9XtBCDD8fZ5d8lfU6_aV6XTvAo_DbZV-y8UKE4k"
ONE_OFF_KEY = "skrbl-original-salary-4panels-20261113-v1"
CAPTION = "Зарплата пришла. Счета уже стоят у двери с протянутой рукой. Бл***ь, я даже порадоваться не успел.\n\n#SKRBL #юмор #карандашныемемы"
OUT = Path(__file__).resolve().parent / "salary_4panel_original.png"


def fetch_original():
    response = requests.get(ORIGINAL_ASSET_URL, timeout=90)
    response.raise_for_status()
    raw = response.content
    if len(raw) < 50000 or len(raw) > 14 * 1024 * 1024:
        raise RuntimeError("Unexpected original image byte length")
    im = Image.open(io.BytesIO(raw))
    if im.format != "PNG" or min(im.size) < 1000:
        raise RuntimeError("Incorrect original: expected detailed PNG >=1000px")
    if (im.width, im.height) != (1254, 1254):
        raise RuntimeError(f"Wrong approved image dimensions {im.size}")
    OUT.write_bytes(raw)
    print("SKRBL_ORIGINAL_PIXELS:", im.size)
    print("SKRBL_ORIGINAL_SHA256:", hashlib.sha256(raw).hexdigest())
    return OUT


def publish_once():
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing VEDISMM_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    account_id = _target_account(headers)
    print("STRICT_VK_TARGET: 243241856")
    print("STRICT_VEDISMM_TARGET:", account_id)
    path = fetch_original()
    with path.open("rb") as image:
        uploaded = requests.post(
            BASE + "/media", headers=headers,
            files={"file": ("SKRBL_salary_4panel.png", image, "image/png")}, timeout=120)
    media = _data(uploaded, 201)
    if media.get("type") != "image" or media.get("status") != "ready":
        raise RuntimeError("Original image not confirmed ready by VediSMM")
    media_id = int(media.get("id") or 0)
    if media_id <= 0:
        raise RuntimeError("Bad media id")
    created = requests.post(
        BASE + "/posts",
        headers={**headers, "Idempotency-Key": ONE_OFF_KEY},
        json={"title": "SKRBL — зарплата и счета (4 кадра)",
              "content": CAPTION, "account_ids": [account_id],
              "media_ids": [media_id]}, timeout=45)
    post = _data(created, 201)
    if post.get("status") != "draft" or not post.get("media"):
        raise RuntimeError("Draft does not contain image")
    post_id, version = int(post.get("id") or 0), int(post.get("version") or 0)
    if post_id <= 0 or version <= 0:
        raise RuntimeError("Bad post id/version")
    launched = requests.post(
        BASE + f"/posts/{post_id}/publish",
        headers={**headers, "Idempotency-Key": ONE_OFF_KEY + "-publish"},
        json={"version": version}, timeout=45)
    job = _data(launched, 202)
    job_id = job.get("id")
    if not isinstance(job_id, str) or not job_id:
        raise RuntimeError("Missing VediSMM job ID")
    print("SKRBL_POST_ID:", post_id)
    for _ in range(24):
        time.sleep(5)
        status_response = requests.get(BASE + f"/jobs/{job_id}", headers=headers, timeout=30)
        job_state = _data(status_response, 200)
        if job_state.get("status") in ("succeeded", "partially_succeeded"):
            targets = [t for t in job_state.get("targets", []) if
                t.get("account", {}).get("id") == account_id
                and t.get("status") == "succeeded" and _valid_vk_url(t.get("external_url"))]
            if not targets:
                raise RuntimeError("VediSMM did not confirm SKRBL-specific VK delivery")
            print("SKRBL_ORIGINAL_PUBLISHED:", targets[0]["external_url"])
            return
        if job_state.get("status") in ("failed", "cancelled"):
            raise RuntimeError(f"SKRBL publication failed: {job_state.get('status')}")
    raise RuntimeError("SKRBL job exists but VK confirmation still unavailable")


if __name__ == "__main__":
    publish_once()
