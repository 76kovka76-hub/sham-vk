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
        if item.get("quality_version", 0) >= 2 and not item.get("review_rejected", False):
            continue
        pid = item.get("vedismm_post_id")
        if not isinstance(pid, int) or pid <= 0:
            errors.append("Missing VediSMM post ID for old queue item")
            continue
        try:
            # If-Match must match the *current* version. The scheduler can
            # advance it between GET and POST, returning HTTP 412.
            cancelled = False
            remote_status = None
            for attempt in range(3):
                response = requests.get(
                    BASE + f"/posts/{pid}", headers=headers, timeout=30
                )
                response.raise_for_status()
                remote = response.json().get("data")
                if not isinstance(remote, dict) or remote.get("id") != pid:
                    raise RuntimeError(f"VediSMM did not return post {pid}")
                remote_status = remote.get("status")
                if remote_status != "scheduled":
                    break
                etag = response.headers.get("ETag")
                if not etag:
                    raise RuntimeError(f"VediSMM post {pid} has no ETag")
                # The GET endpoint sometimes supplies a weak W/"vN" despite
                # documenting a strong "vN". The API's If-Match requires the
                # strong version tag. Only strip W/ if the returned numeric
                # version exactly matches the embedded version number.
                if etag.startswith('W/"v') and etag.endswith('"'):
                    strong = etag[2:]
                    version = remote.get("version")
                    if strong == f'"v{version}"':
                        etag = strong
                    else:
                        raise RuntimeError(f"VediSMM post {pid} ETag/version mismatch")
                request = requests.post(
                    BASE + f"/posts/{pid}/unschedule",
                    headers={**headers, "If-Match": etag}, timeout=35,
                )
                if request.status_code == 412:
                    if attempt == 2:
                        error_code = ""
                        try:
                            payload = request.json()
                            error_code = payload.get("code") or payload.get("error", {}).get("code", "")
                            error_detail = payload.get("detail", "")
                        except (ValueError, AttributeError):
                            error_detail = ""
                        raise RuntimeError(
                            f"VediSMM {pid} version conflict (HTTP 412) "
                            f"after 3 reads; current_version={remote.get('version')}; "
                            f"etag={etag!r}; code={error_code!r}; "
                            f"detail={error_detail[:140]!r}"
                        )
                    continue
                request.raise_for_status()
                body = request.json().get("data")
                if not isinstance(body, dict) or body.get("id") != pid or body.get("status") != "draft":
                    raise RuntimeError(f"VediSMM did not confirm post {pid} was unscheduled")
                cancelled = True
                break
            if not cancelled:
                skipped.append({"id": pid, "status": remote_status})
                if remote_status == "published":
                    item["publication_status"] = "delivered_unverified"
                continue
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
