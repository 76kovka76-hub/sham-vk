"""One-time removal of old incoherent scheduled SHAM memes.

Only touches OUR posts recorded in state/history.json and still scheduled in
VediSMM. Never deletes already published posts. Requires strong ETag.
"""
import os
from datetime import datetime, timezone

import requests

from vedismm_publisher import BASE


def clean_legacy_queue(state):
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN required to cancel legacy queue")
    headers = {"Authorization": f"Bearer {token}"}
    removed, skipped, errors = [], [], []
    for item in state.get("posts", []):
        if item.get("publication_status") != "scheduled":
            continue
        if item.get("quality_version", 0) >= 2:
            continue
        pid = item.get("vedismm_post_id")
        if not isinstance(pid, int) or pid <= 0:
            errors.append("Missing VediSMM post ID for old queue item")
            continue
        try:
            response = requests.get(BASE + f"/posts/{pid}", headers=headers, timeout=30)
            response.raise_for_status()
            remote = response.json().get("data")
            if not isinstance(remote, dict) or remote.get("id") != pid:
                raise RuntimeError(f"VediSMM did not return post {pid}")
            status = remote.get("status")
            if status != "scheduled":
                skipped.append({"id": pid, "status": status})
                # Do not pretend an already published post was stopped.
                if status == "published":
                    item["publication_status"] = "delivered_unverified"
                continue
            etag = response.headers.get("ETag")
            if not etag:
                raise RuntimeError(f"VediSMM post {pid} has no ETag")
            unscheduled = requests.post(
                BASE + f"/posts/{pid}/unschedule",
                headers={**headers, "If-Match": etag}, timeout=35
            )
            unscheduled.raise_for_status()
            body = unscheduled.json().get("data")
            if not isinstance(body, dict) or body.get("id") != pid or body.get("status") != "draft":
                raise RuntimeError(f"VediSMM did not confirm post {pid} was unscheduled")
            item["publication_status"] = "unscheduled_low_quality"
            removed.append(pid)
            # Free the slot if future, so the fixed generator may replace it.
            scheduled = item.get("scheduled_at")
            if scheduled and isinstance(scheduled, str):
                at = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                if at.tzinfo and at > datetime.now(timezone.utc):
                    slot = item.get("slot")
                    if slot in state.get("slots", []):
                        state["slots"].remove(slot)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            errors.append(f"VediSMM {pid}: {type(exc).__name__} {exc}")
    return {"unscheduled": removed, "skipped": skipped, "errors": errors}
