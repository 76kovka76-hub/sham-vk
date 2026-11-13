import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from editorial_experiments import LANES, choose_candidate, lane_for_slot, score_post
from sham_insights import fetch_analytics, observed_metrics, summarize
from community_signals import extract_themes, gather, cached_themes
from fresh_jokes import FRESH_JOKES


class InsightsTests(unittest.TestCase):
    def test_never_count_demo_data_or_unavailable_metrics(self):
        self.assertEqual(observed_metrics({
            "is_demo": True, "available_metrics": ["likes"],
            "likes": 999999}), {})
        self.assertEqual(observed_metrics({
            "is_demo": False, "available_metrics": ["likes"],
            "likes": 12, "shares": 999}), {"likes": 12.0})

    def test_rank_only_our_confirmed_published_vk_posts(self):
        local = {"posts": [
            {"publication_status": "published", "vedismm_post_id": 50,
             "vk_url": "https://vk.com/wall-243230846_1",
             "image_source": {"style": "photomontage"},
             "humor_lane": "hard_absurdity", "top": "Новый мем", "bottom": "Концовка"},
            {"publication_status": "scheduled", "vedismm_post_id": 51,
             "vk_url": "", "image_source": {"style": "anime"}},
        ]}
        remote = {"status": "ok", "posts": [
            {"id": 50, "likes": 20, "shares": 4, "comments": 6, "reach": 300,
             "is_demo": False,
             "available_metrics": ["likes", "shares", "comments", "reach"]},
            {"id": 51, "likes": 999, "shares": 999, "reach": 1000,
             "is_demo": False, "available_metrics": ["likes", "shares", "reach"]},
            {"id": 52, "likes": 99, "shares": 99, "reach": 1000,
             "is_demo": False, "available_metrics": ["likes", "shares", "reach"]},
        ]}
        report = summarize(local, remote)
        self.assertEqual(report["observed_posts"], 1)
        self.assertEqual(report["top"][0]["vk_url"],
                         "https://vk.com/wall-243230846_1")
        self.assertFalse(next(iter(report["experiments"].values()))["sufficient_samples"])

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"}, clear=True)
    @patch("sham_insights._find_account_id", return_value=42)
    def test_analytics_scope_denied_doesnt_stop_publisher(self, acc):
        reply = Mock(status_code=403)
        result = fetch_analytics(
            now=datetime(2026, 11, 13, tzinfo=timezone.utc),
            getter=lambda *args, **kwargs: reply)
        self.assertEqual(result["reason"], "missing_analytics_scope")

    def test_experiment_variants_cycle(self):
        slots = [f"2026-11-13-{h:02d}-{q:02d}"
                 for h in range(24) for q in range(4)]
        self.assertEqual(set(lane_for_slot(s) for s in slots), set(LANES))
        self.assertTrue(all(a != b for a, b in zip(
            [lane_for_slot(s) for s in slots],
            [lane_for_slot(s) for s in slots][1:])))

    def test_editor_prefers_readable_specific_joke(self):
        original = dict(FRESH_JOKES[0])
        original["humor_lane"] = lane_for_slot("2026-11-13-15-02")
        awful = dict(original)
        awful["visual"] = "person"
        self.assertLess(score_post(awful), 0)
        chosen = choose_candidate([awful, original], [], "2026-11-13-15-02")
        self.assertEqual(chosen["visual"], original["visual"])
        self.assertGreater(chosen["editorial_score"], 0)


class CommentSignalsTests(unittest.TestCase):
    def test_only_general_themes_never_raw_comments(self):
        themes = extract_themes("Мой кот и робот-пылесос стали лучшими друзьями")
        self.assertEqual(themes, {"животные", "роботы"})

    @patch.dict("os.environ", {"VK_GROUP_TOKEN": "fake"}, clear=True)
    def test_group_comment_count_anonymizes_data(self):
        post = {"posts": [{"publication_status": "published",
                           "vk_url": "https://vk.com/wall-243230846_123"}]}
        payload = {"response": {"items": [
            {"from_id": 123456, "text": "Хочу больше шуток про роботов, роботов!"}, 
            {"from_id": 123456, "text": "Мой робот опять сломался и смеется"},
            {"from_id": 654321, "text": "Жду еще смешные шутки про роботов"},
        ]}}
        reply = Mock()
        reply.raise_for_status.return_value = None
        reply.json.return_value = payload
        report = gather(post, caller=lambda *args, **kwargs: reply)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["topics"],
                         [{"name": "роботы", "unique_commenters": 2}])
        self.assertNotIn("123456", json.dumps(report))

    def test_unavailable_comments_do_not_fail(self):
        self.assertEqual(gather({"posts": []})["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
