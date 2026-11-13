"""SOVETSKIY 15-minute rolling UTC calendar (96 slots every day).

Only FUTURE slots can be scheduled; GitHub cron is best-effort, so buffer
multiple hours ahead via VediSMM. Never claim a slot is delivered without
confirmed VediSMM scheduling.
"""
from datetime import datetime, timedelta, timezone

SLOTS_PER_DAY=96
SLOT_MINUTES=15
HORIZON_HOURS=14
LEAD_MINUTES=45


def day_slots(day):
    midnight=datetime(day.year,day.month,day.day,tzinfo=timezone.utc)
    return [(f"{day:%Y%m%d}-{n:02d}",midnight+timedelta(minutes=n*SLOT_MINUTES))
            for n in range(SLOTS_PER_DAY)]


def upcoming_slots(state,now=None,horizon_hours=HORIZON_HOURS,lead_minutes=LEAD_MINUTES):
    """Return all still-unreserved candidate UTC slots in a rolling buffer."""
    if now is None:
        now=datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware time required")
    now=now.astimezone(timezone.utc)
    if not (1<=horizon_hours<=36) or not (15<=lead_minutes<=180):
        raise ValueError("Invalid buffer config")
    reserved={x.get("slot") for x in state.get("entries",[]) if x.get("slot")}
    first=now+timedelta(minutes=lead_minutes)
    last=now+timedelta(hours=horizon_hours)
    days=[now.date()+(timedelta(days=i)) for i in range(3)]
    return [(slot,at) for day in days for slot,at in day_slots(day)
            if first<=at<=last and slot not in reserved]


def next_slot(state,now=None):
    all_slots=upcoming_slots(state,now)
    return all_slots[0] if all_slots else (None,None)


def daily_coverage(state,day):
    slots={x.get("slot") for x in state.get("entries",[])
           if x.get("status")=="scheduled"}
    planned={slot for slot,at in day_slots(day)}
    return len(planned & slots)


if __name__=="__main__":
    from datetime import date
    for day in (date(2026,11,13),date(2027,1,1)):
        slots=day_slots(day)
        print(day,"slots",len(slots),"first",slots[0],"last",slots[-1])
