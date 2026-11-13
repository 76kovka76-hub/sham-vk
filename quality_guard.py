"""Editorial guard: only approved coherent SHAM meme pairs."""
import difflib
import hashlib
import random
import re

from quality_bank import TOPICS
from short_jokes import SHORT_JOKES
from hard_jokes import HARD_JOKES
from fresh_jokes import FRESH_JOKES
from meaning_guard import recent_meaning_conflict

SPECIAL_JOKES = SHORT_JOKES + HARD_JOKES + FRESH_JOKES


def norm(s):
    return re.sub(r"[^а-яa-z0-9]+", " ", s.lower().replace("ё", "е")).strip()


def joke_id(p):
    return hashlib.sha256((norm(p["top"]) + "|" + norm(p["bottom"])).encode("utf-8")).hexdigest()


def similar(a, b, limit=0.9):
    a, b = norm(a), norm(b)
    return bool(a and b and (a == b or difflib.SequenceMatcher(None, a, b).ratio() >= limit))


def approved(p):
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
    # Favor separately edited original jokes (including hard, profane, absurd),
    # instead of repeatedly mixing text from the longer themed banks.
    # Each short anecdote has its own action-specific photo/illustration.
    if rng.randrange(4) != 0:
        jokes = list(SPECIAL_JOKES)
        rng.shuffle(jokes)
        for mini in jokes:
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
            validate(mini, history)
            return dict(mini)
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
