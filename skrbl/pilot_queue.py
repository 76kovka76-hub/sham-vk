"""SKRBL live pilot: six free original short-form comics/day, spaced ~4 hours.

The 50/day planner remains the *target*, not a claim of 50 quality images.
A safety-limited first phase verifies real recurring delivery and image quality.
Uses FREE anonymous OVHcloud SDXL only, never a paid key or SHAM publisher.
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

from queue_planner import all_day_slots,LEDGER_PATH,load_state
from story_composer import choose_story,build_comic
from publish_test import BASE,_data,_target_account
from queue_publish import _etag

TARGET_GROUP="243241856"
PILOT_INDICES=(0,8,16,24,32,40)
LEAD=timedelta(minutes=50)
HORIZON=timedelta(hours=14)


def next_pilot_slot(state, now=None):
    if now is None:
        now=datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware now required")
    now=now.astimezone(timezone.utc)
    reserved={e["slot"] for e in state.get("entries",[]) if e.get("slot")}
    for day in (now.date(),(now+timedelta(days=1)).date()):
        slots=all_day_slots(day)
        for i in PILOT_INDICES:
            slot,at=slots[i]
            if slot in reserved:
                continue
            if now+LEAD <= at <= now+HORIZON:
                return slot,at
    return None,None


def schedule_pilot():
    state=load_state()
    if state.get("group_id")!=TARGET_GROUP:
        raise RuntimeError("Wrong VK group: nothing published")
    slot,at=next_pilot_slot(state)
    if not slot:
        print("SKRBL_PILOT_NO_FREE_SLOT_IN_NEXT_14H",flush=True)
        return
    story=choose_story(state,slot)
    print(f"SKRBL_PILOT_SELECTED:{story.id}:{len(story.scenes)} panels:{slot}:{at.isoformat()}",flush=True)
    # Any failure before successful scheduling stops publication, never falls back
    # to generic portraits or canned images from another community.
    art,meta=build_comic(story)
    if meta["story_id"]!=story.id or meta["panels"]!=len(story.scenes):
        raise RuntimeError("Visual storyboard mismatch")
    token=os.getenv("VEDISMM_TOKEN","").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN missing")
    headers={"Authorization":"Bearer "+token}
    account=_target_account(headers)  # Strict check VK 243241856
    if not account:
        raise RuntimeError("SKRBL not linked in VediSMM")
    with Path(art).open("rb") as img:
        up=requests.post(BASE+"/media",headers=headers,
                         files={"file":("SKRBL_original.png",img,"image/png")},timeout=95)
    media=_data(up,201)
    if media.get("status")!="ready" or media.get("type")!="image":
        raise RuntimeError("SKRBL visual upload not confirmed; aborted")
    mediaid=int(media.get("id") or 0)
    if mediaid<=0:
        raise RuntimeError("SKRBL upload ID invalid")
    idem="skrbl-pilot-"+slot+"-"+story.id
    created=requests.post(BASE+"/posts",
       headers={**headers,"Idempotency-Key":idem},
       json={"title":"SKRBL "+slot+" "+story.id,
             "content":story.caption,"account_ids":[account],
             "media_ids":[mediaid]},timeout=45)
    draft=_data(created,201)
    postid=int(draft.get("id") or 0)
    if postid<=0 or draft.get("status")!="draft" or not draft.get("media"):
        raise RuntimeError("VediSMM draft image not confirmed")
    etag=_etag(created,draft)
    utc=at.isoformat().replace("+00:00","Z")
    result=requests.post(BASE+f"/posts/{postid}/schedule",
            headers={**headers,"If-Match":etag},
            json={"scheduled_at":utc},timeout=45)
    checked=_data(result,200)
    if checked.get("status")!="scheduled" or checked.get("id")!=postid:
        raise RuntimeError("SKRBL post not confirmed in VediSMM calendar")
    record={"slot":slot,"scheduled_at":utc,"asset_id":"auto_"+story.id,
            "sha256":meta["image_sha256"],"story_id":story.id,"topic":story.topic,
            "panels":len(story.scenes),"post_id":postid,"status":"scheduled",
            "group_id":TARGET_GROUP,"generator":"FREE_OVH_SDXL","pilot":True}
    state["entries"].append(record)
    LEDGER_PATH.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SKRBL_PILOT_SCHEDULED:"+json.dumps(record,ensure_ascii=False),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    parser.add_argument("--enqueue",action="store_true")
    args=parser.parse_args()
    if args.preview==args.enqueue:
        parser.error("Choose exactly one mode")
    if args.preview:
        state=load_state()
        slot,at=next_pilot_slot(state)
        if slot:
            story=choose_story(state,slot)
            print("SKRBL_PILOT_PREVIEW:",story.id,len(story.scenes),at.isoformat(),flush=True)
        else:
            print("SKRBL_PILOT_PREVIEW: no slot in next 14 hours",flush=True)
    else:
        schedule_pilot()
