"""Read-only SHAM queue observability, fully free on GitHub Actions.

This module never calls VediSMM or VK and never creates or cancels posts.
It distinguishes a reserved slot, a confirmed VK delivery, an unresolved
status and an actual gap. History alone is not live delivery verification.
"""
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _slot_time(slot):
    try:
        day, hh, quarter = str(slot).rsplit("-", 2)
        date = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        hour, q = int(hh), int(quarter)
        if len(hh) != 2 or len(quarter) != 2 or not 0 <= hour < 24 or not 0 <= q < 4:
            return None
        return date.replace(hour=hour, minute=q * 15)
    except (TypeError, ValueError, AttributeError):
        return None


def queue_audit(state, *, now=None, hours=12, lead_minutes=30):
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None or not 1 <= hours <= 48 or not 15 <= lead_minutes <= 90:
        raise ValueError("Invalid SHAM audit range or time")
    now = now.astimezone(timezone.utc)
    begin = now + timedelta(minutes=lead_minutes)
    cursor = begin.replace(minute=(begin.minute // 15) * 15, second=0,
                           microsecond=0)
    if cursor < begin:
        cursor += timedelta(minutes=15)
    end = now + timedelta(hours=hours)
    expected = []
    while cursor <= end:
        expected.append(cursor)
        cursor += timedelta(minutes=15)

    posts = [p for p in state.get("posts", []) if isinstance(p, dict)]
    status_totals = dict(Counter(str(p.get("publication_status") or "unknown")
                                 for p in posts))
    good = {"scheduled", "published"}
    reserved = {}
    duplicates = []
    unresolved = []
    for post in posts:
        at = _slot_time(post.get("slot"))
        if at is None or at < begin or at > end:
            continue
        slot = at.strftime("%Y-%m-%d-%H-") + str(at.minute // 15).zfill(2)
        if slot in reserved:
            duplicates.append(slot)
        if post.get("publication_status") in good:
            reserved[slot] = post
        elif slot not in reserved:
            unresolved.append(slot)
    desired = [at.strftime("%Y-%m-%d-%H-") + str(at.minute // 15).zfill(2)
               for at in expected]
    missing = [slot for slot in desired if slot not in reserved]
    soon = [slot for slot in missing
            if (_slot_time(slot) - now) <= timedelta(minutes=90)]
    published = [p for p in posts
                 if p.get("publication_status") == "published"
                 and isinstance(p.get("vk_url"), str)
                 and "/wall-243230846_" in p.get("vk_url")]
    statuses_requiring_attention = [
        {"slot": p.get("slot"), "vedismm_post_id": p.get("vedismm_post_id"),
         "status": p.get("publication_status")}
        for p in posts
        if p.get("publication_status") in {"requires_attention", "delivered_unverified"}
        and (_slot_time(p.get("slot")) or datetime(1970, 1, 1, tzinfo=timezone.utc))
            >= now - timedelta(days=2)
    ][:20]
    coverage = round(len(desired) and (len(desired) - len(missing)) /
                     len(desired) or 0, 3)
    status = ("urgent" if soon or duplicates or statuses_requiring_attention
              else "degraded" if coverage < .75 else "healthy")
    return {
        "checked_at": now.isoformat(), "status": status,
        "window_hours": hours, "expected_slots": len(desired),
        "reserved_slots": len(desired) - len(missing),
        "coverage": coverage, "missing_slots": missing,
        "urgent_missing_slots": soon, "duplicate_slots": sorted(set(duplicates)),
        "unresolved_in_window": sorted(set(unresolved)),
        "recent_attention": statuses_requiring_attention,
        "published_with_vk_url_count": len(published),
        "local_status_totals": status_totals,
        "last_confirmed_vk_url": published[-1].get("vk_url", "") if published else "",
        "note": "Local GitHub snapshot, not live VediSMM status. "
                "Only confirmed VK wall URLs count as delivered.",
    }


def main():
    state_path = Path("state/history.json")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    report = queue_audit(state)
    out = Path("output/sham_queue_audit.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fp:
            fp.write(
                "\n### SHAM — контроль очереди ВедиSMM (локальная история)\n"
                + f"Статус: **{report['status']}**; заполнено "
                + f"**{report['reserved_slots']}/{report['expected_slots']}** "
                + f"слотов на {report['window_hours']} ч.\n"
                + f"Ближайших пропусков: {len(report['urgent_missing_slots'])}; "
                + f"дублей: {len(report['duplicate_slots'])}; "
                + f"нуждаются в проверке: {len(report['recent_attention'])}.\n"
                + "Сведения из GitHub, не подтверждение будущей публикации во ВК.\n"
            )
    if report["status"] != "healthy":
        print("::warning::SHAM_QUEUE_AUDIT " +
              report["status"] + " missing_next_90m=" +
              str(len(report["urgent_missing_slots"])) +
              " suspect=" + str(len(report["recent_attention"])))
    print("SHAM_QUEUE_AUDIT:", report["status"],
          "reserved=", report["reserved_slots"],
          "expected=", report["expected_slots"],
          "last_published=", report["last_confirmed_vk_url"] or "(not confirmed)")


if __name__ == "__main__":
    main()
