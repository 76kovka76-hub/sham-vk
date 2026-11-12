"""Optional VediSMM publisher for SHAM, using its documented REST API v1.

The workflow never sends a text-only fallback. VediSMM's acceptance of a job
does NOT prove that VK displayed the photo; inspect the target status.
"""
import hashlib
import os
import time
from pathlib import Path

import requests

BASE = "https://vedismm.ru/api/v1"


def _positive_int(value, name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise RuntimeError(f"{name} must be a positive integer") from None
    if number <= 0:
        raise RuntimeError(f"{name} must be a positive integer")
    return number


def _response_data(response, expected):
    response.raise_for_status()
    if response.status_code != expected:
        raise RuntimeError(f"VediSMM HTTP {response.status_code}; expected {expected}: {response.text[:300]}")
    obj = response.json()
    if not isinstance(obj, dict) or not isinstance(obj.get("data"), dict):
        raise RuntimeError("VediSMM returned an invalid API response")
    return obj["data"]


def _find_account_id(token):
    configured = os.getenv("VEDISMM_ACCOUNT_ID", "").strip()
    if configured:
        return _positive_int(configured, "VEDISMM_ACCOUNT_ID")
    response = requests.get(
        BASE + "/accounts", headers={"Authorization": f"Bearer {token}"},
        params={"limit": 100}, timeout=35,
    )
    response.raise_for_status()
    result = response.json().get("data")
    if not isinstance(result, list):
        raise RuntimeError("VediSMM did not return an account list")
    match = [a for a in result if a.get("network") == "vk"
             and str(a.get("external_id", "")).lstrip("-") == "243230846"]
    if len(match) != 1:
        raise RuntimeError(
            "SHAM (VK ID 243230846) must be connected and active in VediSMM. "
            "Otherwise provide VEDISMM_ACCOUNT_ID manually."
        )
    return _positive_int(match[0].get("id"), "VediSMM SHAM account id")


def publish_vedismm(image_path: Path, caption: str, slot: str):
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing VEDISMM_TOKEN (GitHub Actions Secret)")
    account_id = _find_account_id(token)
    headers = {"Authorization": f"Bearer {token}"}
    # Service upload is separate from VK's photos.getWallUploadServer.
    with image_path.open("rb") as src:
        upload = requests.post(
            BASE + "/media", headers=headers,
            files={"file": ("sham.png", src, "image/png")}, timeout=90,
        )
    media = _response_data(upload, 201)
    media_id = _positive_int(media.get("id"), "uploaded VediSMM media id")
    if media.get("type") != "image" or media.get("status") != "ready":
        raise RuntimeError("VediSMM did not confirm a ready image; no post created")

    # A stable per-slot idempotency key prevents two different drafts if
    # an Actions run is repeated after a network interruption.
    key = "sham-" + hashlib.sha256(f"v1:{account_id}:{slot}".encode()).hexdigest()[:48]
    draft = requests.post(
        BASE + "/posts",
        headers={**headers, "Idempotency-Key": key},
        json={"title": f"SHAM {slot}", "content": caption,
              "account_ids": [account_id], "media_ids": [media_id]},
        timeout=45,
    )
    post = _response_data(draft, 201)
    post_id = _positive_int(post.get("id"), "VediSMM post id")
    version = _positive_int(post.get("version"), "VediSMM post version")
    if post.get("status") != "draft" or not post.get("media"):
        raise RuntimeError("VediSMM draft has no attached image; publish cancelled")

    result = requests.post(
        BASE + f"/posts/{post_id}/publish",
        headers={**headers, "Idempotency-Key": key + "-publish"},
        json={"version": version}, timeout=45,
    )
    job = _response_data(result, 202)
    job_id = job.get("id")
    if not isinstance(job_id, str) or not job_id:
        raise RuntimeError("VediSMM accepted a publication but did not return job id")

    # Accepted != published. Check remote VK delivery while the CI runner is up.
    for _ in range(20):
        time.sleep(5)
        status = requests.get(BASE + f"/jobs/{job_id}", headers=headers, timeout=30)
        job_state = _response_data(status, 200)
        state = job_state.get("status")
        if state in ("succeeded", "partially_succeeded"):
            targets = job_state.get("targets", [])
            good = [t for t in targets if t.get("account", {}).get("id") == account_id
                    and t.get("status") == "succeeded" and t.get("external_url")]
            if good:
                return {"post_id": post_id, "job_id": job_id,
                        "status": "published", "url": good[0]["external_url"]}
            raise RuntimeError("VediSMM completed but VK target not confirmed")
        if state in ("failed", "cancelled"):
            raise RuntimeError(f"VediSMM VK publication failed: {job_state.get('error_code') or state}")
    return {"post_id": post_id, "job_id": job_id, "status": "queued",
            "url": ""}  # pending on remote service: do not claim published
