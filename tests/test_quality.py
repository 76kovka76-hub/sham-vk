import unittest

from main import generate_post, identity
from quality_bank import TOPICS
from quality_guard import approved, norm, select_post, similar, validate


class EditorialQualityTests(unittest.TestCase):
    def test_all_600_preapproved_combinations_have_valid_format(self):
        self.assertEqual(len(TOPICS), 30)
        for topic in TOPICS:
            for setup in topic["setups"]:
                for end in topic["punchlines"]:
                    post = {"scene": topic["scene"], "topic": topic["topic"],
                            "visual": topic["visual"], "top": setup,
                            "bottom": end, "caption": topic["captions"][0]}
                    self.assertTrue(approved(post))
                    self.assertTrue(validate(post))

    def test_illogical_furniture_food_post_is_rejected(self):
        bad = {"scene": "home", "topic": "fridge",
               "top": "Решил переставить мебель.",
               "bottom": "Еда так и не заспавнилась. Жду обновление.",
               "caption": "Кто тоже король бытового хаоса?",
               "visual": "hungry adult opening an almost empty refrigerator"}
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            validate(bad)

    def test_no_recent_openers_or_exact_jokes(self):
        state = {"posts": [
            {"scene": "home", "top": "Решил переставить мебель.",
             "bottom": "Еда так и не заспавнилась. Жду обновление.",
             "caption": "Кто тоже король бытового хаоса?",
             "id": "bad-old-hash", "topic": "legacy"}
        ], "slots": []}
        used = set()
        for n in range(180):
            post = generate_post(state, f"2027-03-{(n//96)+1:02d}-{(n//4)%24:02d}-{n%4:02d}")
            self.assertNotIn(identity(post), used)
            self.assertTrue(approved(post))
            self.assertNotEqual(norm(post["top"]), norm(state["posts"][0]["top"]))
            self.assertFalse(any(similar(post["top"], prev.get("top", ""), 0.94)
                                 for prev in state["posts"][-90:]))
            self.assertNotIn(post["topic"], {p.get("topic") for p in state["posts"][-10:]})
            self.assertNotIn(post["scene"], {p.get("scene") for p in state["posts"][-2:]})
            used.add(identity(post))
            state["posts"].append({**post, "id": identity(post)})

    def test_visual_matches_joke_topic(self):
        post = select_post({"posts": [], "slots": []}, "2027-01-01-00-00")
        self.assertTrue(post["visual"])
        self.assertTrue(post["topic"])
        self.assertTrue(validate(post))


if __name__ == "__main__":
    unittest.main()
