import unittest
from PIL import Image

from main import centered_text, font
from meme_layout import LAYOUTS, layout_for_slot, render_meme


class MemeLayoutTests(unittest.TestCase):
    def test_six_distinct_layouts_in_one_day(self):
        slots = [f"2026-11-13-{h:02d}-{q:02d}"
                 for h in range(24) for q in range(4)]
        styles = [layout_for_slot(s) for s in slots]
        self.assertEqual(set(styles), set(LAYOUTS))
        self.assertTrue(all(a != b for a, b in zip(styles, styles[1:])))

    def test_render_preserves_full_russian_joke(self):
        art = Image.effect_noise((512, 512), 40).convert("RGB")
        joke = {
            "top": "Голубь устроился в агентство недвижимости.",
            "bottom": "Теперь он не гадит на квартиры. Он их продаёт.",
        }
        results = set()
        for h in range(6):
            image, layout = render_meme(
                art, joke, f"2026-11-13-02-{h % 4:02d}"
                if h < 4 else f"2026-11-13-03-{h - 4:02d}",
                font, centered_text)
            self.assertEqual(image.size, (1080, 1080))
            self.assertEqual(image.mode, "RGB")
            self.assertIn(layout, LAYOUTS)
            results.add(image.getpixel((10, 10)))
        self.assertGreaterEqual(len(results), 3)

    def test_invalid_slot_rejected(self):
        for slot in ("wrong", "2026-11-13-25-00", "2026-11-13-03-05"):
            with self.assertRaises(ValueError):
                layout_for_slot(slot)


if __name__ == "__main__":
    unittest.main()
