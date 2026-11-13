import sys
import unittest
from pathlib import Path
from PIL import Image, ImageChops

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pencil_gags import decorate_email_comic, hand_text, evil_letter


class SKRBLGagTests(unittest.TestCase):
    def test_all_four_gags_render_without_network_or_errors(self):
        for i in range(4):
            img=Image.new("RGB",(1536,1536),(245,240,227))
            before=img.copy()
            decorate_email_comic(img,i,35,35,720,720)
            self.assertIsNotNone(ImageChops.difference(img,before).getbbox())

    def test_no_publishing_unapproved_art_from_a_simple_gag(self):
        with self.assertRaises(ValueError):
            decorate_email_comic(Image.new("RGB",(1536,1536)),
                                 4,35,35,720,720)

    def test_russian_hand_lettering_and_prof_mask(self):
        img=Image.new("RGB",(1536,1536),"white")
        hand_text(img,"БЛ***Ь. НА*** Я ЕЁ ОТКРЫЛ?!",
                  x=35,y=100,max_width=720,max_size=40,seed=3)
        self.assertIsNotNone(ImageChops.difference(
            img,Image.new("RGB",(1536,1536),"white")).getbbox())


if __name__ == "__main__":
    unittest.main()
