import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from editorial_jokes import EDITORIAL_JOKES
from quality_bank import TOPICS
from quality_guard import approved, joke_id, select_post, validate
from queue_planner import next_missing_slot
from queue_audit import queue_audit


class QualityFirstTests(unittest.TestCase):
    def test_all_new_editing_pairs_are_complete_unique_and_visual(self):
        self.assertGreaterEqual(len(EDITORIAL_JOKES), 40)
        self.assertEqual(len({p["topic"] for p in EDITORIAL_JOKES}), len(EDITORIAL_JOKES))
        self.assertEqual(len({joke_id(p) for p in EDITORIAL_JOKES}), len(EDITORIAL_JOKES))
        for item in EDITORIAL_JOKES:
            self.assertTrue(approved(item))
            self.assertTrue(validate(item))
            self.assertGreaterEqual(len(item["visual"].split()), 10)
            self.assertTrue(any(word in item["visual"].lower()
                                for word in ("realistic", "photo", "documentary",
                                             "cinematic", "surreal", "candid",
                                             "portrait", "absurd")))

    @patch.dict(os.environ, {"SHAM_EDITORIAL_MODE": "quality_first"}, clear=False)
    def test_strict_production_never_uses_mixed_thematic_bank(self):
        state = {"posts": [], "slots": []}
        legacy_topics = {topic["topic"] for topic in TOPICS}
        for n in range(40):
            slot = f"2026-12-{1+n//96:02d}-{(n//4)%24:02d}-{n%4:02d}"
            post = select_post(state, slot)
            self.assertTrue(approved(post))
            self.assertNotIn(post["topic"], legacy_topics)
            self.assertTrue(post["topic"].startswith("mini_"))
            state["posts"].append({**post, "id": joke_id(post)})

    @patch.dict(os.environ, {"SHAM_EDITORIAL_MODE": "quality_first"}, clear=False)
    def test_quality_first_skips_when_finite_pool_exhausted(self):
        from quality_guard import QUALITY_BACKUP_TOPICS
        used = [
            {**post, "id": joke_id(post)}
            for post in (EDITORIAL_JOKES +
                         [p for m in ("fresh_jokes", "hard_jokes")
                          for p in getattr(__import__(m), 
                                           "FRESH_JOKES" if m=="fresh_jokes" else "HARD_JOKES")
                          if p["topic"] in QUALITY_BACKUP_TOPICS])
        ]
        with self.assertRaisesRegex(RuntimeError, "skipping slot"):
            select_post({"posts": used}, "2027-01-01-01-00")

    def test_hourly_targets_ignore_stale_quarter_hour_reservations(self):
        now = datetime(2026, 11, 13, 12, 2, tzinfo=timezone.utc)
        old = {"slots": ["2026-11-13-12-03"]}
        slot, when = next_missing_slot(old, now, step_minutes=60)
        self.assertEqual(slot, "2026-11-13-13-00")
        self.assertEqual(when.hour, 13)
        self.assertEqual(when.minute, 0)
        second, _ = next_missing_slot({"slots": [slot]}, now, step_minutes=60)
        self.assertEqual(second, "2026-11-13-14-00")
        report = queue_audit({"posts": [
            {"slot": slot, "publication_status": "scheduled"},
        ]}, now=now, hours=2, step_minutes=60)
        self.assertEqual(report["expected_slots"], 2)
        self.assertEqual(report["reserved_slots"], 1)
        self.assertEqual(report["missing_slots"], [second])


if __name__ == "__main__":
    unittest.main()
