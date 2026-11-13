"""Aggregate community interests from SHAM's public VK comments.

Only counts topic keywords; never saves, logs, quotes, or sends commenters'
text, IDs or names to a generative model. Disabled gracefully if VK API denies.
"""
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

import requests

GROUP_ID = 243230846
VK_API = "https://api.vk.com/method/wall.getComments"
TOPIC_STEMS = {
    "нейросети": ("нейросет", "искусственн интеллект", "ии "),
    "роботы": ("робот", "дроид", "андроид"),
    "животные": ("кот", "коту", "кошк", "собак", "голуб"),
    "кино": ("кино", "сериал", "фильм"),
    "отношения": ("свидан", "партнер", "муж", "жена", "любов"),
    "работа": ("начальник", "начальств", "коллег", "офис", "работ"),
    "транспорт": ("маршрут", "метро", "автобус", "машин", "парков"),
    "технологии": ("смартфон", "телефон", "компьютер", "гаджет"),
    "абсурд": ("сюрреал", "абсурд", "странн", "бред"),
    "космос": ("космос", "марс", "луна", "пришел"),
    "бюрократия": ("бюрократ", "мфц", "документ", "чиновник"),
    "спорт": ("спорт", "трениров", "фитнес", "зал"),
}
SAFE_WORDS = frozenset(TOPIC_STEMS)


def _post_ids(state, limit=15):
    ids = []
    for post in reversed(state.get("posts", [])):
        if post.get("publication_status") != "published":
            continue
        match = re.fullmatch(
            r"https://(?:www\.)?vk\.(?:com|ru)/wall-243230846_([0-9]+)",
            str(post.get("vk_url") or ""))
        if not match:
            continue
        n = int(match.group(1))
        if n not in ids:
            ids.append(n)
        if len(ids) >= limit:
            break
    return ids


def extract_themes(text):
    if not isinstance(text, str) or not 12 <= len(text) <= 500:
        return set()
    lower = " " + re.sub(r"\s+", " ", text.casefold().replace("ё", "е")) + " "
    if any(x in lower for x in ("http:", "https:", "t.me/", "vk.com/")):
        return set()
    return {name for name, stems in TOPIC_STEMS.items() if any(stem in lower for stem in stems)}


def gather(state, *, caller=None):
    tokens = list(dict.fromkeys([
        key for key in (os.getenv("VK_GROUP_TOKEN", "").strip(),
                        os.getenv("VK_USER_TOKEN", "").strip()) if key]))
    ids = _post_ids(state)
    if not tokens or not ids:
        return {"status": "unavailable", "reason": "no_confirmed_wall_or_vk_token",
                "topics": [], "scanned_posts": 0}
    caller = caller or requests.get
    mentions = defaultdict(set)
    scanned = 0
    try:
        for post_id in ids:
            comments = None
            error_code = "unknown"
            for token in tokens:
                response = caller(
                    VK_API, params={
                        "owner_id": -GROUP_ID, "post_id": post_id,
                        "count": 70, "sort": "desc", "v": "5.199",
                        "access_token": token,
                    }, timeout=15)
                response.raise_for_status()
                payload = response.json()
                if payload.get("error"):
                    err = payload["error"]
                    if isinstance(err, dict):
                        error_code = str(err.get("error_code", "unknown"))
                    continue
                comments = payload.get("response", {}).get("items") or []
                break
            if comments is None:
                return {"status": "unavailable",
                        "reason": "vk_api_denied_" + error_code,
                        "topics": [], "scanned_posts": scanned}
            if not isinstance(comments, list):
                continue
            scanned += 1
            for comment in comments:
                if not isinstance(comment, dict) or comment.get("deleted"):
                    continue
                sender = comment.get("from_id")
                if not isinstance(sender, int) or sender <= 0:
                    continue
                for name in extract_themes(comment.get("text", "")):
                    mentions[name].add(sender)  # ephemeral count; NEVER serialized
        sorted_topics = sorted(
            [(name, len(senders)) for name, senders in mentions.items()
             if len(senders) >= 2], key=lambda x: (-x[1], x[0]))
        return {"status": "ok", "topics": [
                    {"name": name, "unique_commenters": count}
                    for name, count in sorted_topics[:8]],
                "scanned_posts": scanned,
                "created_at": datetime.now(timezone.utc).isoformat()}
    except (requests.RequestException, ValueError, TypeError):
        return {"status": "unavailable", "reason": "api_request_error",
                "topics": [], "scanned_posts": scanned}


def cached_themes(path=Path("state/community_signals.json"), *, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        timestamp = datetime.fromisoformat(data["created_at"])
        if data.get("status") != "ok" or timestamp.tzinfo is None:
            return []
        if abs((now - timestamp).total_seconds()) > 9 * 86400:
            return []
        return [x["name"] for x in data["topics"]
                if x.get("name") in SAFE_WORDS and x.get("unique_commenters", 0) >= 2][:6]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def main():
    from main import get_state
    data = gather(get_state())
    if data["status"] == "ok":
        path = Path("state/community_signals.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = Path("output/sham_community_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SHAM_COMMUNITY:", data["status"], "reason=", data.get("reason", ""),
          "scanned_posts=", data["scanned_posts"],
          "topics=", [t["name"] for t in data["topics"]])


if __name__ == "__main__":
    main()
