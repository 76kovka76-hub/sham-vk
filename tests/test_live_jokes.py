import os
import unittest
from unittest.mock import Mock, patch

import requests

from fresh_jokes import FRESH_JOKES
from live_jokes import _coherent_candidate, generate_live_post
from main import generate_post
from quality_guard import approved, validate


class LiveJokeTests(unittest.TestCase):
    @patch("live_jokes.requests.post")
    def test_five_new_jokes_and_correct_picture_brief(self, request):
        samples = FRESH_JOKES[:5]
        candidates = [
            {**{key: row[key] for key in ("top", "bottom", "caption", "visual", "scene")},
             "idea_key": row["topic"].replace("mini_", "")}
            for row in samples
        ]
        fake = Mock()
        fake.json.return_value = {"choices": [{"message": {
            "content": __import__("json").dumps({"candidates": candidates},
                                                 ensure_ascii=False)
        }}]}
        fake.raise_for_status.return_value = None
        request.return_value = fake

        result = generate_live_post({"posts": []}, "2026-11-13-18-00")
        self.assertEqual(result["source"], "ovh_chat_reviewed_v1")
        self.assertTrue(approved(result))
        self.assertTrue(validate(result))
        self.assertIn(result["visual"], [row["visual"] for row in samples])
        self.assertEqual(request.call_count, 1)

    def test_bad_generic_visual_is_rejected(self):
        src = FRESH_JOKES[0]
        draft = {**src, "idea_key": "robot emotions", "visual": "Smiling adult"}
        self.assertIsNone(_coherent_candidate(draft))

    @patch.dict(os.environ, {"SHAM_LIVE_TEXT": "true"})
    @patch("live_jokes.generate_live_post", side_effect=requests.Timeout("free tier busy"))
    def test_free_provider_failure_falls_back_to_curated(self, llm):
        result = generate_post({"posts": [], "slots": []},
                               "2027-04-22-12-00")
        self.assertTrue(validate(result))
        self.assertNotEqual(result.get("source"), "ovh_chat_reviewed_v1")


if __name__ == "__main__":
    unittest.main()
