"""Regression tests for 50 SKRBL pencil comics/day (no publication)."""
import importlib.util
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import tempfile
import hashlib
import json

MODULE = Path(__file__).resolve().parents[1] / "queue_planner.py"
spec = importlib.util.spec_from_file_location("skrbl_queue_planner", MODULE)
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class SKRBLQueueTests(unittest.TestCase):
    def test_exactly_50_slots_per_utc_day(self):
        for day in [date(2026, 11, 13), date(2027, 1, 1)]:
            slots = q.all_day_slots(day)
            self.assertEqual(len(slots), 50)
            self.assertEqual(len(set(k for k, _ in slots)), 50)
            self.assertEqual(len(set(t for _, t in slots)), 50)
            self.assertTrue(all(t.date() == day for _, t in slots))
            spacing = {(b-a).total_seconds() // 60 for (_, a), (_, b)
                       in zip(slots, slots[1:])}
            self.assertEqual(spacing, {28, 29})

    def test_safe_lead_and_cross_midnight(self):
        now = datetime(2026, 11, 13, 23, 40, tzinfo=timezone.utc)
        slot, at = q.next_slot({"entries": []}, now)
        self.assertTrue(slot.startswith("20261114-"))
        self.assertGreaterEqual(at-now, timedelta(minutes=60))
        self.assertLessEqual(at-now, timedelta(hours=12))

    def test_skips_already_scheduled_slot(self):
        now = datetime(2026, 11, 13, 2, 0, tzinfo=timezone.utc)
        a, _ = q.next_slot({"entries": []}, now)
        b, _ = q.next_slot({"entries": [{"slot": a}]}, now)
        self.assertNotEqual(a, b)

    def test_no_approved_artwork_means_no_post(self):
        self.assertEqual(q.select_approved([], {"entries": []}), (None, None))
        with patch.object(q, "MANIFEST_PATH", Path("/impossible")):
            self.assertFalse(q._is_approved({
                "id":"fake","file":"fake.png","sha256":"1"*64,
                "caption":"Кринж #SKRBL #юмор #набросок", "approved":False, "panels":4
            }))

    def test_rejects_unmasked_profanity_and_one_panel(self):
        common = {"id":"meme_001","file":"meme_001.png","sha256":"a"*64,
                  "approved":True,"panels":4,
                  "caption":"Опять бл***ь кому-то должен! #SKRBL #юмор #скетч"}
        self.assertTrue(q._is_approved(common))
        self.assertFalse(q._is_approved({**common,"panels":1}))
        self.assertFalse(q._is_approved({**common,"caption":"Это пиздец! #SKRBL #юмор #скетч"}))
        self.assertFalse(q._is_approved({**common,"caption":"Два хэштега #SKRBL #юмор"}))

    def test_approved_media_requires_exact_sha256_and_unused_file(self):
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "meme_001.png"
            im = Image.new("RGB", (1100, 1100), "white")
            d=ImageDraw.Draw(im)
            for i in range(0, 1100, 13):
                d.line((i,0,1100-i,1100),fill=(i % 256, (i*7)%256, (i*11)%256),width=6)
            im.save(p)
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            manifest=[{"id":"meme_001","file":"meme_001.png","sha256":digest,
                       "approved":True,"panels":4,
                       "caption":"Это бл***ь именно скетч! #SKRBL #юмор #рисунки"}]
            with patch.object(q, "ASSETS", Path(tmp)):
                post, selected=q.select_approved(manifest, {"entries":[]})
                self.assertEqual(post["id"], "meme_001")
                self.assertEqual(selected, p)
                self.assertEqual(q.select_approved(manifest,
                    {"entries":[{"asset_id":"meme_001","sha256":digest}]}), (None,None))
                self.assertEqual(q.select_approved([{**manifest[0], "sha256":"0"*64}],
                    {"entries":[]}), (None,None))


if __name__ == "__main__":
    unittest.main()
