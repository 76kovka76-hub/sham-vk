"""Refill multiple SHAM quarter-hour VediSMM slots per GitHub wake-up.

GitHub cron scheduling is best-effort and can skip most 5-minute events. A
single meme per cron run led to approx 1 post/hour instead of requested 4.
This runner fills several FUTURE slots per invocation, recording every success
locally so workflow can persist progress even after later failures. It never
publishes a repeated slot or replaces approved memes with generic images.
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

from main import get_state
from queue_planner import next_missing_slot


def _slots(state):
    return set(state.get("slots", []))


def fill_batch(*, max_posts=7, max_seconds=1900, min_remaining=430,
               run_one=None, monotonic=None, now=None):
    if not 1 <= max_posts <= 16:
        raise ValueError("max_posts outside safe range")
    if max_seconds < 450 or min_remaining < 240:
        raise ValueError("Batch time budget must support image generation")
    if run_one is None:
        def run_one():
            return subprocess.run([sys.executable, "-u", "main.py", "--enqueue"],
                                  check=False, timeout=min_remaining).returncode
    if monotonic is None:
        monotonic=time.monotonic
    if now is None:
        now=lambda: datetime.now(timezone.utc)
    started=monotonic()
    done=0
    reason="limit"
    for i in range(max_posts):
        remaining=max_seconds-(monotonic()-started)
        if remaining < min_remaining:
            reason="time_budget"
            break
        current=get_state()
        slot, at=next_missing_slot(current,now())
        if not slot:
            reason="queue_full"
            break
        print(f"SHAM_BATCH_STEP: {i+1}/{max_posts}; slot={slot}; scheduled={at.isoformat()}",flush=True)
        before=_slots(current)
        try:
            code=run_one()
        except subprocess.TimeoutExpired:
            reason="image_timeout"
            print("::warning::SHAM image generator timed out; earlier scheduled slots remain saved.",flush=True)
            break
        after=_slots(get_state())
        if len(after-before)==1 and slot in after:
            done+=1
            print(f"SHAM_BATCH_SCHEDULED: {slot}; total={done}",flush=True)
            # A post may have been scheduled remotely before an incidental
            # nonzero return code; never schedule it again in this invocation.
            if code:
                reason="partial_error"
                break
            continue
        if code:
            reason="generation_or_vksmm_failure"
            print(f"::warning::SHAM failed during {slot}; no low-quality fallback. Exit={code}.",flush=True)
        else:
            reason="no_progress"
            print("::warning::SHAM unexpectedly did not record a scheduled slot; stopped.",flush=True)
        break
    print(f"SHAM_BATCH_RESULT: scheduled={done}, stopped={reason}, elapsed={int(monotonic()-started)}s",flush=True)
    return {"scheduled":done,"stopped":reason}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--max-posts",type=int,default=int(os.getenv("SHAM_BATCH_MAX_POSTS","7")))
    parser.add_argument("--max-seconds",type=int,default=1900)
    args=parser.parse_args()
    fill_batch(max_posts=args.max_posts,max_seconds=args.max_seconds)
