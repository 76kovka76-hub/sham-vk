"""SHAM real engagement intelligence; only official VediSMM analytics.

Never treat demo statistics or unavailable fields as observed measurements.
Report is read-only, with no effect on publication when permissions are absent.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

import requests

from vedismm_publisher import BASE, _find_account_id

METRICS = ("reach", "impressions", "likes", "comments", "shares", "clicks", "engagement")


def _utc(date):
    if isinstance(date, datetime) and date.tzinfo is not None:
        return date.astimezone(timezone.utc)
    raise ValueError("date must be an aware datetime")


def _as_nonnegative(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or value < 0:
        return None
    return float(value)


def observed_metrics(row):
    """Respect available_metrics: null means unknown, not zero."""
    if row.get("is_demo") is not False:
        return {}
    available = row.get("available_metrics")
    if not isinstance(available, list):
        return {}
    return {name: _as_nonnegative(row.get(name))
            for name in METRICS
            if name in available and _as_nonnegative(row.get(name)) is not None}


def fetch_analytics(days=7, *, now=None, getter=None):
    """Query real VK-only insights. Returns unavailable status on scope errors."""
    if not 1 <= days <= 60:
        raise ValueError("Invalid analytics range")
    now = _utc(now or datetime.now(timezone.utc))
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        return {"status": "unavailable", "reason": "missing_token", "posts": []}
    getter = getter or requests.get
    params = {"from": (now - timedelta(days=days)).date().isoformat(),
              "to": now.date().isoformat(), "timezone": "Europe/Moscow",
              "network": "vk", "limit": 100}
    headers = {"Authorization": "Bearer " + token}
    try:
        # The connection already has accounts:read for normal publishing.
        account_id = _find_account_id(token)
        params["account_id"] = account_id
        resp = getter(BASE + "/analytics/posts", headers=headers,
                      params=params, timeout=25)
        if resp.status_code in (401, 403):
            return {"status": "unavailable", "reason": "missing_analytics_scope",
                    "posts": []}
        resp.raise_for_status()
        body = resp.json()
        items = body.get("data")
        if not isinstance(items, list):
            raise ValueError("VediSMM analytics did not return a list")
        if (body.get("meta") or {}).get("has_more"):
            # Do not claim to have checked the whole period when paginated.
            return {"status": "partial", "reason": "additional_pages",
                    "posts": [p for p in items if isinstance(p, dict)]}
        return {"status": "ok", "posts": [p for p in items if isinstance(p, dict)]}
    except (requests.RequestException, KeyError, ValueError, RuntimeError) as exc:
        return {"status": "unavailable",
                "reason": type(exc).__name__, "posts": []}


def summarize(history, remote, *, since=None):
    """Join VediSMM post IDs against own saved SHAM posts only."""
    entries = history.get("posts", [])
    own = {str(p.get("vedismm_post_id")): p
           for p in entries
           if isinstance(p.get("vedismm_post_id"), int)}
    ranked = []
    by_format = defaultdict(lambda: {"count": 0, "shares": 0.,
                                      "likes": 0., "comments": 0.})
    for item in remote.get("posts", []):
        local = own.get(str(item.get("id")))
        if not local or local.get("publication_status") not in (
                "published", "delivered_unverified"):
            continue
        metrics = observed_metrics(item)
        if not metrics:
            continue
        # Never score with fabricated zeros: at least 2 observed reactions.
        if not {"likes", "shares"}.issubset(metrics):
            continue
        reach = metrics.get("reach") or metrics.get("impressions")
        if reach is not None and reach > 0:
            score = (3 * metrics["shares"] + metrics["likes"]
                     + 2 * metrics.get("comments", 0)) / max(reach, 30)
        else:
            score = 3 * metrics["shares"] + metrics["likes"] + 2 * metrics.get("comments", 0)
        style = (local.get("image_source") or {}).get("style", "unknown")
        genre = local.get("humor_lane", "legacy")
        key = f"{genre}|{style}"
        stat = by_format[key]
        stat["count"] += 1
        for name in ("likes", "shares", "comments"):
            if name in metrics:
                stat[name] += metrics[name]
        ranked.append({
            "post_id": item["id"], "vk_url": local.get("vk_url", ""),
            "humor_lane": genre, "style": style,
            "score": round(score, 5),
            "metrics": metrics,
            "caption": (local.get("top", "") + " — " + local.get("bottom", ""))[:250],
        })
    ranked.sort(key=lambda p: (-p["score"], str(p["post_id"])))
    # Small sample sizes must not influence production automatically.
    experiments = {k: {**v, "sufficient_samples": v["count"] >= 12}
                   for k, v in sorted(by_format.items())}
    return {"status": remote.get("status", "unavailable"),
            "observed_posts": len(ranked), "top": ranked[:10],
            "experiments": experiments,
            "quality_note": "No demo data; unavailable metrics excluded. "
                            "A/B results are descriptive until samples are large."}


def main():
    from main import get_state
    report = summarize(get_state(), fetch_analytics())
    out = Path("output/sham_insights.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        top = report["top"][:5]
        lines = ["## SHAM: недельный топ и аналитика",
                 "Доступность: " + report["status"],
                 "Постов с проверенными метриками: " + str(report["observed_posts"])]
        lines.extend(f"- {p['caption']} — {p['vk_url'] or 'VK link unavailable'}"
                     for p in top)
        if not top:
            lines.append("Достоверных данных пока недостаточно. Никаких демонстрационных чисел.")
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print("SHAM_INSIGHTS:", report["status"], "verified=", report["observed_posts"])


if __name__ == "__main__":
    main()
