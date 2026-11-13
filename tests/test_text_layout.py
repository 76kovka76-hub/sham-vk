import unittest

from PIL import Image, ImageDraw

from main import centered_text


class CaptionLayoutTests(unittest.TestCase):
    def test_russian_profanity_readably_typeset(self):
        image = Image.new("RGB", (1080, 1080), (20, 20, 20))
        draw = ImageDraw.Draw(image)
        centered_text(draw, "Теперь на нас орёт кофемашина. Зато не врёт, что мы семья.",
                      812, 1018, (255, 240, 30), 72)
        self.assertNotEqual(image.getpixel((540, 850)), (255, 255, 255))

    def test_overflow_is_rejected_instead_of_tiny_unreadable_letters(self):
        image = Image.new("RGB", (1080, 1080))
        draw = ImageDraw.Draw(image)
        text = "Это очень длинная шутка, " * 45
        with self.assertRaisesRegex(ValueError, "readably"):
            centered_text(draw, text, 812, 1018, (255, 240, 30), 72)


if __name__ == "__main__":
    unittest.main()
