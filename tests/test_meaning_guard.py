import unittest

from hard_jokes import HARD_JOKES
from meaning_guard import idea_group, lexical_overlap, recent_meaning_conflict, shares_premise
from quality_guard import select_post, validate


class MeaningGuardTests(unittest.TestCase):
    def test_rewritten_salary_joke_is_a_repeat(self):
        a = next(x for x in HARD_JOKES if x["topic"] == "mini_salary_fugitive")
        old = {
            "topic": "mini_salary_escape", "scene": "wallet",
            "top": "Получил зарплату. И что?",
            "bottom": "Она сразу убежала к коммунальщикам."
        }
        self.assertTrue(shares_premise(a, old))
        self.assertTrue(recent_meaning_conflict(a, [old]))
        with self.assertRaisesRegex(ValueError, "meaning"):
            validate(a, [old])

    def test_different_abnormal_scenes_can_coexist(self):
        bird = next(x for x in HARD_JOKES if x["topic"] == "mini_pigeon_landlord")
        printer = next(x for x in HARD_JOKES if x["topic"] == "mini_printer_hell")
        self.assertNotEqual(idea_group(bird), idea_group(printer))
        self.assertFalse(shares_premise(bird, printer))

    def test_lexical_paraphrase(self):
        a = {"top": "Сосед начал сверлить в семь утра.",
             "bottom": "К девяти он пробил портал в ад."}
        b = {"top": "Наш сосед опять начал сверлить в семь утра.",
             "bottom": "К девяти сосед пробил портал в ад."}
        self.assertGreaterEqual(lexical_overlap(a, b), 0.72)
        self.assertTrue(shares_premise(a, b))

    def test_published_recent_idea_not_reissued(self):
        state = {"posts": [], "slots": []}
        for index in range(80):
            slot = f"2027-04-{1+index//96:02d}-{(index//4)%24:02d}-{index%4:02d}"
            post = select_post(state, slot)
            self.assertFalse(recent_meaning_conflict(post, state["posts"]))
            state["posts"].append(post)


if __name__ == "__main__":
    unittest.main()
