import unittest
import re
from datetime import datetime, timezone
from unittest.mock import patch

from main import current_slot, generate_post, identity
from hashtags import create_tags, add_hashtags


class FreeMemeTests(unittest.TestCase):
    def test_free_meme_without_external_api(self):
        state = {"posts": [], "slots": []}
        for i in range(100):
            post = generate_post(state, f"test-day-{i}")
            self.assertTrue(post["top"])
            self.assertTrue(post["bottom"])
            self.assertIn(post["scene"], {"work", "wallet", "phone", "home", "social", "life"})
            post_hash = identity(post)
            self.assertNotIn(post_hash, {x["id"] for x in state["posts"]})
            state["posts"].append({**post, "id": post_hash})

    def test_exactly_three_tags_and_never_repeat_triples(self):
        state = {"posts": [], "slots": []}
        seen = set()
        for i in range(100):
            slot = f"2026-11-12-01-{i:03d}"
            scene = ("work", "wallet", "phone", "home", "social", "life")[i % 6]
            tags = create_tags(scene, state, slot)
            self.assertEqual(3, len(tags))
            self.assertEqual(3, len(set(tags)))
            self.assertTrue(all(re.fullmatch(r"#[\w]+", tag) for tag in tags))
            signature = tuple(sorted(tags))
            self.assertNotIn(signature, seen)
            seen.add(signature)
            state["posts"].append({"hashtags": tags})
            published = add_hashtags("Подпись", tags)
            self.assertEqual(3, published.count("#"))

    def test_no_hashtag_reuse_in_last_12_when_candidates_available(self):
        state = {"posts": [], "slots": []}
        for i in range(30):
            scene = ("work", "wallet", "phone", "home", "social", "life")[i % 6]
            recent = {tag for post in state["posts"][-12:] for tag in post["hashtags"]}
            tags = create_tags(scene, state, f"hash-test-{i}")
            self.assertTrue(recent.isdisjoint(tags))
            state["posts"].append({"hashtags": tags})

    def test_slot_is_15_minutes(self):
        class FixedDatetime:
            @classmethod
            def now(cls, tz):
                return datetime(2026, 11, 12, 14, 31, tzinfo=timezone.utc)
        with patch("main.datetime", FixedDatetime):
            self.assertEqual(current_slot(), "2026-11-12-14-02")

    def test_hashtag_validation(self):
        with self.assertRaises(ValueError):
            add_hashtags("text", ["#мемы", "#мемы", "#шутки"])
        with self.assertRaises(ValueError):
            add_hashtags("text", ["#мемы", "#шутки"])


if __name__ == "__main__":
    unittest.main()
