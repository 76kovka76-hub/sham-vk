import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from queue_cleanup import clean_legacy_queue


def rsp(data, etag=None):
    r = Mock()
    r.json.return_value = {"data": data}
    r.raise_for_status.return_value = None
    r.headers = {"ETag": etag} if etag else {}
    return r


class QueueCleanupTests(unittest.TestCase):
    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"})
    @patch("queue_cleanup.requests.post")
    @patch("queue_cleanup.requests.get")
    def test_get_weak_etag_is_translated_to_strong_if_version_matches(self, get, post):
        future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        history = {"posts": [{
            "publication_status": "scheduled", "vedismm_post_id": 4967,
            "slot": "2027-01-01-00-01", "scheduled_at": future,
        }], "slots": ["2027-01-01-00-01"]}
        get.return_value = rsp({"id": 4967, "version": 2,
                                "status": "scheduled"}, etag='W/"v2"')
        post.return_value = rsp({"id": 4967, "status": "draft"})
        result = clean_legacy_queue(history)
        self.assertEqual(result["unscheduled"], [4967])
        self.assertEqual(post.call_args.kwargs["headers"]["If-Match"], '"v2"')
        self.assertEqual(history["posts"][0]["publication_status"], "unscheduled_low_quality")

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"})
    @patch("queue_cleanup.requests.post")
    @patch("queue_cleanup.requests.get")
    def test_unschedules_only_legacy_post_with_matching_etag(self, get, post):
        future = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
        history = {"posts": [
            {"publication_status": "scheduled", "vedismm_post_id": 4966,
             "slot": "2027-01-01-00-00", "scheduled_at": future},
            {"publication_status": "scheduled", "vedismm_post_id": 5000,
             "slot": "2027-01-01-00-01", "scheduled_at": future,
             "quality_version": 2},
        ], "slots": ["2027-01-01-00-00", "2027-01-01-00-01"]}
        get.return_value = rsp({"id": 4966, "status": "scheduled"},
                               etag='"post-4966-v1"')
        post.return_value = rsp({"id": 4966, "status": "draft"})
        result = clean_legacy_queue(history)
        self.assertEqual(result["unscheduled"], [4966])
        self.assertEqual(post.call_count, 1)
        self.assertTrue(post.call_args.kwargs["headers"]["If-Match"])
        self.assertIn("/posts/4966/unschedule", post.call_args.args[0])
        self.assertEqual(history["posts"][0]["publication_status"],
                         "unscheduled_low_quality")
        self.assertEqual(history["posts"][1]["publication_status"], "scheduled")
        self.assertNotIn("2027-01-01-00-00", history["slots"])
        self.assertIn("2027-01-01-00-01", history["slots"])

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"})
    @patch("queue_cleanup.requests.post")
    @patch("queue_cleanup.requests.get")
    def test_never_unschedules_already_published(self, get, post):
        history = {"posts": [{"publication_status": "scheduled",
                              "vedismm_post_id": 4966,
                              "slot": "2026-11-12-21-03"}],
                   "slots": ["2026-11-12-21-03"]}
        get.return_value = rsp({"id": 4966, "status": "published"})
        result = clean_legacy_queue(history)
        post.assert_not_called()
        self.assertEqual(result["unscheduled"], [])
        self.assertEqual(history["posts"][0]["publication_status"],
                         "delivered_unverified")
        self.assertIn("2026-11-12-21-03", history["slots"])


if __name__ == "__main__":
    unittest.main()
