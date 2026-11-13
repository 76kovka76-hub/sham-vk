"""No image + joke pairing is allowed to VK without specific scene review."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jokes import JOKES
from scene_quality import load_matches,review_info,is_approved
import publisher


class SceneQualityTests(unittest.TestCase):
    def test_every_unreviewed_pair_is_blocked(self):
        matches=load_matches()
        self.assertEqual(set(matches),{j.key for j in JOKES})
        self.assertTrue(all(not is_approved(j,matches) for j in JOKES))
        self.assertTrue(all(matches[j.key]["source_ids"]==list(j.source_ids)
                            for j in JOKES))
        with self.assertRaisesRegex(ValueError,"not passed"):
            review_info(JOKES[0])

    def test_selector_never_schedules_unreviewed_or_random_reactions(self):
        self.assertIsNone(publisher.choose_joke({"entries":[]},
                                                  require_scene_approval=True))
        self.assertIsNotNone(publisher.choose_joke({"entries":[]},
                                                  require_scene_approval=False))

    def test_approved_requires_exact_sources_and_observed_emotion(self):
        original=JOKES[0]
        row=copy.deepcopy(load_matches()[original.key])
        row["status"]="approved"
        row["reviewer"]="editorial-visual-check"
        row["observed_per_frame"]=[
            "На конкретном оригинальном кадре персонаж широко раскрыл глаза и выглядит поражённым."
        ]
        row["reviewed_source_urls"]=[
            "https://commons.wikimedia.org/wiki/File:Aelita_screenshot.jpg"
        ]
        row["review_note"]="Выражение удивления усиливает шутку о неожиданно высокой цене в магазине."
        mapping={original.key:row}
        self.assertTrue(is_approved(original,mapping))
        self.assertEqual(review_info(original,mapping)["reviewer"],row["reviewer"])
        mapping[original.key]["source_ids"]=["potemkin_ship"]
        self.assertFalse(is_approved(original,mapping))

    def test_collage_frame_order_is_semantic(self):
        joke=next(j for j in JOKES if j.format=="collage")
        row=copy.deepcopy(load_matches()[joke.key])
        row["status"]="approved"
        row["reviewer"]="visual-editor"
        row["observed_per_frame"]=[
            "В первом кадре герой расслаблен и смотрит уверенно на собеседника.",
            "Во втором кадре персонаж широко раскрыл глаза и явно потрясён.",
        ]
        row["reviewed_source_urls"]=[
            "https://commons.wikimedia.org/wiki/File:Nikolai_Batalov_dans_Aelita.JPG",
            "https://commons.wikimedia.org/wiki/File:Aelita_screenshot.jpg",
        ]
        row["review_note"]="Кадры в таком порядке показывают переход от радости до шока при оплате счетов."
        mapping={joke.key:row}
        self.assertTrue(is_approved(joke,mapping))
        row["source_ids"]=list(reversed(joke.source_ids))
        self.assertFalse(is_approved(joke,mapping))

    def test_false_or_incomplete_review_cannot_enable_post(self):
        joke=JOKES[1]
        row=copy.deepcopy(load_matches()[joke.key])
        row["status"]="approved"
        row["reviewer"]="editor"
        row["review_note"]="Персонаж выглядит задумчивым после просмотра банковского баланса."
        self.assertFalse(is_approved(joke,{joke.key:row}))
        row["observed_per_frame"]=["Общий портрет без ясно различимого предмета."]
        self.assertFalse(is_approved(joke,{joke.key:row}))


if __name__=="__main__":
    unittest.main()
