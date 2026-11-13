"""Editorial guard: only approved coherent SHAM meme pairs."""
import difflib
import hashlib
import os
import random
import re

from quality_bank import TOPICS
from short_jokes import SHORT_JOKES
from hard_jokes import HARD_JOKES
from fresh_jokes import FRESH_JOKES
from editorial_jokes import EDITORIAL_JOKES
from meaning_guard import recent_meaning_conflict

SPECIAL_JOKES = SHORT_JOKES + HARD_JOKES + FRESH_JOKES + EDITORIAL_JOKES


def norm(s):
    return re.sub(r"[^а-яa-z0-9]+", " ", s.lower().replace("ё", "е")).strip()


def joke_id(p):
    return hashlib.sha256((norm(p["top"]) + "|" + norm(p["bottom"])).encode("utf-8")).hexdigest()


def similar(a, b, limit=0.9):
    a, b = norm(a), norm(b)
    return bool(a and b and (a == b or difflib.SequenceMatcher(None, a, b).ratio() >= limit))


def approved(p):
    if (p.get("source") == "ovh_chat_reviewed_v1"
            and str(p.get("topic", "")).startswith("gen_")
            and isinstance(p.get("visual"), str) and len(p["visual"].split()) >= 9
            and p.get("scene") in ("work", "wallet", "phone", "home", "social", "life")
            and p.get("idea_key")):
        return True
    if any(all(p.get(k) == item[k] for k in ("topic","scene","top","bottom","visual"))
           for item in SPECIAL_JOKES):
        return True
    return any(p.get("topic") == t["topic"] and p.get("scene") == t["scene"]
               and p.get("visual") == t["visual"]
               and p.get("top") in t["setups"]
               and p.get("bottom") in t["punchlines"] for t in TOPICS)


def validate(p, history=()):
    if not approved(p):
        raise ValueError("Incompatible or unapproved SHAM joke")
    if not 15 <= len(p["top"]) <= 140 or not 20 <= len(p["bottom"]) <= 150:
        raise ValueError("SHAM meme text length is out of range")
    if not p.get("caption") or similar(p["top"], p["bottom"]):
        raise ValueError("SHAM meme has no valid caption or repeats itself")
    if joke_id(p) in {x.get("id") or joke_id(x) for x in history
                     if x.get("top") and x.get("bottom")}:
        raise ValueError("SHAM meme already used")
    if any(similar(p["top"], x.get("top", ""), 0.94) for x in history[-90:]):
        raise ValueError("SHAM setup nearly repeats a recent post")
    if any(similar(p["bottom"], x.get("bottom", ""), 0.94) for x in history[-60:]):
        raise ValueError("SHAM punchline repeats a recent post")
    if recent_meaning_conflict(p, history):
        raise ValueError("SHAM repeats the meaning of a recent joke")
    return True


# Only deliberately selected older gags may supplement the newer, edited
# bank. Generic mixed setup/punchline combinations are never admitted in the
# production quality-first lane.
QUALITY_BACKUP_TOPICS = frozenset({
    "mini_passenger_luggage", "mini_wedding_bureaucracy",
    "mini_mirror_upgrade", "mini_delivery_drone", "mini_cat_tax",
    "mini_museum_phone", "mini_parking_meteor", "mini_dog_interview",
    "mini_elevator_therapy", "mini_sleep_cinema", "mini_alien_forms",
    "mini_self_checkout", "mini_ghost_smartphone", "mini_online_teacher",
    "mini_rent_coffin", "mini_groupchat_apocalypse", "mini_ai_resume",
})


def _quality_first():
    return os.getenv("SHAM_EDITORIAL_MODE", "").strip().lower() == "quality_first"


def select_post(state, slot):
    history = state.get("posts", [])
    used = {x.get("id") or joke_id(x) for x in history
            if x.get("top") and x.get("bottom")}
    top_recent = [x.get("top", "") for x in history[-105:]]
    ending_recent = [x.get("bottom", "") for x in history[-60:]]
    topic_recent = {x.get("topic") for x in history[-18:]}
    scenes_recent = {x.get("scene") for x in history[-2:]}
    caption_recent = {norm(x.get("caption", "")) for x in history[-12:]}
    rng = random.Random(slot + "-SHAM-approved-v2")
    quality_first = _quality_first()
    # Complete, individually written punchlines and their exact visual briefs.
    # In the live production mode the 44 newer editorial jokes are evaluated
    # first. A finite, explicitly whitelisted backup is allowed; if none is
    # fresh enough the scheduler skips rather than inventing filler.
    premium = list(EDITORIAL_JOKES)
    backup = ([p for p in FRESH_JOKES + HARD_JOKES
               if p["topic"] in QUALITY_BACKUP_TOPICS]
              if quality_first else list(FRESH_JOKES + HARD_JOKES + SHORT_JOKES))
    rng.shuffle(premium)
    rng.shuffle(backup)
    for mini in premium + backup:
        if mini["topic"] in topic_recent or mini["scene"] in scenes_recent:
            continue
        if joke_id(mini) in used:
            continue
        if any(similar(mini["top"], p, 0.92) for p in top_recent):
            continue
        if any(similar(mini["bottom"], p, 0.94) for p in ending_recent):
            continue
        if recent_meaning_conflict(mini, history):
            continue
        try:
            validate(mini, history)
        except ValueError:
            continue
        return dict(mini)
    if quality_first:
        raise RuntimeError(
            "SHAM editorial pool exhausted. Deliberately skipping slot "
            "instead of publishing stale thematic filler.")
    # Only if all full-story drafts are unavailable: thematic bank.
    topics = list(TOPICS)
    rng.shuffle(topics)
    topics.sort(key=lambda t: sum(x.get("topic") == t["topic"] for x in history[-120:]))
    for t in topics:
        if t["topic"] in topic_recent or t["scene"] in scenes_recent:
            continue
        tops, ends = list(t["setups"]), list(t["punchlines"])
        rng.shuffle(tops)
        rng.shuffle(ends)
        for top in tops:
            if any(similar(top, p, 0.92) for p in top_recent):
                continue
            for bottom in ends:
                if any(similar(bottom, p, 0.94) for p in ending_recent):
                    continue
                post = {"top": top, "bottom": bottom, "scene": t["scene"],
                        "topic": t["topic"], "visual": t["visual"]}
                if joke_id(post) in used or recent_meaning_conflict(post, history):
                    continue
                captions = [c for c in t["captions"] if norm(c) not in caption_recent]
                post["caption"] = rng.choice(captions or t["captions"])
                validate(post, history)
                return post
    raise RuntimeError("No approved fresh coherent SHAM joke; cancelling low-quality publication")
