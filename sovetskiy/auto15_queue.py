"""SOVETSKIY — high-frequency free VK queue, target 96 posts/day.

Schedule at all 96 UTC quarter-hours via VediSMM. Refill buffer when GitHub
Actions wakes up; GitHub cron is not a precise real-time scheduler.

A source image is used only when its license AND human scene-match approval
are confirmed. Otherwise use a FREE original scene-specific Soviet photo.
Never copy random copyrighted photos or post unrelated text/portraits.

If an external call's outcome is uncertain, record 'needs_attention' rather
than silently duplicate a VK post. This is not a guarantee of 96 deliveries.
"""
import argparse
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from auto_stories import choose_story
from auto_image import render as render_original
from check_account import BASE, VK_GROUP_ID, find_account
from publisher import _data, _if_match, choose_joke, load_state
from quarter_hour import next_slot, upcoming_slots, SLOTS_PER_DAY
from render import render as render_film
from scene_quality import review_info

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"queue_state.json"
SETTINGS=ROOT/"settings.json"
MAX_POSTS_PER_RUN=9
MAX_SECONDS_PER_RUN=1380


def save(state):
    if state.get("group_id")!=VK_GROUP_ID:
        raise RuntimeError("Refusing to update a different group's queue state")
    tmp=STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(STATE)


def config():
    cfg=json.loads(SETTINGS.read_text(encoding="utf-8"))
    if cfg.get("group_id")!=VK_GROUP_ID:
        raise RuntimeError("SOVETSKIY settings target another community")
    if cfg.get("posts_per_day")!=96 or cfg.get("interval_minutes")!=15:
        raise RuntimeError("SOVETSKIY 96/day configuration invalid")
    return cfg


def prepare(state,slot):
    """Approved Soviet movie frame, or original image designed for the joke.

    Archive image availability may be patchy. Never use unverified licensed
    photographs or misrepresent synthesized photos as real movie frames.
    """
    movie_joke=choose_joke(state,require_scene_approval=True)
    if movie_joke is not None:
        try:
            approval=review_info(movie_joke)
            art,meta=render_film(movie_joke)
            if (meta.get("scene_match_approved") is not True or
                meta.get("source_ids")!=list(movie_joke.source_ids)):
                raise RuntimeError("Movie frame and joke do not have approved visual match")
            return art, {
                "story_id":"film_"+movie_joke.key,
                "theme":movie_joke.theme,
                "source_type":"public_domain_soviet_film",
                "frame_ids":list(movie_joke.source_ids),
                "message":meta["message"],
                "sha256":meta["sha256"],
                "reviewer":approval["reviewer"],
                "original_joke_key":movie_joke.key,
            }
        except (requests.RequestException,RuntimeError,ValueError,OSError) as exc:
            print("::warning::Verified Soviet movie frame unavailable. "
                  "Use an ORIGINAL scene, not another unverified archive image. "
                  +str(exc)[:200],flush=True)
    story=choose_story(state,slot)
    if story is None:
        raise RuntimeError("SOVETSKIY's curated unique joke bank is exhausted. "
                           "No reused posts or empty filler.")
    art,meta=render_original(story,slot)
    if (meta.get("story_id")!=story.id or meta.get("group_id")!=VK_GROUP_ID
        or meta.get("sha256") is None or meta.get("real_movie_frame") is True):
        raise RuntimeError("Generated image/joke metadata does not match SOVETSKIY")
    return art, {
        "story_id":story.id,"theme":story.theme,
        "source_type":"original_soviet_photo",
        "frame_ids":[],"message":meta["message"],
        "sha256":meta["sha256"],"pixel_quality_checked":True,
        "visual_intent":story.visual,
    }


def enqueue_one(state,slot,at,token,session=requests,prepare_fn=prepare):
    """Create at most ONE VediSMM post and mark progress durably.

    For external uncertainty, a pending state may need manual reconciliation;
    it is safer than duplicate automatic posts after network failures.
    """
    if not token:
        raise RuntimeError("Missing VEDISMM_TOKEN; do not publish")
    if any(e.get("slot")==slot for e in state["entries"]):
        raise RuntimeError("The requested 15-minute slot was already processed")
    art,content=prepare_fn(state,slot)
    path=Path(art)
    if not path.is_file() or path.stat().st_size<30_000:
        raise RuntimeError("Generated full-size Soviet meme PNG missing")
    if len(content.get("message","").strip())<25 or content["message"].count("#")!=3:
        raise RuntimeError("SOVETSKIY text must be a concise complete joke with 3 hashtags")
    # Keep the ACTUAL image for each scheduled post, not just the last meme
    # overwriting auto15_preview.png. Helpful to spot model/scene mismatch.
    archive=ROOT/"batch_previews"
    archive.mkdir(exist_ok=True)
    clean_id="".join(c for c in content["story_id"] if c.isalnum() or c in "_-")[:62]
    archived=archive/(slot+"_"+clean_id+".png")
    shutil.copy2(path,archived)
    (archive/(slot+"_"+clean_id+".json")).write_text(
        json.dumps({"slot":slot,"story_id":content["story_id"],
                    "expected_scene":content.get("visual_intent",""),
                    "message":content["message"],"sha256":content["sha256"],
                    "source_type":content["source_type"],
                    "semantic_visual_review":"needs_visual_review"},
                   ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    # Check account before committing even a pending record.
    account=find_account(token)
    headers={"Authorization":"Bearer "+token}
    info={
        "slot":slot,"scheduled_at":at.astimezone(timezone.utc).isoformat().replace("+00:00","Z"),
        "story_id":content["story_id"],
        "theme":content["theme"],"sha256":content["sha256"],
        "source_type":content["source_type"],"frame_ids":content["frame_ids"],
        "group_id":VK_GROUP_ID,"status":"needs_attention",
    }
    state["entries"].append(info)
    # Record potential remote write BEFORE making any remote write.
    save(state)
    key="sovetskiy-auto15-v1-"+slot+"-"+content["story_id"]
    print("SOVETSKIY_QUEUE_ATTEMPT:",slot,content["story_id"],flush=True)
    with path.open("rb") as image:
        upload=session.post(
            BASE+"/media",headers=headers,
            files={"file":("SOVETSKIY_original.png",image,"image/png")},timeout=110)
    media=_data(upload,201)
    mid=int(media.get("id") or 0)
    if mid<=0 or media.get("type")!="image" or media.get("status")!="ready":
        raise RuntimeError("VediSMM did not confirm original image upload")
    info["media_id"]=mid
    save(state)
    draft_response=session.post(
        BASE+"/posts",headers={**headers,"Idempotency-Key":key},
        json={"title":"SOVETSKIY "+slot+" "+content["story_id"],
              "content":content["message"],"account_ids":[account],
              "media_ids":[mid]},timeout=50)
    draft=_data(draft_response,201)
    pid=int(draft.get("id") or 0)
    if pid<=0 or draft.get("status")!="draft" or not draft.get("media"):
        raise RuntimeError("VediSMM did not confirm post draft and attached image")
    info["post_id"]=pid
    save(state)
    time_value=info["scheduled_at"]
    resp=session.post(
        BASE+f"/posts/{pid}/schedule",
        headers={**headers,"If-Match":_if_match(draft_response,draft)},
        json={"scheduled_at":time_value},timeout=55)
    confirmed=_data(resp,200)
    if int(confirmed.get("id") or 0)!=pid or confirmed.get("status")!="scheduled":
        raise RuntimeError("VediSMM did not confirm 15-minute delayed publishing")
    info["status"]="scheduled"
    info["vedismm_status"]="scheduled"
    save(state)
    print("SOVETSKIY_15M_SCHEDULED:",slot,time_value,"post_id",pid,flush=True)
    return pid


def refill(*,maximum=MAX_POSTS_PER_RUN,max_seconds=MAX_SECONDS_PER_RUN,now=None):
    cfg=config()
    if cfg.get("autopublish") is not True:
        print("SOVETSKIY_AUTOPUBLISH_DISABLED")
        return {"scheduled":0,"reason":"disabled"}
    if not 1<=maximum<=16:
        raise ValueError("Unsafe batch size")
    token=os.getenv("VEDISMM_TOKEN","").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN missing")
    state=load_state()
    t0=time.monotonic()
    count=0
    stop="max_posts"
    for i in range(maximum):
        if time.monotonic()-t0>=max_seconds-150:
            stop="time_budget"
            break
        slot,at=next_slot(state,now)
        if slot is None:
            stop="buffer_full"
            break
        try:
            enqueue_one(state,slot,at,token)
            count+=1
            print("SOVETSKIY_BATCH_PROGRESS:",count,"/",maximum,flush=True)
        except (RuntimeError,ValueError,requests.RequestException,OSError) as exc:
            stop="remote_or_generation_failure"
            print("::warning::SOVETSKIY next slot could not be scheduled: "
                  +str(exc)[:300],flush=True)
            # Data about any uncertain VediSMM operation is already in
            # state, to avoid accidental duplicate VK posts.
            break
    print("SOVETSKIY_15M_RESULT:",json.dumps({
        "scheduled":count,"stopped":stop,
        "target_daily":SLOTS_PER_DAY,
        "buffered":sum(e.get("status")=="scheduled" for e in state["entries"]),
        "needs_attention":sum(e.get("status")=="needs_attention"
                              for e in state["entries"])
    },ensure_ascii=False),flush=True)
    return {"scheduled":count,"reason":stop}


def preview():
    state=load_state()
    slot,at=next_slot(state)
    story=choose_story(state,slot or "test")
    print("SOVETSKIY_MODE: 15 minutes / 96 posts per day")
    print("SOVETSKIY_AUTOPUBLISH:",config()["autopublish"])
    print("SOVETSKIY_NEXT_SLOT:",slot,at.isoformat() if at else None)
    print("SOVETSKIY_AVAILABLE_UNIQUE_STORIES:",len(
        [s for s in __import__("auto_stories").STORIES if
         s.id not in {x.get("story_id") for x in state["entries"]}]))
    print("SOVETSKIY_NEXT_STORY:",story.id if story else "(depleted)")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview",action="store_true")
    group.add_argument("--enqueue",action="store_true")
    parser.add_argument("--max-posts",type=int,default=MAX_POSTS_PER_RUN)
    args=parser.parse_args()
    if args.preview:
        preview()
    else:
        refill(maximum=args.max_posts)
