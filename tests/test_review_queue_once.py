import unittest
from datetime import datetime, timedelta, timezone

from review_queue_once import REJECTED_QUEUED_IDS, mark_rejected_future


NOW = datetime(2026, 11, 13, 16, tzinfo=timezone.utc)


def entry(pid, status, minutes):
    return {
        "vedismm_post_id": pid,
        "publication_status": status,
        "scheduled_at": (NOW + timedelta(minutes=minutes)).isoformat(),
        "slot": "2026-11-13-20-00",
        "quality_version": 3,
    }


class EditorialQueueReviewTests(unittest.TestCase):
    def test_only_far_future_weak_posts_flagged(self):
        ids = sorted(REJECTED_QUEUED_IDS)
        state = {"posts": [entry(ids[0], "scheduled", 150),
                            entry(ids[1], "scheduled", 40),
                            entry(ids[2], "published", 200),
                            entry(90000, "scheduled", 240)]}
        count = mark_rejected_future(state, now=NOW)
        self.assertEqual(count, 1)
        self.assertTrue(state["posts"][0]["review_rejected"])
        for item in state["posts"][1:]:
            self.assertFalse(item.get("review_rejected", False))

    def test_never_touch_published_even_with_stale_booked_id(self):
        state = {"posts": [entry(5113, "published", 180)]}
        self.assertEqual(mark_rejected_future(state, now=NOW), 0)
        self.assertNotIn("review_rejected", state["posts"][0])


if __name__ == "__main__":
    unittest.main()
