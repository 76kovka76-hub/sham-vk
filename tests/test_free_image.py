"""Offline test of free OVH image generator and per-joke style metadata."""
import base64
import io
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from sham_free_image import generate_image


class FreeImageTests(unittest.TestCase):
    @patch("sham_free_image.requests.post")
    def test_photomontage_preserves_matching_scene(self, request):
        img = Image.effect_noise((512, 512), 40).convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        reply = Mock()
        reply.status_code = 200
        reply.json.return_value = {"data": [{"b64_json": encoded}]}
        reply.raise_for_status.return_value = None
        request.return_value = reply
        post = {"topic": "mini_pigeon_landlord", "scene": "wallet",
                "visual": "Photorealistic pigeon selling an apartment at a real estate office"}
        output, metadata = generate_image(post, "2026-11-13-18-00", "photomontage")
        self.assertEqual(output.size, (512, 512))
        self.assertEqual(metadata["style"], "photomontage")
        self.assertEqual(metadata["prompt_scene"], post["visual"])
        prompt = request.call_args.kwargs["json"]["prompt"]
        self.assertIn("pigeon selling an apartment", prompt)
        self.assertIn("cut-and-paste", prompt)

    def test_unknown_visual_style_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "visual genre"):
            generate_image({"scene": "life"}, "2026-11-13-18-00", "all_anime_forever")


if __name__ == "__main__":
    unittest.main()
