import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from queue_health import reconcile_scheduled


NOW = datetime(2026, 11, 13, 12, 30, tzinfo=timezone.utc)


def api_post(data):
    result = Mock()
    result.raise_for_status.return_value = None
    result.json.return_value = {"data": data}
    return result


class QueueHealthTests(unittest.TestCase):
    def state(self):
        return {"posts": [
            {"publication_status": "scheduled",
             "vedismm_post_id": 42,
             "scheduled_at": "2026-11-13T12:15:00Z",
             "slot": "2026-11-13-12-01",
             "vk_url": ""},
        ], "slots": ["2026-11-13-12-01"]}

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token"})
    @patch("queue_health.requests.get")
    def test_confirmed_vk_link_updates_history(self, get):
        get.return_value = api_post({
            "status": "published",
            "targets": [{"external_url": "https://vk.com/wall-243230846_1234"}]
        })
        state = self.state()
        result = reconcile_scheduled(state, now=NOW)
        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(state["posts"][0]["publication_status"], "published")
        self.assertEqual(state["posts"][0]["vk_url"],
                         "https://vk.com/wall-243230846_1234")
        self.assertEqual(state["slots"], ["2026-11-13-12-01"])

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token"})
    @patch("queue_health.requests.get")
    def test_different_vk_wall_must_not_count_as_ours(self, get):
        get.return_value = api_post({
            "status": "published",
            "targets": [{"external_url": "https://vk.com/wall-222_1234"},
                        {"external_url": "http://vk.com/wall-243230846_123"}]
        })
        state = self.state()
        result = reconcile_scheduled(state, now=NOW)
        self.assertEqual(state["posts"][0]["publication_status"],
                         "delivered_unverified")
        self.assertEqual(len(result["warnings"]), 1)

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token"})
    @patch("queue_health.requests.get")
    def test_manually_unscheduled_is_not_duplicated(self, get):
        get.return_value = api_post({"status": "draft", "targets": []})
        state = self.state()
        result = reconcile_scheduled(state, now=NOW)
        self.assertEqual(state["posts"][0]["publication_status"],
                         "requires_attention")
        self.assertEqual(state["slots"], ["2026-11-13-12-01"])
        self.assertEqual(len(result["warnings"]), 1)

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token"})
    @patch("queue_health.requests.get")
    def test_remains_scheduled_if_remote_time_matches(self, get):
        get.return_value = api_post({
            "status": "scheduled",
            "scheduled_at": "2026-11-13T12:15:00Z"
        })
        state = self.state()
        result = reconcile_scheduled(state, now=NOW)
        self.assertEqual(state["posts"][0]["publication_status"], "scheduled")
        self.assertEqual(result["updated"], 0)

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token"})
    @patch("queue_health.requests.get")
    def test_unknown_status_does_not_erase_schedule(self, get):
        get.return_value = api_post({"status": "unexpected"})
        state = self.state()
        result = reconcile_scheduled(state, now=NOW)
        self.assertEqual(state["posts"][0]["publication_status"], "scheduled")
        self.assertEqual(len(result["warnings"]), 1)

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token"})
    @patch("queue_health.requests.get")
    def test_old_or_far_future_posts_not_polled(self, get):
        state = self.state()
        state["posts"][0]["scheduled_at"] = "2026-11-09T12:15:00Z"
        result = reconcile_scheduled(state, now=NOW)
        self.assertEqual(result["checked"], 0)
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
