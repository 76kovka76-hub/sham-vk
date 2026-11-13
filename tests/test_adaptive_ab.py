import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from ab_strategy import cached_bias, recommended_bias, update_weights


class AdaptiveStrategyTests(unittest.TestCase):
    def test_no_bias_with_small_or_missing_samples(self):
        self.assertEqual(recommended_bias({
            "hard_absurdity": {"count": 11, "score_sum": 20},
            "dark_irony": {"count": 100, "score_sum": 80},
        }), {})

    def test_enough_real_observations_make_small_bounded_adjustment(self):
        result = recommended_bias({
            "hard_absurdity": {"count": 20, "score_sum": 5},
            "dark_irony": {"count": 20, "score_sum": 2},
        })
        self.assertEqual(set(result), {"hard_absurdity", "dark_irony"})
        self.assertTrue(all(-0.22 <= x <= 0.22 for x in result.values()))
        self.assertGreater(result["hard_absurdity"], result["dark_irony"])

    def test_demo_or_failed_report_never_overwrites_weights(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "weights.json"
            self.assertFalse(update_weights({"status": "unavailable",
                                            "cohorts": {}}, file))
            self.assertFalse(file.exists())

    def test_previously_valid_weights_loaded_from_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "weights.json"
            file.write_text(json.dumps({
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "bias": {"hard_absurdity": .16, "dark_irony": -.1,
                         "uncapped": 0.95}
            }), encoding="utf-8")
            self.assertEqual(cached_bias(file), {
                "hard_absurdity": 0.16, "dark_irony": -0.1})


if __name__ == "__main__":
    unittest.main()
