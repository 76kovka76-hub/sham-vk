import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from horde_style import make_horde_image
from vision_review import review_visual


def post():
    return {
        "topic": "mini_taxi_scene", "scene": "life",
        "visual": "Realistic city minibus full of passengers exchanging a shawarma and a smartphone",
        "top": "Передайте за проезд.", "bottom": "Мне передали шаурму и телефон.",
    }


class PhotoDeliveryGateTests(unittest.TestCase):
    @patch.dict("os.environ", {
        "SHAM_PHOTO_ONLY": "true", "SHAM_FREE_IMAGE_PROVIDER": "ovh",
        "SHAM_VISION_CHECK": "strict", "SHAM_IMAGE_ATTEMPTS": "2"
    })
    @patch("horde_style.render_meme")
    @patch("horde_style.review_visual")
    @patch("horde_style.validate_artwork")
    @patch("sham_free_image.generate_image")
    def test_reject_mismatched_candidate_and_retry_different_source(
        self, generate, basic, vision, layout
    ):
        photo = Image.effect_noise((512, 512), 55).convert("RGB")
        generate.return_value = photo, {"service": "test", "style": "realistic"}
        basic.return_value = {"image_qa": "passed_basic_image_checks"}
        vision.side_effect = [
            RuntimeError("SHAM image disagrees: unrelated beach man"),
            {"vision_review": "matched", "vision_photo_like": True},
        ]
        layout.return_value = Image.new("RGB", (1080, 1080), "gray"), "editorial"
        with tempfile.TemporaryDirectory() as tmp:
            img = make_horde_image(post(), "2026-11-14-15-00",
                                   Path(tmp), Mock(), Mock())
            self.assertTrue(img.exists())
            self.assertEqual(generate.call_count, 2)
            self.assertIn("-photo-retry-2", generate.call_args.args[1])
            self.assertEqual(vision.call_count, 2)
            self.assertIn('"image_attempt": 2',
                          (Path(tmp) / "image_source.json").read_text())

    @patch.dict("os.environ", {
        "SHAM_PHOTO_ONLY": "true", "SHAM_FREE_IMAGE_PROVIDER": "ovh",
        "SHAM_VISION_CHECK": "strict", "SHAM_IMAGE_ATTEMPTS": "2"
    })
    @patch("horde_style.render_meme")
    @patch("horde_style.review_visual",
           side_effect=RuntimeError("image is actually anime"))
    @patch("horde_style.validate_artwork",
           return_value={"image_qa": "passed_basic_image_checks"})
    @patch("sham_free_image.generate_image")
    def test_never_schedule_unverified_anime(self, generate, basic, vision, layout):
        photo = Image.effect_noise((512, 512), 55).convert("RGB")
        generate.return_value = photo, {"service": "test"}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "nothing sent to VediSMM"):
                make_horde_image(post(), "2026-11-14-15-00",
                                 Path(tmp), Mock(), Mock())
            layout.assert_not_called()
            self.assertFalse((Path(tmp) / "sham_meme.png").exists())
            self.assertEqual(generate.call_count, 2)

    @patch.dict("os.environ", {"SHAM_PHOTO_ONLY": "true"})
    def test_a_drawn_image_is_rejected_even_when_objects_match(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"choices": [{"message": {"content":
            '{"matches":true,"photo_like":false,"confidence":0.98,"reason":"anime illustration"}'}}]}
        with self.assertRaisesRegex(RuntimeError, "non-photographic"):
            review_visual(
                Image.effect_noise((512, 512), 55).convert("RGB"), post(),
                mode="strict", request=lambda *args, **kwargs: response)


if __name__ == "__main__":
    unittest.main()
