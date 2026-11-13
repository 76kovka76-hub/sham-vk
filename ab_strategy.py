"""Conservative SHAM A/B optimization from verified, non-demo audience data.

Never optimize on missing metrics or fewer than 12 published observations per
arm. The first phase deliberately explores evenly; later, tiny bounded
adjustments can reward a better-performing lane without creating a monopoly.
"""
from datetime import datetime, timezone
import json
from pathlib import Path

MAX_BONUS = 0.22
MIN_SAMPLES = 12


def recommended_bias(cohorts):
    eligible = {
        lane: (row["score_sum"] / row["count"])
        for lane, row in cohorts.items()
        if row.get("count", 0) >= MIN_SAMPLES
        and isinstance(row.get("score_sum"), (int, float))
        and row.get("count", 0) <= 10000
    }
    if len(eligible) < 2:
        return {}
    scores = sorted(eligible.values())
    midpoint = scores[len(scores)//2]
    spread = max(max(scores) - min(scores), 0.001)
    return {lane: round(max(-MAX_BONUS, min(MAX_BONUS,
                                            (value - midpoint) / spread * MAX_BONUS)), 4)
            for lane, value in eligible.items()}


def cached_bias(path=Path("state/editorial_weights.json")):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(data["updated_at"])
        if updated.tzinfo is None:
            return {}
        if (datetime.now(timezone.utc) - updated).days > 31:
            return {}
        items = data["bias"]
        if not isinstance(items, dict) or len(items) > 20:
            return {}
        return {name: float(value) for name, value in items.items()
                if isinstance(name, str) and len(name) <= 40
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
                and -MAX_BONUS <= float(value) <= MAX_BONUS}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def update_weights(report, path=Path("state/editorial_weights.json")):
    if report.get("status") != "ok":
        return False
    weights = recommended_bias(report.get("cohorts") or {})
    if not weights:
        return False
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "verified_real_vk_or_vedismm_metrics",
        "min_samples_per_lane": MIN_SAMPLES,
        "bias": weights,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True
