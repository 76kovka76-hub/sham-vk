import unittest
from PIL import Image

from image_guard import (fingerprint, distance, validate_artwork,
                         validate_joke_visual_brief)


class ImageGuardTests(unittest.TestCase):
    def test_photo_candidate_passes_and_has_recorded_visual_hash(self):
        image = Image.effect_noise((512, 512), 60).convert("RGB")
        report = validate_artwork(image)
        self.assertEqual(report["image_qa"], "passed_basic_image_checks")
        self.assertEqual(report["visual_hash"], fingerprint(image))
        self.assertGreater(report["image_entropy"], 2)

    def test_blank_image_is_not_scheduled(self):
        with self.assertRaisesRegex(ValueError, "blank"):
            validate_artwork(Image.new("RGB", (512, 512), "white"))

    def test_small_image_is_not_scheduled(self):
        with self.assertRaisesRegex(ValueError, "undersized"):
            validate_artwork(Image.new("RGB", (400, 500), "white"))

    def test_repeated_image_is_not_scheduled_even_with_new_caption(self):
        image = Image.effect_noise((512, 512), 60).convert("RGB")
        old = {"posts": [{
            "image_source": {"visual_hash": fingerprint(image)},
            "top": "Старый мем", "bottom": "Старый текст",
        }]}
        with self.assertRaisesRegex(ValueError, "repeated"):
            validate_artwork(image, old)

    def test_different_visual_hashes_not_mistaken_as_same(self):
        self.assertEqual(distance("0000000000000000", "ffffffffffffffff"), 64)

    def test_unrelated_prompt_scene_is_blocked(self):
        scene = "Realistic pigeon wearing a necktie selling an apartment"
        with self.assertRaisesRegex(ValueError, "omitted"):
            validate_joke_visual_brief({"visual": scene}, "A generic smiling anime employee")

    def test_specific_prompt_scene_is_preserved(self):
        scene = "Realistic pigeon wearing a necktie selling an apartment"
        self.assertTrue(validate_joke_visual_brief(
            {"visual": scene}, "Specific scene: " + scene + "."))
