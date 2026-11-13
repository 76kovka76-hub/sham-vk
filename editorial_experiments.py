"""Deterministic humor treatments and light editorial quality scoring for SHAM.

Each slot has a preferred *direction*, not an obligation to publish bad jokes.
Actual engagement analysis will compare real published posts once sample sizes
are large enough; never optimize on fake or missing statistics.
"""
from datetime import date
import re

LANES = (
    "hard_absurdity", "dark_irony", "technology_satire",
    "unexpected_dialogue", "surreal_physical", "observational",
    "mock_official", "chaotic_collage",
)
CANDIDATE_LANES = (
    "hard_absurdity", "dark_irony", "unexpected_dialogue",
    "technology_satire", "surreal_physical",
)
TRITE = (
    "вот такая история", "жизнь боль", "ну вы поняли", "и все засмеялись",
    "и тут я проснулся", "да уж", "ну как-то так",
)


def lane_for_slot(slot):
    try:
        day, hour, quarter = slot.rsplit("-", 2)
        offset = date.fromisoformat(day).toordinal() * 96 + int(hour) * 4 + int(quarter)
        if not (len(hour) == len(quarter) == 2 and 0 <= int(hour) < 24
                and 0 <= int(quarter) < 4):
            raise ValueError("invalid slot")
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("SHAM slot invalid for editorial experiment") from exc
    return LANES[offset % len(LANES)]


def score_post(post, history=()):
    from meaning_guard import lexical_overlap, recent_meaning_conflict
    if recent_meaning_conflict(post, history):
        return -100.0
    top = str(post.get("top") or "").strip()
    bottom = str(post.get("bottom") or "").strip()
    visual = str(post.get("visual") or "").strip()
    if not 15 <= len(top) <= 140 or not 20 <= len(bottom) <= 150:
        return -100.0
    lower = bottom.casefold().replace("ё", "е")
    if any(cliché in lower for cliché in TRITE):
        return -100.0
    if len(visual.split()) < 8:
        return -100.0
    overlap = max((lexical_overlap(post, older) for older in history[-70:]), default=0.0)
    # Profanity alone does not increase the score. Specificity does.
    visual_specificity = min(len(set(re.findall(r"[a-z]+", visual.lower()))), 32) / 32
    ending_unexpected = int(any(mark in bottom for mark in (":", "—", "!", "?", "«", "»")))
    lazy_ending = int("блядь" in lower and len(bottom.split()) < 7)
    return round(5.0 - overlap * 4.5 + visual_specificity * 1.5
                 + ending_unexpected * 0.25 - lazy_ending * 0.75, 3)


def choose_candidate(candidates, history, slot):
    preferred = lane_for_slot(slot)
    rated = []
    for item in candidates:
        score = score_post(item, history)
        if score < 0:
            continue
        if item.get("humor_lane") == preferred:
            score += 0.35
        rated.append((score, item))
    if not rated:
        return None
    rated.sort(key=lambda item: item[0], reverse=True)
    selected = dict(rated[0][1])
    selected["editorial_score"] = round(rated[0][0], 3)
    return selected
