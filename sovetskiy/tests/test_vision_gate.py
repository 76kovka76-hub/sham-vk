"""No-network semantic image gate tests: block images that don't fit joke."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import auto15_queue as queue
import vision_gate
from auto_stories import STORIES


def fake_response(passed=True):
    response=Mock()
    response.status_code=200
    desc=("The picture clearly shows a distressed adult man holding a very "
          "large padded pillow while trying to move out of a bed.")
    expl=("The pillow visibly restrains the man who wants to leave the bed, "
          "which directly matches the Russian joke about not getting up.")
    result={"visual_description":desc,"central_prop_visible":passed,
            "action_matches_joke":passed,
            "large_caption_legible":True,
            "explanation":expl}
    response.json.return_value={"choices":[{"message":{"content":
        "```json\n"+json.dumps(result)+"\n```"}}]}
    return response


class FreeVisualGateTests(unittest.TestCase):
    def test_positive_and_negative_vision_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"image.png"
            file.write_bytes(b"\x89PNG\r\n\x1a\n"+b"x"*40000)
            with patch.object(vision_gate,"_rate_limit"):
                def yes(*args,**kwargs):return fake_response(True)
                def no(*args,**kwargs):return fake_response(False)
                a=vision_gate.inspect(file,"ПЫТАЛСЯ ВСТАТЬ","ПОДУШКА ДЕРЖИТ",
                                     "man struggling to rise from bed",post=yes)
                self.assertTrue(a["passed"])
                b=vision_gate.inspect(file,"ПЫТАЛСЯ ВСТАТЬ","ПОДУШКА ДЕРЖИТ",
                                     "man struggling to rise from bed",post=no)
                self.assertFalse(b["passed"])
                self.assertFalse(b["central_prop_visible"])

    def test_ambiguous_and_unstructured_model_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"image.png"
            file.write_bytes(b"y"*40000)
            def bad(*args,**kwargs):
                r=fake_response(True)
                r.json.return_value["choices"][0]["message"]["content"]="The picture looks okay"
                return r
            with patch.object(vision_gate,"_rate_limit"):
                with self.assertRaisesRegex(RuntimeError,"JSON"):
                    vision_gate.inspect(file,"СЦЕНА","ШУТКА",
                                        "photograph of a person with bread",
                                        post=bad)

    def test_prequeue_rejects_unrelated_image_twice(self):
        story=STORIES[0]
        with patch.object(queue,"config",return_value={"group_id":"243244760",
                     "posts_per_day":96,"interval_minutes":15,
                     "visual_qa_enabled":True}), \
             patch.object(queue,"choose_joke",return_value=None), \
             patch.object(queue,"choose_story",return_value=story), \
             patch.object(queue,"render_original",return_value=(
                     "fake.png",{"story_id":story.id,"group_id":"243244760",
                     "sha256":"abc","real_movie_frame":False,
                     "message":"Текст #SOVETSKIY #юмор #жиза"})), \
             patch.object(vision_gate,"inspect",return_value={
                     "passed":False,"explanation":"The visible picture has no central prop, so the joke does not match."}):
            with self.assertRaisesRegex(RuntimeError,"failed visual review"):
                queue.prepare({"entries":[]},"20261113-46")


if __name__=="__main__":
    unittest.main()
