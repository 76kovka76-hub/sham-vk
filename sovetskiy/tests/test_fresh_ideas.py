"""Offline safeguards for free LLM humor replenishment, no VK writes."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import fresh_ideas as f
import auto15_queue as q
from auto_stories import Story


NEW={
    "top":"ПОВАР ОТКРЫЛ КАФЕ ПРЯМО НА БАЛКОНЕ.",
    "bottom":"СОСЕДИ ПРИШЛИ С ТАЗАМИ ЗА БОРЩОМ.",
    "visual":("A Soviet apartment balcony with a chaotic middle-aged chef "
              "stirring an enormous soup pot while a line of laughing neighbors "
              "passes buckets through the open balcony door."),
    "theme":"home",
}


class FreshHumorTests(unittest.TestCase):
    def test_parse_markdown_json_and_reject_truncated_content(self):
        body="```json\n"+json.dumps([NEW],ensure_ascii=False)+"\n```"
        self.assertEqual(f._json_content(body)[0]["theme"],"home")
        with self.assertRaises(ValueError):
            f._json_content("Nothing generated")

    def test_original_story_can_pass_with_a_real_visual_prop(self):
        self.assertTrue(f._valid(NEW,f._past_texts({"entries":[]})))
        bad=dict(NEW)
        bad["visual"]="ordinary portrait"
        self.assertFalse(f._valid(bad,[]))

    def test_separate_critical_review_must_score_8_and_validate_originality(self):
        candidates=[NEW]+[{**NEW,
             "top":"СОСЕДИ НАЗНАЧИЛИ КОШКУ ДИРЕКТОРОМ ЭТАЖА "+str(i),
             "bottom":"КОШКА УЖЕ ТРЕБУЕТ ПРИЁМНЫЕ ЧАСЫ "+str(i),
             "theme":"social"} for i in range(3)]
        scored={"index":0,"joke_score":9,"visual_match_score":9,
                "reason":"На балконе настоящий котёл с борщом, а соседи держат тазы и ждут угощения."}
        calls=[json.dumps(candidates,ensure_ascii=False),json.dumps(scored,ensure_ascii=False)]
        def mock_chat(messages,limit=1500):
            return calls.pop(0)
        obj=f.generate({"entries":[]},"20261114-00",chat=mock_chat)
        self.assertEqual(obj.theme,"home")
        self.assertEqual(obj.visual,NEW["visual"])
        poor={"index":0,"joke_score":3,"visual_match_score":9,
              "reason":"Картинка и текст выглядят не вполне смешно, слишком банально."}
        calls=[json.dumps(candidates,ensure_ascii=False),json.dumps(poor)]
        with self.assertRaisesRegex(RuntimeError,"editorial scoring"):
            f.generate({"entries":[]},"20261114-01",chat=mock_chat)

    def test_auto_queue_uses_free_original_joke_only_after_bank_exhausted(self):
        state={"entries":[]}
        new_story=Story("fresh_original_abc",NEW["top"],NEW["bottom"],NEW["visual"],NEW["theme"])
        with patch.object(q,"choose_joke",return_value=None), \
             patch.object(q,"choose_story",return_value=None), \
             patch.object(q,"config",return_value={
                 "group_id":"243244760","posts_per_day":96,
                 "interval_minutes":15,"fresh_ideas_enabled":True,
                 "visual_qa_enabled":False}), \
             patch.object(f,"generate",return_value=new_story), \
             patch.object(q,"render_original",return_value=(
                 "fake.png",{"story_id":new_story.id,"group_id":"243244760",
                 "sha256":"new123","real_movie_frame":False,
                 "message":"Уникальная шутка #SOVETSKIY #юмор #жиза"})):
            art,record=q.prepare(state,"20261114-00")
            self.assertEqual(record["story_id"],new_story.id)
            self.assertEqual(record["top"],new_story.top)
            self.assertIsNone(record["visual_qa"])


if __name__=="__main__":
    unittest.main()
