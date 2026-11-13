"""No-network tests for 96-slot Soviet-photograph meme automation."""
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import auto15_queue as q
from auto_image import render as render_original
from auto_stories import STORIES,choose_story
from quarter_hour import day_slots, next_slot, upcoming_slots


class SOVETSKY15MinuteTests(unittest.TestCase):
    def test_exactly_96_unique_quarter_hour_slots_every_utc_day(self):
        for day in (date(2026,11,13),date(2027,3,28),date(2027,10,31)):
            slots=day_slots(day)
            self.assertEqual(len(slots),96)
            self.assertEqual(len({s for s,t in slots}),96)
            self.assertEqual(slots[0][1].hour,0)
            self.assertEqual(slots[-1][1].hour,23)
            self.assertEqual(slots[-1][1].minute,45)
            self.assertTrue(all((b[1]-a[1])==timedelta(minutes=15)
                                for a,b in zip(slots,slots[1:])))

    def test_14_hour_rolling_buffer_without_duplicate_slots(self):
        now=datetime(2026,11,13,22,50,tzinfo=timezone.utc)
        state={"entries":[]}
        first=next_slot(state,now)
        self.assertEqual(first[0],"20261113-95" if False else "20261113-95")
        # 22:50 + 45m = 23:35; next aligned slot is 23:45.
        self.assertEqual(first[1],datetime(2026,11,13,23,45,tzinfo=timezone.utc))
        self.assertEqual(first[0],"20261113-95")
        state["entries"].append({"slot":first[0],"status":"scheduled"})
        second=next_slot(state,now)
        self.assertEqual(second[1],datetime(2026,11,14,0,0,tzinfo=timezone.utc))
        slots=upcoming_slots(state,now)
        self.assertNotIn(first,slots)

    def test_96_original_short_jokes_and_balanced_themes(self):
        self.assertEqual(len(STORIES),96)
        self.assertEqual(len({x.id for x in STORIES}),96)
        self.assertEqual({s.theme for s in STORIES},
                         {"money","work","home","sleep","social","shopping","phone","life"})
        for story in STORIES:
            self.assertGreater(len(story.visual),65)
            self.assertLessEqual(len(story.bottom),97)
            self.assertNotIn("http",story.visual)
        state={"entries":[]}
        seen=set()
        for i in range(96):
            selected=choose_story(state,f"20261113-{i:02d}")
            self.assertIsNotNone(selected)
            self.assertNotIn(selected.id,seen)
            state["entries"].append({"story_id":selected.id,"theme":selected.theme})
            seen.add(selected.id)
        self.assertIsNone(choose_story(state,"20261114-00"))

    def test_photo_caption_uses_matching_story_and_correct_hashtags(self):
        photo=Image.new("RGB",(1024,1024),(200,180,160))
        dr=ImageDraw.Draw(photo)
        for i in range(70):
            dr.ellipse((20+i*9,40+i*8,100+i*9,100+i*8),
                       fill=((i*7)%255,(i*11)%255,(i*17)%255))
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"photo.png"
            meta=Path(d)/"meta.json"
            _,info=render_original(STORIES[0],"20261113-05",photo=photo,
                                   output=output,metadata_path=meta)
            self.assertEqual(info["story_id"],STORIES[0].id)
            self.assertIn(STORIES[0].top.rstrip("."),info["message"])
            self.assertEqual(info["message"].count("#"),3)
            self.assertFalse(info["real_movie_frame"])
            with Image.open(output) as img:
                self.assertEqual(img.size,(1200,1200))
            self.assertEqual(json.loads(meta.read_text())["sha256"],info["sha256"])

    def test_no_automated_reuse_or_cross_group_fallback(self):
        state={"group_id":"243244760","entries":[]}
        now=datetime(2026,11,13,10,4,tzinfo=timezone.utc)
        s,t=next_slot(state,now)
        state["entries"].append({"slot":s,"status":"needs_attention",
                                 "story_id":STORIES[0].id})
        s2,t2=next_slot(state,now)
        self.assertNotEqual(s,s2)
        self.assertNotEqual(choose_story(state,s2).id,STORIES[0].id)
        with tempfile.TemporaryDirectory() as d:
            with patch.object(q,"STATE",Path(d)/"state.json"):
                with self.assertRaisesRegex(RuntimeError,"different group's"):
                    q.save({"group_id":"243230846","entries":[]})

    def test_batch_can_fill_six_slots_after_one_cron_wakeup(self):
        now=datetime(2026,11,13,10,4,tzinfo=timezone.utc)
        state={"group_id":"243244760","entries":[]}
        def fake_one(obj,slot,at,token):
            self.assertNotIn(slot,[x["slot"] for x in obj["entries"]])
            obj["entries"].append({"slot":slot,"status":"scheduled",
                                   "group_id":"243244760",
                                   "story_id":"test_"+slot})
        with patch.object(q,"load_state",return_value=state), \
             patch.object(q,"config",return_value={
                 "group_id":"243244760","posts_per_day":96,
                 "interval_minutes":15,"autopublish":True}), \
             patch.object(q,"enqueue_one",side_effect=fake_one), \
             patch.dict("os.environ",{"VEDISMM_TOKEN":"unit-test-not-real"}):
            result=q.refill(maximum=6,max_seconds=1380,now=now)
        self.assertEqual(result["scheduled"],6)
        self.assertEqual(len({x["slot"] for x in state["entries"]}),6)


if __name__=="__main__":
    unittest.main()
