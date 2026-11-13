"""Optional fresh-topic inspiration from a documented public technology RSS feed.

Read-only and best-effort: source titles are UNTRUSTED data. Their role is
inspiration, never a fact to assert or a text instruction to execute.
No RSS data is published verbatim.
"""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import re
import xml.etree.ElementTree as ET

import requests

SOURCE_URL = "https://www.ixbt.com/export/news.rss"
SKIP_TERMS = (
    "погибли", "погиб", "убит", "убийств", "теракт", "жертв",
    "ракета попала", "взрыв на", "пострадал", "авария", "войн",
    "насили", "изнасил", "катастроф", "похорон", "скончал",
)
TREND_TERMS = {
    "нейросет": "нейросети",
    "искусственн": "искусственный интеллект",
    "робот": "роботы",
    "дрон": "дроны",
    "смартфон": "смартфоны",
    "телефон": "смартфоны",
    "космос": "космос",
    "луна": "космос",
    "марс": "космос",
    "автомоб": "автомобили",
    "электромоб": "электромобили",
    "гаджет": "гаджеты",
    "интернет": "интернет",
    "процессор": "компьютеры",
    "ноутбук": "компьютеры",
    "умный дом": "умный дом",
    "игр": "видеоигры",
}


def current_topics(*, now=None, getter=None):
    if getter is None:
        getter = requests.get
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        response = getter(SOURCE_URL, timeout=7,
                          headers={"User-Agent": "SHAM-editor/3 (+public RSS)"})
        response.raise_for_status()
        raw = response.content
        if len(raw) > 700_000:
            return []
        root = ET.fromstring(raw)
        themes = []
        for entry in root.findall(".//item")[:40]:
            title = " ".join((entry.findtext("title") or "").lower().split())
            if len(title) > 240 or any(x in title for x in SKIP_TERMS):
                continue
            pub = entry.findtext("pubDate")
            if pub:
                try:
                    date = parsedate_to_datetime(pub).astimezone(timezone.utc)
                    if abs((now - date).total_seconds()) > 3 * 86400:
                        continue
                except (TypeError, ValueError, OverflowError):
                    continue
            for stem, topic in TREND_TERMS.items():
                if stem in title and topic not in themes:
                    themes.append(topic)
                    break
            if len(themes) >= 5:
                return themes
        return themes
    except (requests.RequestException, ET.ParseError, UnicodeError):
        return []
