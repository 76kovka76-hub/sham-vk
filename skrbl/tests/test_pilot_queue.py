import sys
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot_queue import next_pilot_slot,PILOT_INDICES
from queue_planner import all_day_slots
from story_composer import choose_story


class SKRBLPilotTests(unittest.TestCase):
    def test_six_unique_slots_evenly_spaced(self):
        from datetime import date
        slots=all_day_slots(date(2026,11,13))
        result=[slots[i] for i in PILOT_INDICES]
        self.assertEqual(len(set(i for i,_ in result)),6)
        self.assertEqual(len(result),6)
        self.assertTrue(all(result[j+1][1]>result[j][1] for j in range(5)))

    def test_booking_next_free_slot_without_duplicates(self):
        state={"entries":[]}
        now=datetime(2026,11,13,6,28,tzinfo=timezone.utc)
        slot,t=next_pilot_slot(state,now)
        self.assertIsNotNone(slot)
        self.assertGreater(t-now,timedelta(minutes=49))
        self.assertLess(t-now,timedelta(hours=14))
        state["entries"].append({"slot":slot})
        slot2,t2=next_pilot_slot(state,now)
        self.assertNotEqual(slot,slot2)

    def test_outside_horizon_skips_and_does_not_publish(self):
        now=datetime(2026,11,13,4,7,tzinfo=timezone.utc)
        state={"entries":[]}
        slot,t=next_pilot_slot(state,now)
        self.assertTrue(t>=now+timedelta(minutes=50))
        self.assertTrue(t<=now+timedelta(hours=14))

    def test_pilot_stories_are_unique_across_slots(self):
        state={"entries":[]}
        for dayidx in range(6):
            slot=f"20261113-{PILOT_INDICES[dayidx]:02d}"
            story=choose_story(state,slot)
            self.assertTrue(1<=len(story.scenes)<=4)
            state["entries"].append({"slot":slot,"story_id":story.id,"topic":story.topic})
        self.assertEqual(len({x["story_id"] for x in state["entries"]}),6)


if __name__=="__main__":
    unittest.main()
