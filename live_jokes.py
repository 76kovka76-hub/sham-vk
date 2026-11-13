"""Optional zero-key live joke generation for SHAM via OVH chat endpoint.

Generates five original ideas, selects one after local semantic and scene-brief
checks, and gracefully falls back to curated jokes if the free model is busy.
No text-only publications and no claim of actual image understanding.
"""
import hashlib
import json
import os
import re

import requests

from meaning_guard import lexical_overlap, recent_meaning_conflict

API = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
MODEL = "Qwen3.8-27B"
SCENES = frozenset(("work", "wallet", "phone", "home", "social", "life"))
DULL_ENDINGS = (
    "вот такая история", "жизнь боль", "так и живем", "это было смешно",
    "а потом я проснулся", "все как обычно", "ну вы поняли",
)
SYSTEM = (
    "You are a Russian comedy editor writing ORIGINAL, unusually funny short memes "
    "for an irreverent adult VK group called SHAM. Original absurd situations, hard "
    "satire, adult swearing when the punchline earns it, black comedy, witty "
    "internet/technology/life humor, unexpected endings. No fake claims about "
    "real events or real people's misdeeds, no attacks on protected groups, "
    "no sexual content involving minors. Do not imitate or quote existing jokes. "
    "VERY IMPORTANT: every scene brief must depict the exact physical joke "
    "and the punchline, not just a generic person or a generic background. "
    "Write natural colloquial RUSSIAN in top and bottom; write visual IN ENGLISH. "
    "Return only valid JSON object."
)


def _parse_object(value):
    if not isinstance(value, str) or len(value) > 20000:
        raise ValueError("Invalid live joke response")
    start = value.find("{")
    if start < 0:
        raise ValueError("Live jokes contained no JSON object")
    data, _ = json.JSONDecoder().raw_decode(value[start:])
    if not isinstance(data, dict):
        raise ValueError("Live jokes must be a JSON object")
    return data


def _clean(value, max_len):
    if not isinstance(value, str) or len(value) > max_len * 2:
        return ""
    text = re.sub(r"\s+", " ", value).strip().strip('"')
    if len(text) > max_len or "<" in text or ">" in text:
        return ""
    return text


def _coherent_candidate(raw):
    if not isinstance(raw, dict):
        return None
    post = {
        "top": _clean(raw.get("top"), 140),
        "bottom": _clean(raw.get("bottom"), 150),
        "caption": _clean(raw.get("caption"), 160),
        "visual": _clean(raw.get("visual"), 420),
        "scene": _clean(raw.get("scene"), 15).lower(),
        "idea_key": _clean(raw.get("idea_key"), 60).lower(),
    }
    if post["scene"] not in SCENES:
        return None
    if not 15 <= len(post["top"]) <= 140 or not 20 <= len(post["bottom"]) <= 150:
        return None
    if not 6 <= len(post["caption"]) <= 160:
        return None
    if not 9 <= len(post["visual"].split()) <= 65:
        return None
    if re.search(r"[а-яё]", post["visual"], re.I):
        return None
    if len(post["idea_key"].split()) > 4 or len(post["idea_key"]) < 5:
        return None
    if len(re.findall(r"[а-яё]", post["top"] + post["bottom"], re.I)) < 30:
        return None
    if any(ending in post["bottom"].lower().replace("ё", "е") for ending in DULL_ENDINGS):
        return None
    if post["top"].lower() == post["bottom"].lower():
        return None
    # This source flag is assigned in code, not supplied by the text generator.
    post["source"] = "ovh_chat_reviewed_v1"
    post["topic"] = "gen_" + hashlib.sha256(
        (post["top"] + "|" + post["bottom"]).encode("utf-8")
    ).hexdigest()[:12]
    return post


def _request_five(state, slot):
    last = state.get("posts", [])[-20:]
    avoid = [
        {"setup": str(p.get("top", ""))[:140], "punchline": str(p.get("bottom", ""))[:150],
         "idea": str(p.get("idea_key") or p.get("topic") or "")[:80]}
        for p in last
    ]
    desired = ["dark absurd", "hard sarcastic", "unexpected dialogue",
               "cultural/technology satire", "surreal physical gag"]
    payload = {
        "model": os.getenv("SHAM_TEXT_MODEL", MODEL),
        "temperature": 0.95,
        "max_tokens": 2300,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                "Write EXACTLY five different original jokes, one for each of these "
                "humor directions: " + ", ".join(desired) + ". "
                "Use five different premises and preferably different locations. "
                "Avoid trivial topics repeated in this history. History: " +
                json.dumps(avoid, ensure_ascii=False) +
                "\nFor each candidate provide: top (Russian setup), "
                "bottom (Russian unexpected punchline), caption (Russian one short line), "
                "visual (VERY SPECIFIC English physical scene: concrete characters, "
                "objects and action illustrating EXACTLY the ending), "
                "scene (one of work,wallet,phone,home,social,life), "
                "idea_key (unique English 2-3 word thematic story name). "
                "Do NOT make up quotes from real celebrities or claim news facts. "
                "Return JSON object {\"candidates\": [five objects]}. "
                "Slot seed: " + slot
            )},
        ],
    }
    response = requests.post(API, json=payload,
                             headers={"Accept": "application/json",
                                      "Content-Type": "application/json"},
                             timeout=22)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not isinstance(choices, list) or not choices:
        raise ValueError("Live joke API returned no choices")
    text = (choices[0].get("message") or {}).get("content")
    return _parse_object(text)


def generate_live_post(state, slot):
    """Return vetted original generated joke or raise to permit curated fallback."""
    result = _request_five(state, slot)
    items = result.get("candidates")
    if not isinstance(items, list) or not 4 <= len(items) <= 6:
        raise ValueError("Expected five independent original joke candidates")
    history = state.get("posts", [])
    recent_scenes = {p.get("scene") for p in history[-2:]}
    seen = set()
    viable = []
    from quality_guard import validate
    for raw in items:
        post = _coherent_candidate(raw)
        if post is None or post["scene"] in recent_scenes:
            continue
        if post["idea_key"] in seen or recent_meaning_conflict(post, history):
            continue
        seen.add(post["idea_key"])
        try:
            validate(post, history)
        except ValueError:
            continue
        # Favor distinct premise and specific visual gag, not keyword stuffing.
        overlap = max((lexical_overlap(post, prior) for prior in history[-35:]),
                      default=0.0)
        scene_words = len(set(post["visual"].lower().split()))
        score = (2.5 - overlap * 3.0
                 + min(scene_words, 25) / 35.0
                 + (0.5 if "!" not in post["bottom"] else 0.0))
        viable.append((score, post))
    if not viable:
        raise ValueError("No original SHAM joke passed text and meaning checks")
    viable.sort(key=lambda item: item[0], reverse=True)
    return viable[0][1]
