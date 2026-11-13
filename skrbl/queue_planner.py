"""SKRBL 50/day: strict schedule and quality-gated approved-media pool.

This is a planning/approval component, NOT a drawing generator.
Never substitute SHAM images or anonymous AI one-panel portraits for approved
SKRBL 2-4 frame pencil comics.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

POSTS_PER_DAY = 50
MINUTES_PER_DAY = 1440
LEAD_MINUTES = 60
HORIZON_HOURS = 12
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "approved"
LEDGER_PATH = ROOT / "queue_state.json"
MANIFEST_PATH = ROOT / "approved.json"

HASHTAG_PATTERN = re.compile(r"(?<!\w)#[\wа-яА-ЯёЁ]+", re.UNICODE)
UNMASKED_SWEARS = re.compile(
    r"(?i)(?:\bблять\b|\bблядь\b|\bпиздец\b|\bпизд[а-яё]+\b|"
    r"\bебан[а-яё]*\b|\bнахуй\b|\bхуй\b|\bсука\b|\bебать\b)"
)


def all_day_slots(day):
    """Exactly 50 distinct, near-evenly-spaced slots per UTC calendar day.

    UTC is intentionally used to avoid daylight-saving and ambiguous slots.
    """
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return [
        (f"{day:%Y%m%d}-{i:02d}",
         start + timedelta(minutes=(MINUTES_PER_DAY * i) // POSTS_PER_DAY))
        for i in range(POSTS_PER_DAY)
    ]


def next_slot(ledger, now=None, *, lead_minutes=LEAD_MINUTES,
              horizon_hours=HORIZON_HOURS):
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware UTC datetime required")
    now = now.astimezone(timezone.utc)
    if lead_minutes < 30 or not 1 <= horizon_hours <= 48:
        raise ValueError("Unsafe queue horizon")
    lower, upper = (now + timedelta(minutes=lead_minutes),
                    now + timedelta(hours=horizon_hours))
    busy = {x["slot"] for x in ledger.get("entries", []) if "slot" in x}
    for d in (now.date(), (now + timedelta(days=1)).date(),
              (now + timedelta(days=2)).date()):
        for slot, at in all_day_slots(d):
            if lower <= at <= upper and slot not in busy:
                return slot, at
    return None, None


def _is_approved(record):
    return (
        record.get("approved") is True and
        isinstance(record.get("id"), str) and
        re.fullmatch(r"[a-z0-9][a-z0-9_-]{3,63}", record["id"]) is not None and
        isinstance(record.get("file"), str) and
        re.fullmatch(r"[a-zA-Z0-9_-]{4,85}\.png", record["file"]) is not None and
        isinstance(record.get("sha256"), str) and
        re.fullmatch(r"[a-f0-9]{64}", record["sha256"]) is not None and
        isinstance(record.get("caption"), str) and
        18 <= len(record["caption"]) <= 700 and
        len(HASHTAG_PATTERN.findall(record["caption"])) == 3 and
        UNMASKED_SWEARS.search(record["caption"]) is None and
        record.get("panels") in (2, 3, 4)
    )


def select_approved(manifest, ledger):
    """Only images that pass human approval and exact sha256 checks.

    Quality status is not inferred from AI completion. One file = one unique
    published/scheduled post; no automatic repeats.
    """
    used_ids = {x.get("asset_id") for x in ledger.get("entries", [])}
    used_hashes = {x.get("sha256") for x in ledger.get("entries", [])}
    seen_ids, seen_hashes = set(), set()
    if not isinstance(manifest, list):
        raise ValueError("approved.json must be an array")
    for item in manifest:
        if not isinstance(item, dict) or not _is_approved(item):
            continue
        if item["id"] in seen_ids or item["sha256"] in seen_hashes:
            continue
        seen_ids.add(item["id"])
        seen_hashes.add(item["sha256"])
        if item["id"] in used_ids or item["sha256"] in used_hashes:
            continue
        path = ASSETS / item["file"]
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            continue
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            continue
        try:
            from PIL import Image
            with Image.open(path) as img:
                if min(img.size) < 1000 or img.format != "PNG":
                    continue
                # Refuse visually empty/flat files (not proof of humor).
                stat = img.convert("L").resize((128, 128))
                hist = stat.histogram()
                if sum(1 for x in hist if x) < 45:
                    continue
        except (OSError, ValueError):
            continue
        return item, path
    return None, None


def load_state():
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def preview(now=None):
    ledger = load_state()
    items = load_manifest()
    slot, at = next_slot(ledger, now)
    post, path = select_approved(items, ledger)
    print("SKRBL_DAILY_TARGET: 50")
    print("SKRBL_NEXT_SLOT:", slot)
    print("SKRBL_NEXT_TIME:", at.isoformat() if at else "(full)")
    print("SKRBL_APPROVED_UNPUBLISHED:", sum(
        bool(x.get("approved")) and x.get("id") not in
        {p.get("asset_id") for p in ledger.get("entries", [])}
        for x in items
    ))
    print("SKRBL_READY_TO_SCHEDULE:", bool(slot and post))
    if post:
        print("SKRBL_NEXT_APPROVED_ID:", post["id"])
    else:
        print("No quality-approved unused comic. Skipping rather than publishing a poor image.")
    return slot, at, post, path
