"""Read-only hourly reconciliation of SHAM scheduled VediSMM posts.

Do not automatically duplicate failed or manually unscheduled posts.
Only an actual VK wall link can change a post from scheduled to published.
"""
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

from vedismm_publisher import BASE


def _as_utc(value):
    if not value or not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None:
        return None
    return result.astimezone(timezone.utc)


def _vk_post_link(post):
    for target in post.get("targets", []):
        if not isinstance(target, dict):
            continue
        url = target.get("external_url")
        if not isinstance(url, str):
            continue
        parsed = urlparse(url)
        if (parsed.scheme == "https"
                and parsed.hostname in ("vk.com", "www.vk.com", "vk.ru", "www.vk.ru")
                and parsed.path.startswith("/wall-243230846_")
                and parsed.path.split("_")[-1].isdigit()):
            return url
    return ""


def reconcile_scheduled(state, *, now=None, max_posts=12):
    """Synchronize recent VediSMM schedule status (read-only in VediSMM).

    On errors the state remains safe to retry. Each result is returned as a
    count. Failures mark a history entry as needing attention; never duplicate.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing VEDISMM_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    updates = 0
    checked = 0
    warnings = []
    candidates = []
    for item in state.get("posts", []):
        if item.get("publication_status") != "scheduled":
            continue
        at = _as_utc(item.get("scheduled_at"))
        if at is None:
            continue
        if now - timedelta(hours=3) <= at <= now + timedelta(hours=2):
            candidates.append((at, item))
    # Prefer posts already due, then soon-to-be-due ones.
    candidates.sort(key=lambda pair: (pair[0] > now, abs((pair[0]-now).total_seconds())))
    for at, item in candidates[:max_posts]:
        pid = item.get("vedismm_post_id")
        if not isinstance(pid, int) or pid <= 0:
            warnings.append("Missing VediSMM post ID in local history")
            continue
        response = requests.get(
            BASE + f"/posts/{pid}", headers=headers, timeout=35)
        response.raise_for_status()
        payload = response.json()
        remote = payload.get("data")
        if not isinstance(remote, dict):
            raise RuntimeError(f"Bad VediSMM response for post {pid}")
        checked += 1
        status = remote.get("status")
        if status == "published":
            link = _vk_post_link(remote)
            if link:
                item["publication_status"] = "published"
                item["vk_url"] = link
                updates += 1
            else:
                item["publication_status"] = "delivered_unverified"
                warnings.append(f"VediSMM post {pid} says published but VK link is unavailable")
                updates += 1
        elif status in ("failed", "cancelled", "canceled", "draft"):
            item["publication_status"] = "requires_attention"
            item["remote_status"] = status
            warnings.append(f"VediSMM post {pid} status {status}; no duplicate scheduled")
            updates += 1
        elif status == "scheduled":
            remote_at = _as_utc(remote.get("scheduled_at"))
            if remote_at and abs((remote_at-at).total_seconds()) > 60:
                item["publication_status"] = "requires_attention"
                item["remote_status"] = status
                warnings.append(f"VediSMM post {pid} schedule changed externally")
                updates += 1
        elif status in ("publishing", "queued", "processing"):
            pass
        else:
            warnings.append(f"VediSMM post {pid} has unknown status {status!r}")
    return {"checked": checked, "updated": updates, "warnings": warnings}
