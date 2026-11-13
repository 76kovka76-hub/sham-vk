"""Plan a rolling queue of SHAM posts, using quarter-hour UTC slots."""
from datetime import datetime, timedelta, timezone


def slot_name(when: datetime) -> str:
    when = when.astimezone(timezone.utc)
    return f"{when.date().isoformat()}-{when.hour:02d}-{when.minute // 15:02d}"


def next_missing_slot(state, now=None, *, lead_minutes=30, buffer_hours=12, step_minutes=15):
    """Earliest unreserved slot between now+lead and now+buffer (UTC).

    Returns (slot_name, scheduled_datetime) or (None, None) when full.
    Already-recorded slots are immutable: failed delivery must be handled
    separately rather than duplicated by an automatic retry.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    if not (20 <= lead_minutes < 60):
        raise ValueError("lead_minutes must be between 20 and 59")
    if not (2 <= buffer_hours <= 48):
        raise ValueError("buffer_hours must be between 2 and 48")
    if step_minutes not in (15, 30, 60):
        raise ValueError("step_minutes must be 15, 30 or 60")
    start = now + timedelta(minutes=lead_minutes)
    floor = start.replace(minute=(start.minute // 15) * 15, second=0,
                          microsecond=0)
    if floor < start:
        floor += timedelta(minutes=15)
    cutoff = now + timedelta(hours=buffer_hours)
    # Keep the established 15-minute naming system but only consider
    # user-selected editorial publication moments. Old booked slots remain.
    while floor.minute % step_minutes != 0:
        floor += timedelta(minutes=15)
    reserved = set(state.get("slots", []))
    while floor <= cutoff:
        name = slot_name(floor)
        if name not in reserved:
            return name, floor
        floor += timedelta(minutes=step_minutes)
    return None, None
