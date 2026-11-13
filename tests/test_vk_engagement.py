import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from sham_insights import fetch_vk_stats, fetch_best_analytics, summarize


class VKEngagementTests(unittest.TestCase):
    def _history(self):
        return {"posts": [
            {"publication_status": "published",
             "slot": "2026-11-13-12-00",
             "vedismm_post_id": 5001,
             "vk_url": "https://vk.com/wall-243230846_85",
             "top": "Сходил к роботу", "bottom": "Он меня уволил",
             "image_source": {"style": "cinematic"},
             "humor_lane": "hard_absurdity"}
        ]}

    @patch.dict("os.environ", {"VK_USER_TOKEN": "dummy"}, clear=True)
    def test_real_vk_wall_counters_only(self):
        reply = Mock()
        reply.raise_for_status.return_value = None
        reply.json.return_value = {"response": [
            {"id": 85, "owner_id": -243230846, "likes": {"count": 7},
             "reposts": {"count": 3}, "comments": {"count": 2},
             "views": {"count": 240}},
            {"id": 86, "owner_id": -243230846, "likes": {"count": 999},
             "reposts": {"count": 999}},
            {"id": 85, "owner_id": -999, "likes": {"count": 999},
             "reposts": {"count": 999}},
        ]}
        def client(url, *, params, timeout):
            self.assertIn("wall.getById", url)
            self.assertEqual(params["posts"], "-243230846_85")
            return reply
        report = fetch_vk_stats(self._history(),
                                now=datetime(2026, 11, 13, tzinfo=timezone.utc),
                                getter=client)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(len(report["posts"]), 1)
        self.assertEqual(report["posts"][0]["id"], 5001)
        self.assertEqual(report["posts"][0]["shares"], 3)
        self.assertEqual(report["posts"][0]["impressions"], 240)
        summary = summarize(self._history(), report)
        self.assertEqual(summary["observed_posts"], 1)

    @patch.dict("os.environ", {"VK_USER_TOKEN": "dummy"}, clear=True)
    def test_denied_vk_access_does_not_report_fake_stats(self):
        reply = Mock()
        reply.raise_for_status.return_value = None
        reply.json.return_value = {"error": {"error_code": 5}}
        outcome = fetch_vk_stats(
            self._history(), now=datetime(2026, 11, 13, tzinfo=timezone.utc),
            getter=lambda *args, **kwargs: reply)
        self.assertEqual(outcome["status"], "unavailable")
        self.assertFalse(outcome["posts"])

    @patch.dict("os.environ", {}, clear=True)
    def test_no_vk_token_yields_no_metrics(self):
        outcome = fetch_vk_stats(self._history())
        self.assertEqual(outcome["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
