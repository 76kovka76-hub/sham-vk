import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import queue_batch


NOW = datetime(2026, 11, 13, 9, 4, tzinfo=timezone.utc)


class RefillBatchTests(unittest.TestCase):
    def test_fills_multiple_distinct_future_slots(self):
        state={"posts":[],"slots":[]}
        def once():
            slot,_=queue_batch.next_missing_slot(state,NOW)
            state["slots"].append(slot)
            return 0
        with patch.object(queue_batch,"get_state",return_value=state):
            result=queue_batch.fill_batch(
                max_posts=6,run_one=once,now=lambda:NOW,
                monotonic=lambda:100)
        self.assertEqual(result["scheduled"],6)
        self.assertEqual(len(set(state["slots"])),6)
        self.assertEqual(state["slots"][:2],["2026-11-13-09-03","2026-11-13-10-00"])

    def test_generation_failure_keeps_prior_scheduled_posts(self):
        state={"posts":[],"slots":[]}
        calls=[0]
        def once():
            calls[0]+=1
            if calls[0]>2:
                return 1
            slot,_=queue_batch.next_missing_slot(state,NOW)
            state["slots"].append(slot)
            return 0
        with patch.object(queue_batch,"get_state",return_value=state):
            result=queue_batch.fill_batch(
                max_posts=6,run_one=once,now=lambda:NOW,
                monotonic=lambda:100)
        self.assertEqual(result["scheduled"],2)
        self.assertEqual(result["stopped"],"generation_or_vksmm_failure")
        self.assertEqual(len(state["slots"]),2)

    def test_stops_safely_when_all_window_slots_booked(self):
        state={"posts":[],"slots":[]}
        start=datetime(2026,11,13,9,45,tzinfo=timezone.utc)
        from datetime import timedelta
        state["slots"]=[queue_batch.next_missing_slot(
            {"slots":state["slots"]},NOW)[0]
            for _ in []]
        state["slots"]=[
            queue_batch.slot_name(start+timedelta(minutes=15*i))
            if hasattr(queue_batch, "slot_name") else ""
            for i in range(46)]
        # fallback: only use the implementation's exposed planner
        state["slots"]=[]
        while True:
            slot,_=queue_batch.next_missing_slot(state,NOW)
            if slot is None:break
            state["slots"].append(slot)
        with patch.object(queue_batch,"get_state",return_value=state):
            res=queue_batch.fill_batch(max_posts=7,run_one=lambda:0,
                now=lambda:NOW,monotonic=lambda:100)
        self.assertEqual(res["scheduled"],0)
        self.assertEqual(res["stopped"],"queue_full")

    def test_no_extra_slot_if_subprocess_exits_ok_without_record(self):
        state={"posts":[],"slots":[]}
        with patch.object(queue_batch,"get_state",return_value=state):
            result=queue_batch.fill_batch(
                max_posts=7,run_one=lambda:0,now=lambda:NOW,
                monotonic=lambda:100)
        self.assertEqual(result["stopped"],"no_progress")
        self.assertEqual(result["scheduled"],0)


if __name__=="__main__":
    unittest.main()
