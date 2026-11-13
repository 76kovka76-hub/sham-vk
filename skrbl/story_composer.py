"""Free, original SKRBL comic compositor for one, two, three or four panels.

Storyboard text is editorially authored in story_bank.py. Free SDXL creates
each scene separately, Pillow adds readable Russian words. This avoids
model-invented Russian glyphs and varying layouts. No paid API or photo fallback.
"""
import hashlib
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, ImageStat

from story_bank import STORIES
from free_horde_test import _convert_to_pencil, _font, PAPER, STROKE
from pencil_gags import hand_text
from ovh_free import _one_request, SHORT_STYLE

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"story_preview.png"
META=ROOT/"story_preview.json"


def choose_story(ledger, slot):
    used={x.get("story_id") for x in ledger.get("entries", [])}
    recent_topics=[x.get("topic") for x in ledger.get("entries", [])[-3:]]
    # Rotate layouts 1/2/3/4 across the 50 daily slots: do not show
    # only 4-panel grids. If one layout is exhausted, other formats are fine.
    idx=int(slot.rsplit("-",1)[-1])
    desired=([1,2,1,2,3,1,2,4,1,2] * 5)[idx%50]
    rng=random.Random(slot+"SKRBL-short-original-story-v1")
    candidates=[s for s in STORIES if s.id not in used]
    rng.shuffle(candidates)
    candidates.sort(key=lambda s: (len(s.scenes)!=desired,
         s.topic in recent_topics, abs(len(s.scenes)-desired)))
    if not candidates:
        raise RuntimeError("SKRBL story bank depleted: no recycled joke may be posted")
    return candidates[0]


def validate_story(story):
    if not 1<=len(story.scenes)<=4:
        raise ValueError("SKRBL allows 1–4 panels")
    if story.caption.count("#")!=3:
        raise ValueError("SKRBL requires exactly three hashtags")
    if len({x.top for x in story.scenes})!=len(story.scenes):
        raise ValueError("Repeated panel caption")
    if not story.id or not story.topic:
        raise ValueError("Incomplete SKRBL story")
    return True


def panel_geometry(n, width=1536, height=1536, margin=34, gap=19):
    if not 1<=n<=4:
        raise ValueError("SKRBL panel count outside 1–4")
    iw=width-2*margin
    ih=height-2*margin
    if n==1:
        return [(margin,margin,iw,ih)]
    if n==2:
        h=(ih-gap)//2
        return [(margin,margin,iw,h),(margin,margin+h+gap,iw,h)]
    if n==3:
        halfw=(iw-gap)//2
        halfh=(ih-gap)//2
        return [(margin,margin,iw,halfh),
                (margin,margin+halfh+gap,halfw,halfh),
                (margin+halfw+gap,margin+halfh+gap,halfw,halfh)]
    pw=(iw-gap)//2
    ph=(ih-gap)//2
    return [(margin+(i%2)*(pw+gap),
             margin+(i//2)*(ph+gap),pw,ph) for i in range(4)]


def _quality(im, originals, story):
    if len(originals)!=len(story.scenes):
        raise RuntimeError("Missing generated SKRBL panel")
    hashes=set()
    for i,original in enumerate(originals):
        if min(original.size)<512:
            raise RuntimeError("Generated frame has insufficient detail")
        var=ImageStat.Stat(original.convert("L")).stddev[0]
        if var<28:
            raise RuntimeError("Bland free art is not a publishable comic")
        digest=hashlib.sha256(original.tobytes()[::53]).hexdigest()
        if digest in hashes:
            raise RuntimeError("Duplicate images in single SKRBL story")
        hashes.add(digest)
    if ImageStat.Stat(im.convert("L").resize((128,128))).stddev[0]<22:
        raise RuntimeError("Flat assembled SKRBL page rejected")


def build_comic(story, *, image_generator=None, output=None, metadata_path=None):
    validate_story(story)
    if image_generator is None:
        image_generator=_one_request
    if output is None:
        output=OUT
    if metadata_path is None:
        metadata_path=META
    W=H=1536
    bg=Image.new("RGB",(W,H),PAPER)
    draw=ImageDraw.Draw(bg)
    rng=random.Random(story.id)
    for _ in range(22000):
        x=rng.randrange(W);y=rng.randrange(H)
        k=rng.choice((223,235,243))
        draw.point((x,y),fill=(k,k-3,k-9))
    originals=[]
    panels=panel_geometry(len(story.scenes))
    for index, (scene, (px,py,pw,ph)) in enumerate(zip(story.scenes, panels)):
        prompt=scene.visual+(
            ". One clearly staged funny action, strong exaggerated facial "
            "emotion and gesture, detailed busy setting. " + SHORT_STYLE)
        original=image_generator(prompt)
        originals.append(original)
        # Negative space for readable Russian line added programmatically.
        caption_h=115 if len(story.scenes)>=3 else (117 if len(story.scenes)==2 else 152)
        drawing=_convert_to_pencil(original,(pw-14,ph-caption_h-14))
        draw.rectangle((px,py,px+pw,py+ph),outline=STROKE,width=5,fill=(250,247,237))
        bg.paste(drawing,(px+7,py+caption_h))
        draw.rectangle((px+6,py+caption_h,px+pw-6,py+ph-6),
                       outline=(102,91,80),width=2)
        for dy in (2,6):
            draw.line((px+7,py+dy,px+pw-7,py+dy+1),
                      fill=(118+dy,108+dy,99+dy),width=1)
        # Cyrillic captions are never delegated to image generation.
        hand_text(bg,scene.top,px,py+22,pw,
                  max_size=(58 if len(story.scenes)==1 else
                            48 if len(story.scenes)==2 else 39),
                  seed=index*49+len(story.id))
        print(f"SKRBL_STORY_FRAME:{story.id}:{index+1}/{len(story.scenes)}",flush=True)
    # Tiny integrated signature, never as a standalone giant overlay.
    draw.text((W-22,H-10),"SKRBL",font=_font(23),fill=STROKE,anchor="rd")
    _quality(bg,originals,story)
    bg.save(output,format="PNG",optimize=True)
    digest=hashlib.sha256(Path(output).read_bytes()).hexdigest()
    md={"story_id":story.id,"topic":story.topic,
        "panels":len(story.scenes),"caption":story.caption,
        "image_sha256":digest,"model":"stabilityai/stable-diffusion-xl-base-1.0",
        "generator":"OVHcloud anonymous FREE SDXL","review":"machine-checks-only"}
    Path(metadata_path).write_text(json.dumps(md,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"SKRBL_STORY_READY:{story.id}:{len(story.scenes)}:{digest}",flush=True)
    return Path(output),md


if __name__=="__main__":
    import argparse
    from queue_planner import load_state, next_slot
    parser=argparse.ArgumentParser()
    parser.add_argument("--id",default="")
    args=parser.parse_args()
    st=load_state()
    slot,_=next_slot(st)
    if not slot:
        raise RuntimeError("SKRBL 12-hour buffer already full")
    story=next((s for s in STORIES if s.id==args.id),None) if args.id else choose_story(st,slot)
    if not story:raise RuntimeError("Unknown SKRBL story")
    build_comic(story)
