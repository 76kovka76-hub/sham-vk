"""One original, fictional Soviet-era photograph matched to one specific joke.

FREE anonymous OVHcloud SDXL only, no Openverse, no borrowed copyrighted
film/cartoon frame, no payments. Cyrillic is added by Pillow at full quality.

WARNING: cheap pixel checks can reject flat/duplicate frames but do NOT prove
that a model depicted every requested prop. Run visual QA and review failures.
"""
import base64
import hashlib
import io
import json
from pathlib import Path
import random
import time

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps, ImageStat

from auto_stories import Story

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"auto15_preview.png"
META=ROOT/"auto15_preview.json"
API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/images/generations"
MODEL="stabilityai/stable-diffusion-xl-base-1.0"
RUST=(109,30,26)
CREAM=(239,224,191)
INK=(31,29,26)

PERIOD=(
    "Authentic-looking FICTIONAL 1970s USSR everyday film photograph, "
    "ordinary Soviet people, precise setting and props, believable faces. "
    "A witty cinematic freeze frame of a physical comedy moment, expressive "
    "face and readable action, medium-wide framing with clear body language. "
    "Photorealistic 35mm Soviet color negative film, candid slightly faded "
    "colors, period-correct wooden furniture and clothing, lively background "
    "details, natural film grain, accurate human anatomy. No modern logos, "
    "no written text, no captions, no letters, no political figures, "
    "no photorealistic famous actors. ONE main subject unless scene asks for "
    "two people. The described action and central prop MUST be visible."
)

def _font(size):
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(p).is_file():
            return ImageFont.truetype(p,size)
    return ImageFont.load_default()


def _write_lines(draw,text,rect,size_max=51,color=INK):
    x,y,w,h=rect
    if not text or len(text)>105:
        raise ValueError("Meme joke must be one short meaningful sentence")
    words=text.split()
    for size in range(size_max,21,-1):
        font=_font(size)
        lines=[]
        current=""
        for word in words:
            candidate=(current+" "+word).strip()
            if current and draw.textbbox((0,0),candidate,font=font)[2]>w-20:
                lines.append(current);current=word
            else:
                current=candidate
        if current:lines.append(current)
        line_h=int(size*1.25)
        if len(lines)*line_h<=h-8 and all(
            draw.textbbox((0,0),ln,font=font)[2]<=w-20 for ln in lines
        ):
            break
    else:
        raise ValueError("Caption cannot fit mobile layout")
    yy=y+(h-len(lines)*line_h)//2
    for line in lines:
        draw.text((x+w//2,yy),line,font=font,fill=color,anchor="mt")
        yy+=line_h


def _creative_prompt(story,style_variant=0):
    atmospheres=(
        "Warm nostalgic golden window light and documentary grain.",
        "Natural outdoor daylight, slightly muted vintage colors.",
        "1970s magazine-style Soviet candid snapshot with flash shadows.",
        "Old family album color photo, slightly faded warm film."
    )
    return (
        "MAIN ACTION: "+story.visual+". "+
        PERIOD+" "+atmospheres[style_variant%len(atmospheres)]
    )[:2600]


def free_photo(story,slot,request=requests.post):
    if not isinstance(story,Story):
        raise TypeError("Prewritten scene-specific SOVETSKIY story required")
    payload={
        "model":MODEL,
        "prompt":_creative_prompt(story,int(hashlib.sha256(slot.encode()).hexdigest()[:3],16)),
        "size":"1024x1024","n":1,
    }
    response=request(
        API,json=payload,
        headers={"accept":"application/json","Content-Type":"application/json"},
        timeout=160,
    )
    if response.status_code in (401,402,403,429):
        raise RuntimeError("SOVETSKIY free OVH image service unavailable, HTTP "
                           +str(response.status_code))
    response.raise_for_status()
    obj=response.json()
    images=obj.get("data") or []
    if not images or not isinstance(images[0],dict) or not isinstance(images[0].get("b64_json"),str):
        raise RuntimeError("Free model failed to return an image")
    binary=base64.b64decode(images[0]["b64_json"],validate=True)
    if not 30_000<len(binary)<19_000_000:
        raise RuntimeError("Generated photo bytes out of range")
    with Image.open(io.BytesIO(binary)) as img:
        if min(img.size)<512:
            raise RuntimeError("Generated Soviet scene too small")
        photo=img.convert("RGB")
    if ImageStat.Stat(photo.convert("L")).stddev[0]<32:
        raise RuntimeError("Generated photo too flat to be a useful meme")
    return photo


def render(story,slot,photo=None,output=OUT,metadata_path=META):
    if photo is None:
        photo=free_photo(story,slot)
    W=H=1200
    page=Image.new("RGB",(W,H),CREAM)
    d=ImageDraw.Draw(page)
    d.rectangle((0,0,W,134),fill=RUST)
    d.text((W//2,65),"SOVETSKIY",font=_font(86),fill=CREAM,anchor="mm")
    # Make the ACTUAL SCENE dominant: 1100x760, not a generic poster block.
    panel=ImageOps.fit(photo.convert("RGB"),(1120,800),
                       method=Image.Resampling.LANCZOS,centering=(.5,.47))
    panel=ImageEnhance.Contrast(panel).enhance(1.10)
    page.paste(panel,(40,145))
    d.rectangle((36,142,1164,949),fill=None,outline=INK,width=8)
    d.rectangle((35,969,1165,1035),fill=RUST)
    _write_lines(d,story.top,(53,972,1094,58),size_max=44,color=CREAM)
    _write_lines(d,story.bottom,(45,1043,1110,116),size_max=53,color=INK)
    d.text((1170,1190),"СОВЕТСКАЯ ЭСТЕТИКА · АВТОРСКАЯ ИЛЛЮСТРАЦИЯ",
           font=_font(15),anchor="rd",fill=(79,65,51))
    rnd=random.Random(story.id+slot)
    for _ in range(3900):
        x=rnd.randrange(W);y=rnd.randrange(H)
        if y<134 or y>=965:
            d.point((x,y),fill=rnd.choice((
                (224,202,174),(195,161,125),(242,222,184))))
    if ImageStat.Stat(page.convert("L")).stddev[0]<32:
        raise RuntimeError("Meme composition lacks visual contrast")
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    page.save(output,format="PNG",optimize=True)
    raw=Path(output).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    caption=(story.top.rstrip(".")+" — "+story.bottom.capitalize()).strip()
    caption+="\n\n#SOVETSKIY #юмор #жиза"
    if caption.count("#")!=3:
        raise ValueError("Unexpected hashtag count")
    info={
        "story_id":story.id,"theme":story.theme,"group_id":"243244760",
        "format":"original_fictional_soviet_photo","real_movie_frame":False,
        "source":"free anonymous OVHcloud SDXL","size":[W,H],
        "top":story.top,"bottom":story.bottom,"visual_intent":story.visual,
        "message":caption,"sha256":sha,
        "pixel_quality_checked":True,
        "semantic_visual_review":"unverified_by_automatic_pixel_checks",
    }
    Path(metadata_path).write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",
                                  encoding="utf-8")
    print("SOVETSKIY_ORIGINAL_SCENE:",story.id,story.theme,flush=True)
    print("SOVETSKIY_MATCHING_JOKE:",story.top,"/",story.bottom,flush=True)
    print("SOVETSKIY_IMAGE_SHA256:",sha,flush=True)
    return Path(output),info
