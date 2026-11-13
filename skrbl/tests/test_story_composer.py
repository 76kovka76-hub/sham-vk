"""Offline regression tests for flexible 1–4 panel original SKRBL jokes."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from story_bank import STORIES
from story_composer import choose_story, panel_geometry, build_comic, validate_story
from queue_planner import UNMASKED_SWEARS


def fake_free_frame(prompt):
    image=Image.new("RGB",(1024,1024),(245,233,212))
    d=ImageDraw.Draw(image)
    k=int(hashlib.sha256(prompt.encode()).hexdigest()[:7],16)
    for i in range(130):
        x=(k+i*83)%1010
        y=(k//9+i*107)%1010
        d.ellipse((x,y,x+34+i%61,y+40+i%17),
                  fill=((i*17)%225,(i*57)%205,(i*37)%215),outline=(27,28,22),width=4)
    return image


class StoryTests(unittest.TestCase):
    def test_no_copied_jokes_and_no_unmasked_profanity(self):
        self.assertGreaterEqual(len(STORIES),40)
        self.assertEqual(len(set(s.id for s in STORIES)),len(STORIES))
        for story in STORIES:
            self.assertTrue(validate_story(story))
            self.assertIsNone(UNMASKED_SWEARS.search(story.caption))
            self.assertEqual(story.caption.count("#"),3)
            self.assertTrue(all(len(p.visual)>60 for p in story.scenes))

    def test_layout_counts_and_no_panel_overlap(self):
        for n in range(1,5):
            regions=panel_geometry(n)
            self.assertEqual(len(regions),n)
            for x,y,w,h in regions:
                self.assertGreaterEqual(x,0)
                self.assertGreaterEqual(y,0)
                self.assertLessEqual(x+w,1536)
                self.assertLessEqual(y+h,1536)
                self.assertGreater(w,450)
                self.assertGreater(h,450)
            for i,a in enumerate(regions):
                for b in regions[i+1:]:
                    # Interior rectangles must never overlap
                    self.assertTrue(
                        a[0]+a[2]<=b[0] or b[0]+b[2]<=a[0] or
                        a[1]+a[3]<=b[1] or b[1]+b[3]<=a[1]
                    )

    def test_avoids_repeating_story_id(self):
        ledger={"entries":[{"story_id":s.id,"topic":s.topic} for s in STORIES[:-1]]}
        story=choose_story(ledger,"20261113-12")
        self.assertEqual(story.id,STORIES[-1].id)
        ledger["entries"].append({"story_id":STORIES[-1].id})
        with self.assertRaisesRegex(RuntimeError,"depleted"):
            choose_story(ledger,"20261113-13")

    def test_render_one_two_three_four_offline(self):
        for n in range(1,5):
            story=next(s for s in STORIES if len(s.scenes)==n)
            with tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp)/"pic.png"
                meta=Path(tmp)/"meta.json"
                path,result=build_comic(story,image_generator=fake_free_frame,
                                        output=output,metadata_path=meta)
                self.assertTrue(path.exists())
                self.assertEqual(result["panels"],n)
                with Image.open(output) as im:
                    self.assertEqual(im.size,(1536,1536))
                self.assertEqual(json.loads(meta.read_text())["story_id"],story.id)


if __name__=="__main__":
    unittest.main()
