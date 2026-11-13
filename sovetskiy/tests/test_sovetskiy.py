"""Safe SOVETSKIY tests: rights, VK account isolation, captions and no repeats.

All offline; no VediSMM posts and no remote frames during unit tests.
"""
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import commons
import publisher as squeue
from check_account import find_account
from jokes import JOKES
from render import render


def dummy_frame(source_id):
    im=Image.new("RGB",(810,700),color=(170,161,140))
    d=ImageDraw.Draw(im)
    for n in range(30):
        d.ellipse(((n*43)%770,(n*37)%660,(n*43)%770+30,(n*37)%660+30),
                  outline=(30,35,29),width=6)
    return im,{"id":source_id,"movie":"Аэлита (1924)","source":"https://commons.wikimedia.org/wiki/File:Aelita_screenshot.jpg"}


class SOVETSKIYTests(unittest.TestCase):
    def test_target_account_is_exact_and_active(self):
        s=Mock()
        s.get.return_value.json.return_value={"data":[
            {"id":201,"network":"vk","external_id":"-243230846","status":"active"},
            {"id":202,"network":"vk","external_id":"-243241856","status":"active"},
            {"id":5472,"network":"vk","external_id":"-243244760","status":"active"}]}
        self.assertEqual(find_account("dummy",s),5472)
        s.get.return_value.json.return_value["data"][-1]["status"]="paused"
        with self.assertRaisesRegex(RuntimeError,"not active"):
            find_account("dummy",s)
        s.get.return_value.json.return_value["data"].pop()
        with self.assertRaisesRegex(RuntimeError,"NOT linked"):
            find_account("dummy",s)

    def test_license_catalog_has_provenance(self):
        entries=commons.catalog()
        self.assertGreaterEqual(len(entries),5)
        self.assertEqual(len(set(x["id"] for x in entries)),len(entries))
        self.assertTrue(all(x["rights"]=="public_domain" for x in entries))
        self.assertTrue(all(x["rights_proof"].startswith("https://commons.wikimedia.org/wiki/File:") for x in entries))

    def test_commons_rejects_unknown_licenses(self):
        self.assertFalse(commons._is_pd({"LicenseShortName":{"value":"copyrighted"}}))
        self.assertFalse(commons._is_pd({}))
        self.assertTrue(commons._is_pd({"LicenseShortName":{"value":"Public domain"}}))

    def test_unsupported_images_not_scraped(self):
        with self.assertRaisesRegex(RuntimeError,"Unknown"):
            commons.download("soviet_films_are_not_automatically_public_domain")

    def test_all_jokes_short_and_source_checked(self):
        ids={x["id"] for x in commons.catalog()}
        self.assertEqual(len({x.key for x in JOKES}),len(JOKES))
        for j in JOKES:
            self.assertLess(len(j.bottom),120)
            self.assertTrue(set(j.source_ids)<=ids)
            self.assertIn(j.format,("single","collage"))
            self.assertEqual(len(j.source_ids),1 if j.format=="single" else 2)

    def test_four_slots_per_day_and_no_duplicates(self):
        now=datetime(2026,11,13,9,40,tzinfo=timezone.utc)
        state={"group_id":"243244760","entries":[]}
        one,t=squeue.next_slot(state,now)
        self.assertEqual(one,"20261113-12")
        self.assertEqual(t.hour,12)
        state["entries"].append({"slot":one})
        two,two_time=squeue.next_slot(state,now)
        self.assertNotEqual(one,two)
        self.assertEqual(two_time.hour,18)

    def test_no_duplicate_film_frame(self):
        state={"entries":[]}
        first=squeue.choose_joke(state)
        self.assertIsNotNone(first)
        state["entries"].append({"joke_id":first.key,"frame_ids":list(first.source_ids),"theme":first.theme})
        next_one=squeue.choose_joke(state)
        self.assertIsNotNone(next_one)
        self.assertTrue(set(first.source_ids).isdisjoint(next_one.source_ids))

    def test_single_and_collage_render_offline(self):
        for fmt in ("single","collage"):
            joke=next(x for x in JOKES if x.format==fmt)
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/"preview.png"
                meta=Path(td)/"preview.json"
                out,details=render(joke,downloader=dummy_frame,output=path,metadata_path=meta)
                self.assertTrue(out.exists())
                self.assertEqual(details["format"],fmt)
                self.assertEqual(details["message"].count("#"),3)
                with Image.open(path) as im:
                    self.assertEqual(im.size,(1200,1200))
                self.assertEqual(json.loads(meta.read_text())["joke_id"],joke.key)


if __name__=="__main__":
    unittest.main()
