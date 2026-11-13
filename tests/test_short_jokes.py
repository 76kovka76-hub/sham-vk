import unittest
from quality_bank import TOPICS
from quality_guard import approved,validate,select_post,joke_id
from short_jokes import SHORT_JOKES
from visual_gags import VISUAL_GAGS,get_visual_gag


class ShortJokesTests(unittest.TestCase):
    def test_every_mini_joke_has_its_own_visual_and_is_approved(self):
        self.assertGreaterEqual(len(SHORT_JOKES),15)
        self.assertEqual(len({p["topic"] for p in SHORT_JOKES}),len(SHORT_JOKES))
        self.assertEqual(len(VISUAL_GAGS),len(TOPICS))
        for post in SHORT_JOKES:
            self.assertTrue(approved(post))
            self.assertTrue(validate(post))
            self.assertGreater(len(get_visual_gag(post)),45)
            self.assertTrue(post["visual"])
            self.assertNotIn("http",post["visual"])

    def test_no_random_unapproved_internet_jokes_are_posted(self):
        bad=dict(SHORT_JOKES[0])
        bad["bottom"]="Копия случайного анекдота с неизвестного сайта."
        self.assertFalse(approved(bad))
        with self.assertRaisesRegex(ValueError,"Incompatible"):
            validate(bad)

    def test_all_slot_choices_are_approved_and_recency_safe(self):
        history={"posts":[]}
        seen=set()
        mini_count=0
        for index in range(140):
            slot=f"2026-11-13-{index//4:02d}-{index%4:02d}"
            post=select_post(history,slot)
            self.assertTrue(approved(post))
            self.assertNotIn(joke_id(post),seen)
            if post["topic"].startswith("mini_"):
                mini_count+=1
            seen.add(joke_id(post))
            history["posts"].append({**post,"id":joke_id(post)})
        self.assertGreater(mini_count,0)
        self.assertLess(mini_count,90)


if __name__=="__main__":
    unittest.main()
