import unittest
from unittest.mock import Mock
from PIL import Image
from vision_review import review_visual


def response(verdict):
    reply = Mock()
    reply.raise_for_status.return_value = None
    reply.json.return_value = {"choices": [{
        "message": {"content": __import__("json").dumps(verdict)}
    }]}
    return reply


class VisualMatchingTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.effect_noise((512, 512), 50).convert("RGB")
        self.post = {"top": "Голубь стал риелтором.",
                     "bottom": "Теперь он продаёт квартиры.",
                     "visual": "Photorealistic pigeon in real estate office selling an apartment"}

    def test_actual_image_is_sent_to_vision_model_for_review(self):
        request = Mock(return_value=response({
            "matches": True, "confidence": 0.94,
            "reason": "Pigeon with property brochures clearly visible"}))
        result = review_visual(self.image, self.post, request=request)
        self.assertEqual(result["vision_review"], "matched")
        self.assertEqual(result["vision_model"], "Qwen3.8-27B")
        body = request.call_args.kwargs["json"]
        self.assertIn("selling an apartment",
                      body["messages"][0]["content"][0]["text"])
        self.assertTrue(
            body["messages"][0]["content"][1]["image_url"]["url"].startswith(
                "data:image/jpeg;base64,"))

    def test_confident_mismatch_blocks_publication(self):
        request = Mock(return_value=response({
            "matches": False, "confidence": 0.99,
            "reason": "Image just shows a woman smiling"}))
        with self.assertRaisesRegex(RuntimeError, "disagrees"):
            review_visual(self.image, self.post, request=request)

    def test_free_model_unavailable_is_reported_not_falsely_approved(self):
        request = Mock(side_effect=__import__("requests").Timeout("provider busy"))
        result = review_visual(self.image, self.post, request=request)
        self.assertEqual(result["vision_review"], "unavailable")
        with self.assertRaises(RuntimeError):
            review_visual(self.image, self.post, mode="strict", request=request)

    def test_opt_out_does_not_call_provider(self):
        request = Mock()
        self.assertEqual(
            review_visual(self.image, self.post, mode="off", request=request),
            {"vision_review": "disabled"})
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
