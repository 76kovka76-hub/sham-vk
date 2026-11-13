import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from sham_motion import make_motion_previews, reveal_frames
from sham_weekly_top import draw_top, weekly_top


class NewFormatsTests(unittest.TestCase):
    def test_gif_punchline_reveal_and_final_full_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "original.png"
            img = Image.effect_noise((600, 600), 45).convert("RGB")
            img.save(src)
            frames = reveal_frames(src)
            self.assertEqual(len(frames), 10)
            self.assertNotEqual(frames[0].getpixel((200, 600)),
                                frames[-1].getpixel((200, 600)))
            files = make_motion_previews(src, Path(temp) / "preview",
                                         render_mp4=False)
            gif = Path(files["gif"])
            self.assertTrue(gif.is_file())
            with Image.open(gif) as im:
                self.assertGreater(im.n_frames, 1)
                self.assertEqual(im.size, (720, 720))
            self.assertIsNone(files["mp4"])

    def test_weekly_poster_fails_closed_with_two_posts(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "three"):
                draw_top([{"post_id": 1}, {"post_id": 2}],
                         Path(folder) / "top.png")

    def test_weekly_poster_from_three_real_posts(self):
        items = [
            {"post_id": i, "caption": "Смешная ситуация с голубем и роботом — он уволился",
             "vk_url": f"https://vk.com/wall-243230846_{i}"}
            for i in (1, 2, 3)
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = draw_top(items, Path(folder) / "top.png")
            with Image.open(path) as img:
                self.assertEqual(img.size, (1080, 1080))

    def test_top_does_not_publish_if_not_sunday(self):
        self.assertEqual(weekly_top(now=datetime(2026, 11, 13, 12,
                                                 tzinfo=timezone.utc)),
                         {"status": "skipped", "reason": "not_sunday"})


if __name__ == "__main__":
    unittest.main()
