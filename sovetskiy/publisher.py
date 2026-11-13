"""SOVETSKIY: safe 24/7-capable VediSMM queue (4 posts/day pilot).

Only authentic Soviet film frames with a verifiable Commons public-domain tag.
No SHAM/SKRBL account fallback, no unpaid-license guessing, no repeats.
"""
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from check_account import find_account, BASE, VK_GROUP_ID
from jokes import JOKES
from render import render

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"queue_state.json"
SLOTS_UTC=(0,6,12,18)
MIN_LEAD=timedelta(minutes=50)
HORIZON=timedelta(hours=18)


def load_state():
    obj=json.loads(STATE.read_text(encoding="utf-8"))
    if obj.get("group_id")!=VK_GROUP_ID or not isinstance(obj.get("entries"),list):
        raise RuntimeError("SOVETSKIY queue group ID or entry list corrupted")
    return obj


def next_slot(state,now=None):
    if now is None: now=datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware clock required")
    now=now.astimezone(timezone.utc)
    used={x.get("slot") for x in state["entries"]}
    midnight=now.replace(hour=0,minute=0,second=0,microsecond=0)
    for day in range(3):
        start=midnight+timedelta(days=day)
        for hour in SLOTS_UTC:
            at=start+timedelta(hours=hour)
            key=at.strftime("%Y%m%d-%H")
            if now+MIN_LEAD<=at<=now+HORIZON and key not in used:
                return key,at
    return None,None


def choose_joke(state):
    used_jokes={x.get("joke_id") for x in state["entries"]}
    used_frames={f for x in state["entries"] for f in x.get("frame_ids",[])}
    previous_themes=[x.get("theme") for x in state["entries"][-3:]]
    options=[j for j in JOKES if j.key not in used_jokes
             and not any(f in used_frames for f in j.source_ids)]
    # Rotate singles and collages; first post uses just one source image.
    prefer_collage=(len(state["entries"]) % 3 == 1)
    options.sort(key=lambda j:(j.theme in previous_themes,
                   (j.format=="collage")!=prefer_collage,
                   [item.key for item in JOKES].index(j.key)))
    return options[0] if options else None


def _data(response,expected):
    response.raise_for_status()
    if response.status_code!=expected:
        raise RuntimeError("Unexpected VediSMM HTTP status")
    payload=response.json()
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),dict):
        raise RuntimeError("VediSMM API response invalid")
    return payload["data"]


def _if_match(reply,draft):
    etag=reply.headers.get("ETag","")
    if etag.startswith('W/"v') and etag.endswith('"'):
        if etag[2:]==f'"v{draft.get("version")}"':
            etag=etag[2:]
        else:
            raise RuntimeError("VediSMM draft version conflict")
    if not re.fullmatch(r'"v\d+"',etag):
        raise RuntimeError("VediSMM draft ETag is not a trusted version tag")
    return etag


def schedule_one():
    settings=json.loads((ROOT/"settings.json").read_text(encoding="utf-8"))
    if settings.get("group_id")!=VK_GROUP_ID or settings.get("autopublish") is not True:
        print("SOVETSKIY_AUTOPUBLISH_DISABLED: preview/tests only; no VediSMM post")
        return
    state=load_state()
    slot,at=next_slot(state)
    if slot is None:
        print("SOVETSKIY_QUEUE_SLOT_FULL_OR_OUTSIDE_HORIZON")
        return
    joke=choose_joke(state)
    if joke is None:
        print("::warning::SOVETSKIY rights-cleared original film frames exhausted. No recycled or unknown-rights images.")
        return
    print("SOVETSKIY_SELECTED:",joke.key,joke.format,slot,flush=True)
    try:
        art,meta=render(joke)
    except requests.HTTPError as exc:
        status=getattr(getattr(exc,"response",None),"status_code",None)
        if status in (429,503):
            # A public archive may throttle shared GitHub runner IPs.
            # Skip this refill rather than silently posting a different image.
            print("::warning::SOVETSKIY source archive rate-limited ("
                  +str(status)+"); post safely skipped; no VediSMM changes.",flush=True)
            return
        raise
    if meta["joke_id"]!=joke.key or meta["source_ids"]!=list(joke.source_ids):
        raise RuntimeError("SOVETSKIY image/content mismatch")
    token=os.getenv("VEDISMM_TOKEN","").strip()
    account=find_account(token)
    headers={"Authorization":"Bearer "+token}
    with Path(art).open("rb") as img:
        up=requests.post(BASE+"/media",headers=headers,
            files={"file":("SOVETSKIY_meme.png",img,"image/png")},timeout=100)
    image=_data(up,201)
    if image.get("status")!="ready" or image.get("type")!="image":
        raise RuntimeError("VediSMM image not confirmed ready")
    media_id=int(image.get("id") or 0)
    if media_id<=0:
        raise RuntimeError("VediSMM media ID invalid")
    key="sovetskiy-v1-"+slot+"-"+joke.key
    draft_response=requests.post(BASE+"/posts",
        headers={**headers,"Idempotency-Key":key},
        json={"title":"SOVETSKIY "+slot+" "+joke.key,
              "content":meta["message"],"account_ids":[account],
              "media_ids":[media_id]},timeout=50)
    draft=_data(draft_response,201)
    post_id=int(draft.get("id") or 0)
    if post_id<=0 or draft.get("status")!="draft" or not draft.get("media"):
        raise RuntimeError("VediSMM draft not ready")
    scheduled_at=at.isoformat().replace("+00:00","Z")
    response=requests.post(BASE+f"/posts/{post_id}/schedule",
        headers={**headers,"If-Match":_if_match(draft_response,draft)},
        json={"scheduled_at":scheduled_at},timeout=55)
    result=_data(response,200)
    if int(result.get("id") or 0)!=post_id or result.get("status")!="scheduled":
        raise RuntimeError("VediSMM did not confirm scheduling")
    record={"slot":slot,"scheduled_at":scheduled_at,"joke_id":joke.key,
            "theme":joke.theme,"frame_ids":list(joke.source_ids),"sha256":meta["sha256"],
            "post_id":post_id,"group_id":VK_GROUP_ID,"status":"scheduled"}
    state["entries"].append(record)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOVETSKIY_POST_SCHEDULED:",json.dumps(record,ensure_ascii=False),flush=True)


def preview():
    state=load_state()
    slot,when=next_slot(state)
    joke=choose_joke(state)
    print("SOVETSKIY_TARGET: https://vk.ru/club"+VK_GROUP_ID)
    print("SOVETSKIY_NEXT_SLOT:",slot,when.isoformat() if when else None)
    print("SOVETSKIY_UNUSED_JOKE:",joke.key if joke else "none")
    if joke:render(joke)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    opts=parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--preview",action="store_true")
    opts.add_argument("--enqueue",action="store_true")
    args=parser.parse_args()
    if args.preview:preview()
    else:schedule_one()
