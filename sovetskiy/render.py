"""SOVETSKIY film-frame memes: one-image jokes and two-image collages.

Original contemporary punchlines + actual verified public-domain Soviet frames.
No claims that AI imitation frames are excerpts from copyrighted classics.
"""
import hashlib
import json
import random
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps, ImageStat

from commons import download
from jokes import JOKES

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"preview.png"
META=ROOT/"preview.json"
SIZE=1200
PAPER=(239,222,181)
RED=(145,32,26)
RED_DARK=(103,24,23)
INK=(30,29,25)
GOLD=(243,210,137)


def font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path,size)
    return ImageFont.load_default()


def multiline(draw,text,max_width,max_height,max_font,min_font=21):
    words=text.split()
    for s in range(max_font,min_font-1,-1):
        f=font(s)
        lines=[]
        current=""
        for word in words:
            trial=(current+" "+word).strip()
            if current and draw.textbbox((0,0),trial,font=f)[2]>max_width:
                lines.append(current);current=word
            else: current=trial
        if current:lines.append(current)
        if len(lines)*int(s*1.24) <= max_height and all(
                draw.textbbox((0,0),line,font=f)[2]<=max_width for line in lines):
            return f,lines
    raise ValueError("SOVETSKIY caption doesn't fit; refuse publication")


def caption(draw,text,region,max_font,fill):
    x,y,w,h=region
    f,lines=multiline(draw,text,w-35,h-18,max_font)
    line_h=int(f.size*1.23)
    yy=y+(h-line_h*len(lines))//2
    for line in lines:
        draw.text((x+w//2,yy),line,font=f,anchor="mt",fill=fill,
                  stroke_width=0)
        yy+=line_h


def _grain(img,seed=0):
    r=random.Random(seed)
    d=ImageDraw.Draw(img)
    for _ in range(9000):
        x=r.randrange(img.width);y=r.randrange(img.height)
        c=r.choice(((50,37,23),(255,247,222),(187,164,132)))
        d.point((x,y),fill=c)
    return img


def _film_frame(original,width,height):
    # Preserve the actual film still; film grain and color grading are stylistic.
    im=ImageOps.fit(original,(width,height),method=Image.Resampling.LANCZOS)
    im=ImageEnhance.Contrast(im.convert("L")).enhance(1.18)
    return ImageOps.colorize(im,black=(19,23,25),white=(245,226,184)).convert("RGB")


def _sprockets(draw,x,y,width,height):
    for px in (x+8,x+width-24):
        for yy in range(y+12,y+height-12,40):
            draw.rounded_rectangle((px,yy,px+16,yy+23),radius=4,
                                   fill=(48,35,29),outline=GOLD,width=1)


def render(joke, downloader=download, output=None, metadata_path=None):
    if output is None:output=OUT
    if metadata_path is None:metadata_path=META
    if joke.format not in ("single","collage"):
        raise ValueError("Unknown SOVETSKIY layout")
    if len(joke.source_ids)!=(1 if joke.format=="single" else 2):
        raise ValueError("Image count does not match joke layout")
    if len(set(joke.source_ids))!=len(joke.source_ids):
        raise ValueError("Collage reuses the same image")
    if len(joke.caption)>185:
        raise ValueError("Post caption is too long")
    items=[downloader(x) for x in joke.source_ids]
    if len({x["id"] for _,x in items})!=len(items):
        raise ValueError("Duplicate film frame")
    page=Image.new("RGB",(SIZE,SIZE),PAPER)
    draw=ImageDraw.Draw(page)
    # Distinctive printed-poster branding, readable on mobile.
    draw.rectangle((0,0,SIZE,155),fill=RED_DARK)
    draw.text((SIZE//2,70),"SOVETSKIY",font=font(88),anchor="mm",
              fill=GOLD)
    draw.line((80,136,SIZE-80,136),fill=GOLD,width=3)
    if joke.format=="single":
        pic,source=items[0]
        box=(34,181,SIZE-34,840)
        bw=box[2]-box[0];bh=box[3]-box[1]
        page.paste(_film_frame(pic,bw-60,bh-16),(box[0]+30,box[1]+8))
        draw.rectangle(box,outline=INK,width=8)
        _sprockets(draw,box[0],box[1],bw,bh)
        draw.rectangle((35,865,1165,942),fill=RED)
        caption(draw,joke.top,(54,867,1092,72),46,PAPER)
        caption(draw,joke.bottom,(50,949,1100,150),59,INK)
    else:
        top_y=180
        top_h=105
        caption(draw,joke.top,(45,top_y,1110,top_h),58,INK)
        y=304;ph=615;gap=17;px=35;pw=(SIZE-70-gap)//2
        for i,(pic,source) in enumerate(items):
            x=px+i*(pw+gap)
            page.paste(_film_frame(pic,pw-12,ph-20),(x+6,y+10))
            draw.rectangle((x,y,x+pw,y+ph),outline=INK,width=7)
            # Film perforations on the outer margins.
            _sprockets(draw,x,y,pw,ph)
        draw.rectangle((35,935,1165,1119),fill=RED_DARK)
        caption(draw,joke.bottom,(54,947,1092,164),58,PAPER)
    # Sources are displayed in the actual published post text, not hidden.
    names=" / ".join(dict.fromkeys(source["movie"] for _,source in items))
    source_label=("Кадр: "+names)[:88]
    draw.line((30,1137,1170,1137),fill=RED,width=3)
    caption(draw,source_label,(45,1141,1110,42),25,INK)
    draw.text((1165,1194),"© SOVETSKIY: мемная обработка",font=font(15),
              fill=INK,anchor="rd")
    page=_grain(page,seed=int(hashlib.sha256(joke.key.encode()).hexdigest()[:8],16))
    if ImageStat.Stat(page.convert("L")).stddev[0]<33:
        raise RuntimeError("Rendered SOVETSKIY image has insufficient contrast")
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    page.save(output,format="PNG",optimize=True)
    img_hash=hashlib.sha256(Path(output).read_bytes()).hexdigest()
    body=joke.caption.strip()
    credit=" / ".join(dict.fromkeys(source["movie"] for _,source in items))
    post_text=(body+"\n\nКадр: "+credit+"\n\n#SOVETSKIY #юмор #кино")
    meta={"joke_id":joke.key,"format":joke.format,"source_ids":list(joke.source_ids),
          "rights_sources":[x["source"] for _,x in items],
          "copyright_status":"Commons public domain checked at download",
          "message":post_text,"sha256":img_hash,"size":[SIZE,SIZE]}
    Path(metadata_path).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOVETSKIY_PREVIEW_READY:",output,flush=True)
    print("SOVETSKIY_JOKE_ID:",joke.key,flush=True)
    return Path(output),meta


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--id",default=JOKES[0].key)
    args=parser.parse_args()
    story=next((j for j in JOKES if j.key==args.id),None)
    if story is None:parser.error("unknown joke")
    render(story)
