"""One-time SHAM editorial rejection list for already booked weak captions.

Human text-level review of the existing queue, not an image classifier.
Only still-scheduled posts with >= 90 min lead may be flagged for an
ETag-checked unschedule by the normal VediSMM cleanup path. No deletion
of published content. IDs belong exclusively to SHAM 243230846.
"""
from datetime import datetime, timedelta, timezone

REJECTED_QUEUED_IDS = frozenset({
    # Legacy v2 routine filler, if still pending with enough lead.
    5066, 5067, 5068, 5069, 5070, 5071, 5073,
    # Later v3 stories with overly predictable or repetitious gimmicks.
    5087, 5088, 5090, 5091, 5113, 5115, 5116, 5118,
    5124, 5127, 5128, 5129, 5135, 5139, 5141, 5142, 5143, 5144,
})


def mark_rejected_future(state, *, now=None, min_lead_minutes=90):
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None or min_lead_minutes < 60:
        raise ValueError("Editorial review requires aware time and safe lead")
    count = 0
    for item in state.get("posts", []):
        if (item.get("publication_status") != "scheduled"
                or item.get("vedismm_post_id") not in REJECTED_QUEUED_IDS):
            continue
        value = item.get("scheduled_at")
        if not isinstance(value, str):
            continue
        try:
            when = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None or when <= now + timedelta(minutes=min_lead_minutes):
            continue
        item["review_rejected"] = True
        item["review_rejected_reason"] = "editorial: weak or repeated premise"
        count += 1
    return count
