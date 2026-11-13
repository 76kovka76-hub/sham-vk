import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from horde_style import build_prompt
from style_catalog import PHOTO_FIRST_ORDER, story_style
from review_queue_once import mark_rejected_future, ILLUSTRATED_STYLES
from sham_free_image import generate_image as generate_sdxl


class NeverAnimeInNewSHAMPostsTests(unittest.TestCase):
    @patch.dict("os.environ", {"SHAM_PHOTO_ONLY": "true"}, clear=False)
    def test_anime_cartoon_paintings_never_selected_by_production(self):
        post = {"topic": "mini_park_absurdity", "scene": "life",
                "visual": "Photorealistic pigeon demands an apartment lease outside a cafe"}
        slots = [f"2026-11-14-{h:02d}-{q:02d}"
                 for h in range(24) for q in range(4)]
        styles = [story_style(post, slot) for slot in slots]
        self.assertGreaterEqual(len(set(styles)), 15)
        self.assertTrue(all(style in PHOTO_FIRST_ORDER for style in styles))
        self.assertFalse(set(styles) & ILLUSTRATED_STYLES)

    @patch.dict("os.environ", {"SHAM_PHOTO_ONLY": "true"}, clear=False)
    def test_prompt_requires_camera_not_anime(self):
        post = {"topic": "mini_bench_business", "scene": "life",
                "visual": "Realistic old man with his own stool in a park renting chairs"}
        slot = "2026-11-14-13-00"
        style = story_style(post, slot)
        prompt = build_prompt(post, slot, style)
        self.assertIn("Actual live-action photographic capture", prompt)
        self.assertIn("Real-life reportage photograph", prompt)
        self.assertNotIn("anime", prompt.lower())
        self.assertIn("stool in a park", prompt)

    def test_scheduled_illustration_flags_only_safe_future_not_published(self):
        now = datetime(2026, 11, 13, 16, tzinfo=timezone.utc)
        future = (now + timedelta(hours=4)).isoformat()
        imminent = (now + timedelta(minutes=15)).isoformat()
        state = {"posts": [
            {"publication_status": "scheduled", "vedismm_post_id": 8001,
             "scheduled_at": future, "image_source": {"style": "anime"}},
            {"publication_status": "scheduled", "vedismm_post_id": 8002,
             "scheduled_at": future, "image_source": {"style": "watercolor"}},
            {"publication_status": "scheduled", "vedismm_post_id": 8003,
             "scheduled_at": future, "image_source": {"style": "realistic"}},
            {"publication_status": "published", "vedismm_post_id": 8004,
             "scheduled_at": future, "image_source": {"style": "anime"}},
            {"publication_status": "scheduled", "vedismm_post_id": 8005,
             "scheduled_at": imminent, "image_source": {"style": "claymation"}},
        ]}
        self.assertEqual(mark_rejected_future(state, now=now), 2)
        self.assertTrue(state["posts"][0]["review_rejected"])
        self.assertTrue(state["posts"][1]["review_rejected"])
        self.assertFalse(any(p.get("review_rejected", False)
                             for p in state["posts"][2:]))

    @patch.dict("os.environ", {"SHAM_PHOTO_ONLY": "true"}, clear=False)
    @patch("sham_free_image.requests.post")
    def test_sdxl_prompt_is_photographic_even_for_absurd_story(self, post):
        post.return_value.status_code = 503
        post.return_value.raise_for_status.side_effect = __import__("requests").HTTPError("down")
        with self.assertRaises(__import__("requests").HTTPError):
            generate_sdxl({
                "topic": "mini_lamp", "scene": "social",
                "visual": "A photo of a physical light bulb holding a microphone at a press conference"
            }, "2026-11-14-13-00", "photojournalism")
        requested = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("RAW PHOTOGRAPH", requested)
        self.assertIn("RAW REAL-WORLD PHOTOGRAPH", requested)
        self.assertNotIn("anime", requested.lower())
        self.assertIn("light bulb holding a microphone", requested)


if __name__ == "__main__":
    unittest.main()
