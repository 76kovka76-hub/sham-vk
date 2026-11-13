"""VediSMM durable queue for editorially-approved SKRBL 2–4 panel comics.

Dry-run is always safe. Live scheduling requires BOTH an explicit env opt-in
and a human-approved, verified unique comic asset. Never targets SHAM.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

from publish_test import BASE, _data, _target_account
from queue_planner import LEDGER_PATH, load_manifest, load_state, next_slot, preview, select_approved


def _etag(resp, post):
    etag = resp.headers.get("ETag", "")
    if not etag:
        raise RuntimeError("VediSMM returned no draft ETag")
    if etag.startswith('W/"v') and etag.endswith('"'):
        if etag[2:] == f'"v{post.get("version")}"':
            return etag[2:]
        raise RuntimeError("VediSMM version/ETag mismatch")
    return etag


def schedule_one():
    if os.getenv("SKRBL_ENABLE_AUTOPUBLISH", "") != "true":
        print("SKRBL autopublishing is OFF; no VK changes")
        return
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN missing")
    state = load_state()
    if state.get("group_id") != "243241856":
        raise RuntimeError("Unexpected VK group_id: refusing to publish")
    manifest = load_manifest()
    slot, at = next_slot(state)
    if slot is None:
        print("SKRBL next 12-hour buffer already reserved")
        return
    selected, path = select_approved(manifest, state)
    if selected is None:
        print("::warning::SKRBL has no approved unused 2–4 panel comic; skipping slot")
        return
    print("SKRBL slot:", slot)
    print("SKRBL time:", at.isoformat())
    print("SKRBL editorial-approved comic:", selected["id"])

    headers = {"Authorization": "Bearer " + token}
    account_id = _target_account(headers)
    if not account_id:
        raise RuntimeError("SKRBL group is not linked")
    with path.open("rb") as source:
        media_response = requests.post(
            BASE + "/media", headers=headers,
            files={"file": (path.name, source, "image/png")}, timeout=100)
    media = _data(media_response, 201)
    if media.get("status") != "ready" or media.get("type") != "image":
        raise RuntimeError("VediSMM rejected image; no draft created")
    mid = int(media.get("id") or 0)
    if mid <= 0:
        raise RuntimeError("Missing uploaded media ID")
    # Stable on slot AND asset ID. On an uncertain failure, stop and inspect the
    # remote draft manually rather than silently sending another image.
    idempotency = "skrbl-schedule-v1-" + slot + "-" + selected["id"]
    draft_resp = requests.post(
        BASE + "/posts",
        headers={**headers, "Idempotency-Key": idempotency},
        json={"title": "SKRBL " + slot + " " + selected["id"],
              "content": selected["caption"],
              "account_ids": [account_id], "media_ids": [mid]},
        timeout=45)
    draft = _data(draft_resp, 201)
    pid = int(draft.get("id") or 0)
    if not pid or draft.get("status") != "draft" or not draft.get("media"):
        raise RuntimeError("SKRBL draft was not confirmed ready with image")
    etag = _etag(draft_resp, draft)
    when = at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    resp = requests.post(
        BASE + f"/posts/{pid}/schedule",
        headers={**headers, "If-Match": etag},
        json={"scheduled_at": when}, timeout=45)
    scheduled = _data(resp, 200)
    if scheduled.get("id") != pid or scheduled.get("status") != "scheduled":
        raise RuntimeError("VediSMM did not confirm scheduled SKRBL post")
    entry = {"slot": slot, "scheduled_at": when, "asset_id": selected["id"],
             "sha256": selected["sha256"], "post_id": pid,
             "status": "scheduled", "group_id": "243241856"}
    state["entries"].append(entry)
    LEDGER_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("SKRBL_SCHEDULED:", json.dumps(entry, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enqueue", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if args.enqueue == args.preview:
        parser.error("Choose exactly --enqueue or --preview")
    if args.preview:
        preview()
    else:
        schedule_one()
