import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from queue_planner import next_missing_slot, slot_name
from horde_style import style_for_slot
from vedismm_publisher import schedule_vedismm


def response(code, data, etag=None):
    r = Mock()
    r.status_code = code
    r.json.return_value = {"data": data}
    r.raise_for_status.return_value = None
    r.headers = {"ETag": etag} if etag else {}
    return r


class QueueTests(unittest.TestCase):
    def test_queue_initial_slot_30min_ahead(self):
        now = datetime(2026, 11, 13, 12, 2, tzinfo=timezone.utc)
        slot, when = next_missing_slot({"slots": []}, now)
        self.assertEqual(slot, "2026-11-13-12-03")
        self.assertEqual(when, datetime(2026, 11, 13, 12, 45,
                                        tzinfo=timezone.utc))

    def test_queue_refills_first_hole_and_no_duplicates(self):
        now = datetime(2026, 11, 13, 12, 2, tzinfo=timezone.utc)
        slot, when = next_missing_slot({"slots": []}, now)
        newer, later = next_missing_slot({"slots": [slot]}, now)
        self.assertEqual((newer, later),
                         ("2026-11-13-13-00",
                          datetime(2026, 11, 13, 13, 0, tzinfo=timezone.utc)))
        # Gaps behind a reserved slot are filled first.
        hole, _ = next_missing_slot({"slots": [newer]}, now)
        self.assertEqual(hole, slot)

    def test_queue_is_full_for_12h(self):
        now = datetime(2026, 11, 13, 12, 2, tzinfo=timezone.utc)
        beginning = datetime(2026, 11, 13, 12, 45, tzinfo=timezone.utc)
        slots = [slot_name(beginning + timedelta(minutes=15*i))
                 for i in range(46)]
        self.assertEqual(next_missing_slot({"slots": slots}, now),
                         (None, None))

    def test_queue_rolls_across_midnight_and_styles(self):
        now = datetime(2026, 11, 13, 23, 32, tzinfo=timezone.utc)
        slot, when = next_missing_slot({"slots": []}, now)
        self.assertEqual(slot, "2026-11-14-00-01")
        first_style = style_for_slot("2026-11-14-00-00")
        second_style = style_for_slot(slot)
        self.assertNotEqual(first_style, second_style)
        self.assertEqual(style_for_slot(slot), second_style)

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"}, clear=True)
    @patch("vedismm_publisher._find_account_id", return_value=45)
    @patch("vedismm_publisher.requests.post")
    def test_creates_image_attached_scheduled_post_using_etag(self, post, account):
        post.side_effect = [
            response(201, {"id": 5, "type": "image", "status": "ready"}),
            response(201, {"id": 40, "version": 1, "status": "draft",
                           "media": [{"id": 5}]}, etag='"post-40-v1"'),
            response(200, {"id": 40, "status": "scheduled",
                           "scheduled_at": "2027-01-01T15:00:00Z"}),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "meme.png"
            path.write_bytes(b"test")
            when = datetime(2027, 1, 1, 15, tzinfo=timezone.utc)
            result = schedule_vedismm(path, "Мем #1 #2 #3",
                                      "2027-01-01-15-00", when)
        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(post.call_count, 3)
        self.assertEqual(post.call_args_list[1].kwargs["json"]["media_ids"], [5])
        self.assertEqual(post.call_args_list[2].kwargs["headers"]["If-Match"],
                         '"post-40-v1"')
        self.assertEqual(post.call_args_list[2].kwargs["json"],
                         {"scheduled_at": "2027-01-01T15:00:00Z"})

    @patch.dict("os.environ", {"VEDISMM_TOKEN": "test"}, clear=True)
    @patch("vedismm_publisher._find_account_id", return_value=45)
    @patch("vedismm_publisher.requests.post")
    def test_no_schedule_if_draft_missing_image(self, post, account):
        post.side_effect = [
            response(201, {"id": 5, "type": "image", "status": "ready"}),
            response(201, {"id": 40, "status": "draft", "media": []},
                     etag='"post-40-v1"'),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "meme.png"
            path.write_bytes(b"test")
            with self.assertRaisesRegex(RuntimeError, "no image"):
                schedule_vedismm(path, "text", "2027-01-01-15-00",
                                 datetime(2027, 1, 1, 15,
                                          tzinfo=timezone.utc))
        self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
