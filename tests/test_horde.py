import unittest
from unittest.mock import Mock, patch

from PIL import Image

from horde_style import build_prompt, generate_image, style_for_slot
from style_catalog import STYLE_PROMPTS, PHOTO_STYLES, story_style


def reply(data):
    r = Mock()
    r.status_code = 200
    r.json.return_value = data
    r.raise_for_status.return_value = None
    return r


class AIHordeTests(unittest.TestCase):
    def test_96_posts_have_many_visual_genres_and_no_anime_monopoly(self):
        slots = [f"2026-11-13-{h:02d}-{q:02d}"
                 for h in range(24) for q in range(4)]
        styles = [style_for_slot(slot) for slot in slots]
        self.assertGreaterEqual(len(set(styles)), 28)
        self.assertLessEqual(styles.count("anime"), 5)
        self.assertGreaterEqual(sum(s in PHOTO_STYLES for s in styles), 55)
        self.assertTrue(all(a != b for a, b in zip(styles, styles[1:])))
        self.assertTrue(all(style in STYLE_PROMPTS for style in styles))

    def test_incompatible_macro_or_sports_style_is_avoided_for_conference(self):
        story = {"topic": "mini_press_conference",
                 "visual": "Photorealistic conference with officials and ten angry tenants"}
        for style in ("macro_photo", "miniature_photo", "sports_photo", "fashion_photo"):
            slot = next(s for s in (
                f"2026-11-13-{h:02d}-{q:02d}"
                for h in range(24) for q in range(4)
            ) if style_for_slot(s) == style)
            self.assertNotEqual(story_style(story, slot), style)

    def test_macro_allowed_when_punchline_is_tiny_physical_gag(self):
        slot = next(s for s in (
            f"2026-11-13-{h:02d}-{q:02d}"
            for h in range(24) for q in range(4)
        ) if style_for_slot(s) == "macro_photo")
        self.assertEqual(story_style({
            "topic": "mini_tiny_teacup",
            "visual": "Tiny paper dragon inside miniature ceramic coffee cup"
        }, slot), "macro_photo")

    def test_no_real_person_name_or_embedded_captions(self):
        post = {"scene": "work"}
        real = build_prompt(post, "2026-11-13-00-00", "realistic")
        anime = build_prompt(post, "2026-11-13-01-01", "anime")
        self.assertIn("fictional", real)
        self.assertIn("Hyperrealistic", real)
        self.assertIn("anime", anime)
        self.assertIn("no visible letters", real)
        self.assertIn("no visible letters", anime)

    def test_invalid_slot_is_not_anime_by_accident(self):
        for slot in ("invalid", "2026-11-12-28-00", "2026-11-12-00-15"):
            with self.assertRaises(ValueError):
                style_for_slot(slot)

    @patch("horde_style._download")
    @patch("horde_style.time.sleep", return_value=None)
    @patch("horde_style.requests.get")
    @patch("horde_style.requests.post")
    def test_generation_then_remote_status(self, post, get, sleep, download):
        post.return_value = reply({"id": "fictitious-job"})
        get.side_effect = [
            reply({"done": False, "faulted": False, "is_possible": True}),
            reply({"done": True, "faulted": False, "is_possible": True}),
            reply({"generations": [{
                "img": "https://example.org/fictional.png",
                "censored": False,
                "model": "mock-model",
                "seed": "1",
                "worker_name": "test"
            }]}),
        ]
        download.return_value = Image.new("RGB", (512, 512))
        image, metadata = generate_image(
            {"scene": "phone"}, "2026-11-13-01-01", "anime", deadline_seconds=30
        )
        self.assertEqual(image.size, (512, 512))
        self.assertEqual(metadata["style"], "anime")
        self.assertEqual(metadata["service"], "ai_horde")
        self.assertEqual(post.call_count, 1)
        sent = post.call_args.kwargs["json"]
        self.assertFalse(sent["nsfw"])
        self.assertIn("anime", sent["prompt"])
        self.assertIn("apikey", post.call_args.kwargs["headers"])

    @patch("horde_style.time.sleep", return_value=None)
    @patch("horde_style.requests.get")
    @patch("horde_style.requests.post")
    def test_faulted_job_is_never_published(self, post, get, sleep):
        post.return_value = reply({"id": "fictitious-job"})
        get.return_value = reply({"done": False, "faulted": True})
        with self.assertRaisesRegex(RuntimeError, "faulted"):
            generate_image({"scene": "life"}, "2026-11-13-01-01", "anime", deadline_seconds=30)


if __name__ == "__main__":
    unittest.main()
