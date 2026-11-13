import unittest
from datetime import datetime, timezone

from queue_audit import queue_audit


NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


def post(slot, status="scheduled", number=1, url=""):
    return {
        "slot": slot, "publication_status": status,
        "vedismm_post_id": number, "vk_url": url,
    }


class QueueAuditTests(unittest.TestCase):
    def test_complete_window_is_healthy(self):
        entries = [post("2026-11-13-12-02", number=1),
                   post("2026-11-13-12-03", number=2),
                   post("2026-11-13-13-00", number=3)]
        report = queue_audit({"posts": entries}, now=NOW, hours=1)
        self.assertEqual(report["expected_slots"], 3)
        self.assertEqual(report["reserved_slots"], 3)
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["missing_slots"], [])

    def test_missing_near_slot_is_urgent_without_destructive_action(self):
        entries = [post("2026-11-13-12-02", number=1)]
        state = {"posts": entries}
        report = queue_audit(state, now=NOW, hours=1)
        self.assertEqual(report["status"], "urgent")
        self.assertEqual(report["reserved_slots"], 1)
        self.assertEqual(report["urgent_missing_slots"],
                         ["2026-11-13-12-03", "2026-11-13-13-00"])
        self.assertEqual(state["posts"], entries)

    def test_unverified_is_not_a_verified_future_reservation(self):
        state = {"posts": [post("2026-11-13-12-02", "requires_attention")]}
        report = queue_audit(state, now=NOW, hours=1)
        self.assertIn("2026-11-13-12-02", report["missing_slots"])
        self.assertIn("2026-11-13-12-02", report["unresolved_in_window"])
        self.assertEqual(report["status"], "urgent")

    def test_duplicate_post_is_flagged_without_republishing(self):
        entries = [post("2026-11-13-12-02", number=1),
                   post("2026-11-13-12-02", number=2),
                   post("2026-11-13-12-03", number=3),
                   post("2026-11-13-13-00", number=4)]
        report = queue_audit({"posts": entries}, now=NOW, hours=1)
        self.assertEqual(report["duplicate_slots"],
                         ["2026-11-13-12-02"])
        self.assertEqual(report["status"], "urgent")

    def test_only_confirmed_vk_url_counted_as_published(self):
        entries = [
            post("2026-11-13-09-00", "published", number=1,
                 url="https://vk.com/wall-243230846_25"),
            post("2026-11-13-09-01", "delivered_unverified", number=2)]
        report = queue_audit({"posts": entries}, now=NOW, hours=1)
        self.assertEqual(report["published_with_vk_url_count"], 1)
        self.assertEqual(report["last_confirmed_vk_url"],
                         "https://vk.com/wall-243230846_25")

    def test_reject_invalid_time(self):
        with self.assertRaises(ValueError):
            queue_audit({}, now=datetime(2026, 11, 13), hours=1)


if __name__ == "__main__":
    unittest.main()
