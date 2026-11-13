import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from queue_cleanup import clean_legacy_queue


def response(data, etag=None):
    reply = Mock()
    reply.json.return_value = {"data": data}
    reply.headers = {"ETag": etag} if etag else {}
    reply.raise_for_status.return_value = None
    return reply


class SafeAnimeRefreshTests(unittest.TestCase):
    def _entry(self, ident, style="anime", version=2, minutes=240):
        return {
            "vedismm_post_id": ident,
            "publication_status": "scheduled",
            "quality_version": version,
            "image_source": {"style": style},
            "scheduled_at": (datetime.now(timezone.utc)
                             + timedelta(minutes=minutes)).isoformat(),
            "slot": f"2027-01-01-01-{ident % 4:02d}",
        }

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"})
    @patch("queue_cleanup.requests.post")
    @patch("queue_cleanup.requests.get")
    def test_only_one_distant_old_anime_is_unscheduled(self, get, post):
        old1 = self._entry(5001)
        old2 = self._entry(5002)
        realistic = self._entry(5003, style="realistic")
        new = self._entry(5004, style="anime", version=3)
        history = {"posts": [old1, old2, realistic, new],
                   "slots": [x["slot"] for x in [old1, old2, realistic, new]]}
        get.return_value = response(
            {"id": 5001, "version": 2, "status": "scheduled"}, '"v2"')
        post.return_value = response({"id": 5001, "status": "draft"})
        report = clean_legacy_queue(history, replace_outdated_anime=True,
                                    max_changes=1)
        self.assertEqual(report["unscheduled"], [5001])
        self.assertEqual(post.call_count, 1)
        self.assertEqual(old1["publication_status"], "unscheduled_low_quality")
        self.assertNotIn(old1["slot"], history["slots"])
        self.assertEqual(old2["publication_status"], "scheduled")
        self.assertEqual(realistic["publication_status"], "scheduled")
        self.assertEqual(new["publication_status"], "scheduled")

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"})
    @patch("queue_cleanup.requests.post")
    @patch("queue_cleanup.requests.get")
    def test_near_future_and_published_are_untouched(self, get, post):
        imminent = self._entry(6001, minutes=30)
        published = self._entry(6002, minutes=300)
        published["publication_status"] = "published"
        state = {"posts": [imminent, published],
                 "slots": [imminent["slot"], published["slot"]]}
        result = clean_legacy_queue(state, replace_outdated_anime=True,
                                    max_changes=1)
        self.assertEqual(result["unscheduled"], [])
        post.assert_not_called()
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
