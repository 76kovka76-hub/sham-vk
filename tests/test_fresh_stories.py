import unittest

from fresh_jokes import FRESH_JOKES
from quality_guard import approved, validate


class FreshStoryTests(unittest.TestCase):
    def test_original_jokes_are_approved_and_individually_visualized(self):
        self.assertEqual(len(FRESH_JOKES), 24)
        self.assertEqual(len({p["topic"] for p in FRESH_JOKES}), 24)
        for item in FRESH_JOKES:
            self.assertTrue(approved(item))
            self.assertTrue(validate(item))
            self.assertGreaterEqual(len(item["visual"].split()), 6)

    def test_wrong_joke_to_picture_pair_is_blocked(self):
        a = dict(FRESH_JOKES[0])
        a["visual"] = FRESH_JOKES[1]["visual"]
        self.assertFalse(approved(a))
        with self.assertRaisesRegex(ValueError, "unapproved"):
            validate(a)


if __name__ == "__main__":
    unittest.main()
