import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from vedismm_publisher import publish_vedismm


def response(status, data):
    fake = Mock()
    fake.status_code = status
    fake.json.return_value = {"data": data}
    fake.raise_for_status.return_value = None
    return fake


class VediSmmTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_missing_credentials_do_not_publish(self):
        with self.assertRaisesRegex(RuntimeError, "VEDISMM_TOKEN"):
            publish_vedismm(Path("/not-a-file.png"), "Пример", "slot")
    
    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token",
                               "VEDISMM_ACCOUNT_ID": "45"}, clear=True)
    @patch("vedismm_publisher.time.sleep")
    @patch("vedismm_publisher.requests.get")
    @patch("vedismm_publisher.requests.post")
    def test_image_uploaded_and_vk_target_confirmed(self, post, get, sleep):
        post.side_effect = [
            response(201, {"id": 12, "type": "image", "status": "ready"}),
            response(201, {"id": 79, "version": 1, "status": "draft",
                           "media": [{"id": 12}]}),
            response(202, {"id": "job-test-1", "status": "queued"}),
        ]
        get.return_value = response(200, {"status": "succeeded", "targets": [
            {"account": {"id": 45}, "status": "succeeded",
             "external_url": "https://vk.com/wall-243230846_10"}
        ]})
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "meme.png"
            file.write_bytes(b"not-an-image-requests-are-mocked")
            result = publish_vedismm(file, "Мем #мемы #юмор #жиза", "2026-11-12-09-00")
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["url"], "https://vk.com/wall-243230846_10")
        self.assertEqual(post.call_count, 3)
        self.assertIn("media_ids", post.call_args_list[1].kwargs["json"])
        self.assertEqual(post.call_args_list[1].kwargs["json"]["media_ids"], [12])
        self.assertEqual(post.call_args_list[2].kwargs["json"], {"version": 1})
        self.assertEqual(get.call_count, 1)

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test-token",
                               "VEDISMM_ACCOUNT_ID": "45"}, clear=True)
    @patch("vedismm_publisher.requests.post")
    def test_reject_nonimage_upload_without_posting(self, post):
        post.return_value = response(201, {"id": 12, "type": "video", "status": "ready"})
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "meme.png"
            file.write_bytes(b"sample")
            with self.assertRaisesRegex(RuntimeError, "ready image"):
                publish_vedismm(file, "Мем", "slot")
        self.assertEqual(post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
